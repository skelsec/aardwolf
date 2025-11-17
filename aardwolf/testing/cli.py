#!/usr/bin/env python3
"""
CLI interface for RDP Disconnect Testing Framework

Provides command-line interface for surgical, protocol-aware RDP disconnect testing.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from aardwolf.testing.config import TestConfig, ALL_STAGES
from aardwolf.testing.logger import TestLogger
from aardwolf.testing.orchestrator import TestOrchestrator


def create_parser() -> argparse.ArgumentParser:
	"""Create and configure argument parser"""
	parser = argparse.ArgumentParser(
		description="RDP Disconnect Testing & Stress Framework",
		epilog="Example: rdp-test connect --target 'rdp+ntlm-password://DOMAIN\\User:Pass@192.168.1.50'"
	)

	parser.add_argument(
		'--version',
		action='version',
		version='RDP Disconnect Testing Framework v1.0.0'
	)

	subparsers = parser.add_subparsers(dest='command', help='Command to execute')

	# Connect command - simple single connection test
	connect_parser = subparsers.add_parser(
		'connect',
		help='Run a single connection test'
	)
	connect_parser.add_argument(
		'--target',
		required=True,
		help='RDP connection URL (e.g., rdp+ntlm-password://DOMAIN\\User:Pass@host)'
	)
	connect_parser.add_argument(
		'--stage',
		choices=ALL_STAGES,
		help='Protocol stage to abort at'
	)
	connect_parser.add_argument(
		'--abort-mode',
		choices=['hard', 'soft'],
		default='hard',
		help='Abort mode: hard (immediate) or soft (graceful disconnect)'
	)
	connect_parser.add_argument(
		'--timeout',
		type=int,
		default=20,
		help='Connection timeout in seconds (default: 20)'
	)

	# Stage sweep command - test all stages systematically
	sweep_parser = subparsers.add_parser(
		'stage-sweep',
		help='Sweep through all protocol stages'
	)
	sweep_parser.add_argument(
		'--config',
		required=True,
		help='Path to YAML configuration file'
	)
	sweep_parser.add_argument(
		'--stages',
		nargs='+',
		choices=ALL_STAGES,
		help='Specific stages to test (overrides config)'
	)

	# Hammer mode command - stress testing
	hammer_parser = subparsers.add_parser(
		'hammer',
		help='Run stress testing (hammer mode)'
	)
	hammer_parser.add_argument(
		'--config',
		required=True,
		help='Path to YAML configuration file'
	)
	hammer_parser.add_argument(
		'--strategy',
		choices=['parallel', 'focused', 'burst', 'random'],
		help='Hammer strategy (overrides config)'
	)
	hammer_parser.add_argument(
		'--iterations',
		type=int,
		help='Number of iterations (overrides config)'
	)

	# Random mode command - randomized fuzzing
	random_parser = subparsers.add_parser(
		'random',
		help='Run randomized stage testing'
	)
	random_parser.add_argument(
		'--config',
		required=True,
		help='Path to YAML configuration file'
	)
	random_parser.add_argument(
		'--iterations',
		type=int,
		default=1000,
		help='Total number of connections to make (default: 1000)'
	)

	# List stages command
	list_parser = subparsers.add_parser(
		'list-stages',
		help='List all available protocol stages'
	)

	# Generate config command
	genconfig_parser = subparsers.add_parser(
		'gen-config',
		help='Generate example configuration file'
	)
	genconfig_parser.add_argument(
		'--output',
		default='config.yaml',
		help='Output file path (default: config.yaml)'
	)
	genconfig_parser.add_argument(
		'--target',
		required=True,
		help='RDP connection URL'
	)

	return parser


async def cmd_connect(args):
	"""Execute single connection test"""
	from aardwolf.connection import RDPConnection
	from aardwolf.commons.factory import RDPConnectionFactory
	from aardwolf.commons.iosettings import RDPIOSettings
	from aardwolf.exceptions import RDPAbortException
	import time

	print(f"Connecting to: {args.target}")
	if args.stage:
		print(f"Will abort at stage: {args.stage}")

	start_time = time.time()

	try:
		iosettings = RDPIOSettings()
		rdpurl = RDPConnectionFactory.from_url(args.target, iosettings)
		conn = rdpurl.get_connection(iosettings)

		if args.stage:
			conn.abort_stage = args.stage
			conn.abort_mode = args.abort_mode

		_, err = await asyncio.wait_for(conn.connect(), timeout=args.timeout)

		if err is not None:
			print(f"❌ Connection failed: {err}")
			return 1

		duration = time.time() - start_time
		print(f"✓ Connection succeeded in {duration:.3f}s")

		await conn.terminate()
		return 0

	except RDPAbortException as e:
		duration = time.time() - start_time
		print(f"⚠ Aborted at stage '{e.stage}' in {duration:.3f}s")
		return 0

	except asyncio.TimeoutError:
		print(f"❌ Connection timed out after {args.timeout}s")
		return 1

	except Exception as e:
		duration = time.time() - start_time
		print(f"❌ Error after {duration:.3f}s: {type(e).__name__}: {e}")
		return 1


async def cmd_stage_sweep(args):
	"""Execute stage sweep test"""
	try:
		config = TestConfig.from_yaml(args.config)
		config.validate()

		# Override stages if specified
		if args.stages:
			config.stages = args.stages

		logger = TestLogger(
			log_file=config.logging.file,
			json_file=config.logging.json,
			csv_file=config.logging.csv,
			verbose=config.logging.verbose
		)

		orchestrator = TestOrchestrator(config, logger)

		print(f"Starting stage sweep with {len(config.stages)} stages...")
		print(f"Iterations per stage: {config.iterations_per_stage}")
		print(f"Parallel connections: {config.parallel_stages}")
		print(f"Max concurrent: {config.max_concurrent_connections}\n")

		results = await orchestrator.run_stage_sweep()

		logger.save_results()
		logger.print_summary()

		return 0

	except Exception as e:
		print(f"❌ Error: {e}")
		import traceback
		traceback.print_exc()
		return 1


async def cmd_hammer(args):
	"""Execute hammer mode stress testing"""
	try:
		config = TestConfig.from_yaml(args.config)
		config.validate()

		# Enable hammer mode
		config.hammer_mode = True

		# Override strategy if specified
		if args.strategy:
			config.hammer_strategy = args.strategy

		# Override iterations if specified
		if args.iterations:
			config.iterations_per_stage = args.iterations

		logger = TestLogger(
			log_file=config.logging.file,
			json_file=config.logging.json,
			csv_file=config.logging.csv,
			verbose=config.logging.verbose
		)

		orchestrator = TestOrchestrator(config, logger)

		print(f"Starting hammer mode: {config.hammer_strategy}")
		print(f"Max concurrent: {config.max_concurrent_connections}\n")

		results = await orchestrator.run_tests()

		logger.save_results()
		logger.print_summary()

		return 0

	except Exception as e:
		print(f"❌ Error: {e}")
		import traceback
		traceback.print_exc()
		return 1


async def cmd_random(args):
	"""Execute random stage testing"""
	try:
		config = TestConfig.from_yaml(args.config)
		config.validate()

		logger = TestLogger(
			log_file=config.logging.file,
			json_file=config.logging.json,
			csv_file=config.logging.csv,
			verbose=config.logging.verbose
		)

		orchestrator = TestOrchestrator(config, logger)

		print(f"Starting random testing with {args.iterations} connections...")
		print(f"Stages: {len(config.stages)}")
		print(f"Max concurrent: {config.max_concurrent_connections}\n")

		results = await orchestrator.run_random_hammer(total_connections=args.iterations)

		logger.save_results()
		logger.print_summary()

		return 0

	except Exception as e:
		print(f"❌ Error: {e}")
		import traceback
		traceback.print_exc()
		return 1


def cmd_list_stages(args):
	"""List all available protocol stages"""
	print("\nAvailable Protocol Stages:")
	print("=" * 60)

	stage_categories = {
		"Initial Negotiation": [
			"after_x224_negotiate",
		],
		"Channel Setup": [
			"after_establish_channels",
			"after_erect_domain",
			"after_attach_user",
			"after_join_channels",
		],
		"Security Exchange": [
			"after_security_exchange",
			"after_send_userdata",
			"after_license",
		],
		"Capability Exchange": [
			"after_server_demand_active",
			"after_client_confirm_active",
			"after_capability_exchange",
		],
		"Synchronization": [
			"after_server_sync",
			"after_client_sync",
			"after_client_control_cooperate",
			"after_client_control_request",
			"after_client_fontlist",
		],
		"Active Connection": [
			"after_start_external_reader",
			"on_first_fastpath_bitmap",
			"on_nth_fastpath_bitmap",
		]
	}

	for category, stages in stage_categories.items():
		print(f"\n{category}:")
		for stage in stages:
			print(f"  - {stage}")

	print("\n" + "=" * 60)
	print(f"Total stages: {len(ALL_STAGES)}\n")
	return 0


def cmd_gen_config(args):
	"""Generate example configuration file"""
	config = TestConfig(
		target=args.target,
		iterations_per_stage=10,
		parallel_stages=5,
		abort_mode="hard",
		stages=ALL_STAGES,
		bitmap_abort_threshold=5,
		connection_timeout=20,
		max_concurrent_connections=30
	)

	config.to_yaml(args.output)
	print(f"✓ Generated configuration file: {args.output}")
	return 0


def main():
	"""Main entry point"""
	parser = create_parser()
	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		return 1

	try:
		# Route to appropriate command handler
		if args.command == 'connect':
			return asyncio.run(cmd_connect(args))
		elif args.command == 'stage-sweep':
			return asyncio.run(cmd_stage_sweep(args))
		elif args.command == 'hammer':
			return asyncio.run(cmd_hammer(args))
		elif args.command == 'random':
			return asyncio.run(cmd_random(args))
		elif args.command == 'list-stages':
			return cmd_list_stages(args)
		elif args.command == 'gen-config':
			return cmd_gen_config(args)
		else:
			parser.print_help()
			return 1

	except KeyboardInterrupt:
		print("\n\n⚠ Interrupted by user")
		return 130
	except Exception as e:
		print(f"\n❌ Fatal error: {e}")
		import traceback
		traceback.print_exc()
		return 1


if __name__ == '__main__':
	sys.exit(main())
