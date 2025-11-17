"""
Logging and reporting engine for RDP disconnect testing
"""

import json
import csv
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
from pathlib import Path


class TestLogger:
	"""Comprehensive logging and reporting for RDP disconnect tests"""

	def __init__(self, log_file: str = "logs/session.log",
				 json_file: str = "logs/results.json",
				 csv_file: Optional[str] = None,
				 verbose: bool = False):
		"""
		Initialize test logger

		Args:
			log_file: Path to text log file
			json_file: Path to JSON results file
			csv_file: Optional path to CSV export file
			verbose: Enable verbose logging
		"""
		self.log_file = log_file
		self.json_file = json_file
		self.csv_file = csv_file
		self.verbose = verbose

		# Create directories if they don't exist
		for filepath in [log_file, json_file, csv_file]:
			if filepath:
				Path(filepath).parent.mkdir(parents=True, exist_ok=True)

		# Setup logging
		self.logger = logging.getLogger('rdp_disconnect_test')
		self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

		# File handler
		fh = logging.FileHandler(log_file)
		fh.setLevel(logging.DEBUG)

		# Console handler
		ch = logging.StreamHandler()
		ch.setLevel(logging.INFO)

		# Formatter
		formatter = logging.Formatter(
			'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
			datefmt='%Y-%m-%d %H:%M:%S'
		)
		fh.setFormatter(formatter)
		ch.setFormatter(formatter)

		self.logger.addHandler(fh)
		self.logger.addHandler(ch)

		# Results storage
		self.results: List[Dict[str, Any]] = []
		self.session_start = datetime.now()

	def log_connection_start(self, stage: str, iteration: int):
		"""Log the start of a connection test"""
		self.logger.info(f"Starting connection test - Stage: {stage}, Iteration: {iteration}")

	def log_connection_result(self, stage: str, outcome: str, exception: Optional[str] = None,
							  duration_sec: float = 0.0, metadata: Optional[Dict] = None):
		"""
		Log the result of a connection test

		Args:
			stage: The protocol stage at which abort occurred
			outcome: The outcome classification
			exception: Optional exception string
			duration_sec: Connection duration in seconds
			metadata: Optional additional metadata
		"""
		result = {
			"stage": stage,
			"outcome": outcome,
			"exception": exception,
			"timestamp": datetime.now().isoformat(),
			"duration_sec": round(duration_sec, 3),
			"metadata": metadata or {}
		}

		self.results.append(result)

		# Log to file
		log_msg = f"Result - Stage: {stage}, Outcome: {outcome}, Duration: {duration_sec:.3f}s"
		if exception:
			log_msg += f", Exception: {exception}"

		if outcome in ["termservice_crash", "rdpcorets_crash", "kernel_watchdog"]:
			self.logger.warning(log_msg)
		elif outcome == "no_crash":
			self.logger.info(log_msg)
		else:
			self.logger.error(log_msg)

	def classify_outcome(self, exception: Optional[Exception]) -> str:
		"""
		Classify the outcome based on exception type and message

		Args:
			exception: The exception raised during connection

		Returns:
			Outcome classification string
		"""
		if exception is None:
			return "no_crash"

		exc_str = str(exception).lower()
		exc_type = type(exception).__name__.lower()

		# Classification logic
		if "rdpabortexception" in exc_type:
			return "intentional_abort"

		if "timeout" in exc_str or "timeout" in exc_type:
			return "connection_timeout"

		if "connection closed" in exc_str or "connection reset" in exc_str:
			return "transport_error"

		if "license" in exc_str:
			return "licensing_failure"

		if "security" in exc_str and "exchange" in exc_str:
			return "security_exchange_failure"

		if "termservice" in exc_str or "terminal service" in exc_str:
			return "termservice_crash"

		if "rdpcorets" in exc_str:
			return "rdpcorets_crash"

		if "watchdog" in exc_str or "hang" in exc_str:
			return "kernel_watchdog"

		return "unknown_error"

	def generate_summary(self) -> Dict[str, Any]:
		"""Generate summary statistics"""
		if not self.results:
			return {"error": "No results to summarize"}

		# Count outcomes
		outcome_counts = defaultdict(int)
		stage_outcomes = defaultdict(lambda: defaultdict(int))
		total_duration = 0.0

		for result in self.results:
			outcome_counts[result["outcome"]] += 1
			stage_outcomes[result["stage"]][result["outcome"]] += 1
			total_duration += result["duration_sec"]

		# Calculate crash frequency
		total_tests = len(self.results)
		crash_types = ["termservice_crash", "rdpcorets_crash", "kernel_watchdog"]
		total_crashes = sum(outcome_counts[ct] for ct in crash_types)

		summary = {
			"session_start": self.session_start.isoformat(),
			"session_end": datetime.now().isoformat(),
			"total_tests": total_tests,
			"total_crashes": total_crashes,
			"crash_rate": round(total_crashes / total_tests * 100, 2) if total_tests > 0 else 0,
			"total_duration_sec": round(total_duration, 3),
			"avg_duration_sec": round(total_duration / total_tests, 3) if total_tests > 0 else 0,
			"outcome_counts": dict(outcome_counts),
			"stage_outcomes": {k: dict(v) for k, v in stage_outcomes.items()},
		}

		return summary

	def save_results(self):
		"""Save results to JSON file"""
		output = {
			"summary": self.generate_summary(),
			"results": self.results
		}

		with open(self.json_file, 'w') as f:
			json.dump(output, f, indent=2)

		self.logger.info(f"Results saved to {self.json_file}")

		# Save CSV if requested
		if self.csv_file and self.results:
			self._save_csv()

	def _save_csv(self):
		"""Save results to CSV file"""
		fieldnames = ["stage", "outcome", "duration_sec", "timestamp", "exception"]

		with open(self.csv_file, 'w', newline='') as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames)
			writer.writeheader()

			for result in self.results:
				row = {
					"stage": result["stage"],
					"outcome": result["outcome"],
					"duration_sec": result["duration_sec"],
					"timestamp": result["timestamp"],
					"exception": result.get("exception", "")
				}
				writer.writerow(row)

		self.logger.info(f"CSV export saved to {self.csv_file}")

	def print_summary(self):
		"""Print summary to console"""
		summary = self.generate_summary()

		print("\n" + "=" * 70)
		print("RDP DISCONNECT TEST SUMMARY")
		print("=" * 70)
		print(f"Session Start:     {summary['session_start']}")
		print(f"Session End:       {summary['session_end']}")
		print(f"Total Tests:       {summary['total_tests']}")
		print(f"Total Crashes:     {summary['total_crashes']}")
		print(f"Crash Rate:        {summary['crash_rate']}%")
		print(f"Total Duration:    {summary['total_duration_sec']:.3f}s")
		print(f"Avg Duration:      {summary['avg_duration_sec']:.3f}s")
		print("\n" + "-" * 70)
		print("OUTCOME BREAKDOWN:")
		print("-" * 70)

		for outcome, count in sorted(summary['outcome_counts'].items(), key=lambda x: x[1], reverse=True):
			pct = round(count / summary['total_tests'] * 100, 1) if summary['total_tests'] > 0 else 0
			print(f"  {outcome:30s} {count:5d} ({pct:5.1f}%)")

		print("\n" + "-" * 70)
		print("CRASHES BY STAGE:")
		print("-" * 70)

		crash_types = ["termservice_crash", "rdpcorets_crash", "kernel_watchdog"]
		for stage, outcomes in sorted(summary['stage_outcomes'].items()):
			stage_crashes = sum(outcomes.get(ct, 0) for ct in crash_types)
			if stage_crashes > 0:
				print(f"  {stage:30s} {stage_crashes:5d} crashes")
				for ct in crash_types:
					if ct in outcomes and outcomes[ct] > 0:
						print(f"    - {ct:26s} {outcomes[ct]:5d}")

		print("=" * 70 + "\n")
