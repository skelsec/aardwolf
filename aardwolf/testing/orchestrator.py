"""
Test orchestrator for RDP disconnect testing framework
"""

import asyncio
import time
import random
from typing import List, Optional, Callable
from aardwolf.connection import RDPConnection
from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.exceptions import RDPAbortException
from aardwolf.testing.config import TestConfig
from aardwolf.testing.logger import TestLogger


class TestOrchestrator:
	"""Orchestrates RDP disconnect testing with various modes and strategies"""

	def __init__(self, config: TestConfig, logger: TestLogger):
		"""
		Initialize test orchestrator

		Args:
			config: Test configuration
			logger: Test logger instance
		"""
		self.config = config
		self.logger = logger
		self.active_connections = 0
		self.max_concurrent = config.max_concurrent_connections
		self.semaphore = asyncio.Semaphore(self.max_concurrent)

	async def run_single_connection(self, stage: str, iteration: int = 0,
									 abort_callback: Optional[Callable] = None) -> dict:
		"""
		Run a single RDP connection test with abort at specified stage

		Args:
			stage: Protocol stage to abort at
			iteration: Iteration number for logging
			abort_callback: Optional callback function for dynamic abort logic

		Returns:
			Dictionary with test results
		"""
		start_time = time.time()
		outcome = "unknown"
		exception_str = None
		conn = None

		try:
			async with self.semaphore:
				self.active_connections += 1
				self.logger.log_connection_start(stage, iteration)

				# Parse target URL and create connection
				iosettings = RDPIOSettings()
				rdpurl = RDPConnectionFactory.from_url(self.config.target, iosettings)
				conn = rdpurl.get_connection(iosettings)

				# Configure abort settings
				conn.abort_stage = stage
				conn.abort_mode = self.config.abort_mode
				conn.abort_callback = abort_callback
				conn.abort_n_bitmap = self.config.bitmap_abort_threshold

				# Attempt connection
				try:
					_, err = await asyncio.wait_for(
						conn.connect(),
						timeout=self.config.connection_timeout
					)

					if err is not None:
						raise err

					# If we get here without abort, connection succeeded
					outcome = "no_crash"

				except asyncio.TimeoutError:
					outcome = "connection_timeout"
					exception_str = f"Connection timed out after {self.config.connection_timeout}s"

				except RDPAbortException as e:
					# Expected abort
					outcome = "intentional_abort"
					exception_str = str(e)

				except Exception as e:
					# Unexpected error - classify it
					outcome = self.logger.classify_outcome(e)
					exception_str = f"{type(e).__name__}: {str(e)}"

		except Exception as e:
			# Outer exception handling
			outcome = "framework_error"
			exception_str = f"Framework error: {type(e).__name__}: {str(e)}"

		finally:
			duration = time.time() - start_time
			self.active_connections -= 1

			# Cleanup connection
			if conn is not None:
				try:
					await asyncio.wait_for(conn.terminate(), timeout=5)
				except:
					pass

			# Log result
			self.logger.log_connection_result(
				stage=stage,
				outcome=outcome,
				exception=exception_str,
				duration_sec=duration,
				metadata={"iteration": iteration}
			)

		return {
			"stage": stage,
			"outcome": outcome,
			"duration": duration,
			"exception": exception_str
		}

	async def run_stage_sweep(self, stages: Optional[List[str]] = None) -> List[dict]:
		"""
		Run tests sweeping through all specified stages

		Args:
			stages: List of stages to test (uses config.stages if None)

		Returns:
			List of test results
		"""
		if stages is None:
			stages = self.config.stages

		self.logger.logger.info(f"Starting stage sweep with {len(stages)} stages, "
								f"{self.config.iterations_per_stage} iterations each")

		results = []

		for stage in stages:
			self.logger.logger.info(f"\n{'=' * 60}")
			self.logger.logger.info(f"Testing stage: {stage}")
			self.logger.logger.info(f"{'=' * 60}")

			# Run iterations for this stage with controlled concurrency
			stage_tasks = []
			for i in range(self.config.iterations_per_stage):
				task = self.run_single_connection(stage, iteration=i)
				stage_tasks.append(task)

				# Limit parallel execution
				if len(stage_tasks) >= self.config.parallel_stages:
					batch_results = await asyncio.gather(*stage_tasks)
					results.extend(batch_results)
					stage_tasks = []

			# Run remaining tasks
			if stage_tasks:
				batch_results = await asyncio.gather(*stage_tasks)
				results.extend(batch_results)

		return results

	async def run_parallel_hammer(self, stages: Optional[List[str]] = None) -> List[dict]:
		"""
		Hammer mode: Run many connections in parallel across multiple stages

		Args:
			stages: List of stages to hammer (uses config.stages if None)

		Returns:
			List of test results
		"""
		if stages is None:
			stages = self.config.stages

		self.logger.logger.info(f"Starting parallel hammer mode with {len(stages)} stages")

		tasks = []
		for stage in stages:
			for i in range(self.config.iterations_per_stage):
				task = self.run_single_connection(stage, iteration=i)
				tasks.append(task)

		results = await asyncio.gather(*tasks)
		return list(results)

	async def run_focused_hammer(self, stage: str, iterations: int) -> List[dict]:
		"""
		Focused hammer: Hit a single stage repeatedly

		Args:
			stage: Stage to hammer
			iterations: Number of iterations

		Returns:
			List of test results
		"""
		self.logger.logger.info(f"Starting focused hammer on stage: {stage} ({iterations} iterations)")

		tasks = []
		for i in range(iterations):
			task = self.run_single_connection(stage, iteration=i)
			tasks.append(task)

		results = await asyncio.gather(*tasks)
		return list(results)

	async def run_burst_hammer(self, stages: Optional[List[str]] = None) -> List[dict]:
		"""
		Burst hammer: Short bursts of rapid connections

		Args:
			stages: List of stages to test (uses config.stages if None)

		Returns:
			List of test results
		"""
		if stages is None:
			stages = self.config.stages

		self.logger.logger.info(
			f"Starting burst hammer mode: {self.config.burst_repeat} bursts of "
			f"{self.config.burst_size} connections with {self.config.burst_delay}s delay"
		)

		results = []

		for burst_num in range(self.config.burst_repeat):
			self.logger.logger.info(f"Burst {burst_num + 1}/{self.config.burst_repeat}")

			# Create burst of connections
			tasks = []
			for _ in range(self.config.burst_size):
				stage = random.choice(stages)
				task = self.run_single_connection(stage, iteration=burst_num)
				tasks.append(task)

			# Run burst
			burst_results = await asyncio.gather(*tasks)
			results.extend(burst_results)

			# Delay between bursts (except last one)
			if burst_num < self.config.burst_repeat - 1:
				await asyncio.sleep(self.config.burst_delay)

		return results

	async def run_random_hammer(self, stages: Optional[List[str]] = None,
								total_connections: int = 1000) -> List[dict]:
		"""
		Random hammer: Random stage selection for each connection

		Args:
			stages: List of stages to randomly select from (uses config.stages if None)
			total_connections: Total number of connections to make

		Returns:
			List of test results
		"""
		if stages is None:
			stages = self.config.stages

		self.logger.logger.info(
			f"Starting random hammer mode: {total_connections} connections "
			f"across {len(stages)} stages"
		)

		tasks = []
		for i in range(total_connections):
			stage = random.choice(stages)
			task = self.run_single_connection(stage, iteration=i)
			tasks.append(task)

		results = await asyncio.gather(*tasks)
		return list(results)

	async def run_tests(self) -> List[dict]:
		"""
		Run tests based on configuration

		Returns:
			List of test results
		"""
		if self.config.hammer_mode:
			if self.config.hammer_strategy == "parallel":
				results = await self.run_parallel_hammer()
			elif self.config.hammer_strategy == "focused":
				# Focus on first stage in list
				stage = self.config.stages[0] if self.config.stages else "after_capability_exchange"
				results = await self.run_focused_hammer(stage, self.config.iterations_per_stage * 10)
			elif self.config.hammer_strategy == "burst":
				results = await self.run_burst_hammer()
			elif self.config.hammer_strategy == "random":
				total = len(self.config.stages) * self.config.iterations_per_stage
				results = await self.run_random_hammer(total_connections=total)
			else:
				raise ValueError(f"Unknown hammer strategy: {self.config.hammer_strategy}")
		else:
			# Normal stage sweep
			results = await self.run_stage_sweep()

		return results
