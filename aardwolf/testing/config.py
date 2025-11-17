"""
Configuration models for RDP disconnect testing framework
"""

import yaml
from typing import List, Optional, Literal
from dataclasses import dataclass, field


# All supported abort stages
ALL_STAGES = [
	"after_x224_negotiate",
	"after_establish_channels",
	"after_erect_domain",
	"after_attach_user",
	"after_join_channels",
	"after_security_exchange",
	"after_send_userdata",
	"after_license",
	"after_server_demand_active",
	"after_client_confirm_active",
	"after_server_sync",
	"after_client_sync",
	"after_client_control_cooperate",
	"after_client_control_request",
	"after_client_fontlist",
	"after_capability_exchange",
	"after_start_external_reader",
	"on_first_fastpath_bitmap",
	"on_nth_fastpath_bitmap",
]


@dataclass
class LoggingConfig:
	"""Configuration for logging and reporting"""
	file: str = "logs/session.log"
	json: str = "logs/results.json"
	csv: Optional[str] = None
	per_connection: bool = True
	verbose: bool = False


@dataclass
class TestConfig:
	"""Main configuration for RDP disconnect testing"""
	target: str
	iterations_per_stage: int = 10
	parallel_stages: int = 5
	abort_mode: Literal["hard", "soft"] = "hard"
	stages: List[str] = field(default_factory=lambda: ALL_STAGES.copy())
	bitmap_abort_threshold: int = 5
	connection_timeout: int = 20
	max_concurrent_connections: int = 30
	logging: LoggingConfig = field(default_factory=LoggingConfig)

	# Hammer mode specific settings
	hammer_mode: bool = False
	hammer_strategy: Literal["parallel", "focused", "burst", "random"] = "parallel"
	burst_size: int = 20
	burst_delay: float = 0.1
	burst_repeat: int = 100

	@classmethod
	def from_yaml(cls, filepath: str) -> 'TestConfig':
		"""Load configuration from YAML file"""
		with open(filepath, 'r') as f:
			data = yaml.safe_load(f)

		# Extract logging config
		logging_data = data.pop('logging', {})
		logging_config = LoggingConfig(**logging_data)

		# Create main config
		return cls(logging=logging_config, **data)

	def to_yaml(self, filepath: str):
		"""Save configuration to YAML file"""
		data = {
			'target': self.target,
			'iterations_per_stage': self.iterations_per_stage,
			'parallel_stages': self.parallel_stages,
			'abort_mode': self.abort_mode,
			'stages': self.stages,
			'bitmap_abort_threshold': self.bitmap_abort_threshold,
			'connection_timeout': self.connection_timeout,
			'max_concurrent_connections': self.max_concurrent_connections,
			'hammer_mode': self.hammer_mode,
			'hammer_strategy': self.hammer_strategy,
			'burst_size': self.burst_size,
			'burst_delay': self.burst_delay,
			'burst_repeat': self.burst_repeat,
			'logging': {
				'file': self.logging.file,
				'json': self.logging.json,
				'csv': self.logging.csv,
				'per_connection': self.logging.per_connection,
				'verbose': self.logging.verbose,
			}
		}
		with open(filepath, 'w') as f:
			yaml.dump(data, f, default_flow_style=False)

	def validate(self):
		"""Validate configuration"""
		if not self.target:
			raise ValueError("Target URL is required")

		for stage in self.stages:
			if stage not in ALL_STAGES:
				raise ValueError(f"Invalid stage: {stage}. Must be one of {ALL_STAGES}")

		if self.iterations_per_stage < 1:
			raise ValueError("iterations_per_stage must be >= 1")

		if self.parallel_stages < 1:
			raise ValueError("parallel_stages must be >= 1")

		if self.connection_timeout < 1:
			raise ValueError("connection_timeout must be >= 1")

		if self.max_concurrent_connections < 1:
			raise ValueError("max_concurrent_connections must be >= 1")
