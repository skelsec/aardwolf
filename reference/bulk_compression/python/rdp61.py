"""Specification-derived RDP 6.1 chained bulk decompression.

The byte-level structure and state transitions follow [MS-RDPEGDI]
sections 2.2.2.4.1 and 3.1.8.2.
"""

import struct

from .bitstream import BulkCompressionError
from .mppc import MppcDecoder
from .types import (
	BulkCompressionFlags,
	BulkCompressionType,
	VALID_FLAG_MASK,
)


L1_COMPRESSED = 0x01
L1_NO_COMPRESSION = 0x02
L1_PACKET_AT_FRONT = 0x04
L1_INNER_COMPRESSION = 0x10
L1_VALID_FLAGS = (
	L1_COMPRESSED
	| L1_NO_COMPRESSION
	| L1_PACKET_AT_FRONT
	| L1_INNER_COMPRESSION
)


class Rdp61Decoder:
	HISTORY_SIZE = 2000000
	MAX_BLOCK_SIZE = 16382
	MATCH_DETAILS_SIZE = 8

	def __init__(self, max_output_size=None):
		if max_output_size is None:
			self.max_output_size = self.MAX_BLOCK_SIZE
		else:
			if max_output_size <= 0:
				raise ValueError('Maximum decompressed size must be positive')
			self.max_output_size = min(
				max_output_size,
				self.MAX_BLOCK_SIZE,
			)
		self.history = bytearray(self.HISTORY_SIZE)
		self.history_offset = 0
		self.level2 = MppcDecoder(
			BulkCompressionType.RDP5_64K,
			65535,
		)

	def _validate_outer_flags(self, flags):
		flags = int(flags)
		if flags & ~int(VALID_FLAG_MASK):
			raise BulkCompressionError('Reserved bulk-compression flag is set')
		packet_type = flags & int(BulkCompressionFlags.TYPE_MASK)
		if packet_type != BulkCompressionType.RDP61:
			raise BulkCompressionError(
				'RDP 6.1 decoder received compression type %d' % packet_type
			)
		if (
			flags & BulkCompressionFlags.AT_FRONT
			and not flags & BulkCompressionFlags.COMPRESSED
		):
			raise BulkCompressionError(
				'PACKET_AT_FRONT requires PACKET_COMPRESSED'
			)
		return flags

	def _validate_level1_flags(self, flags):
		if flags & ~L1_VALID_FLAGS:
			raise BulkCompressionError(
				'Reserved RDP 6.1 level-1 compression flag is set'
			)
		mode = flags & (L1_COMPRESSED | L1_NO_COMPRESSION)
		if mode not in (L1_COMPRESSED, L1_NO_COMPRESSION):
			raise BulkCompressionError(
				'RDP 6.1 packet must select exactly one level-1 mode'
			)

	def _history_value(self, history, start_offset, output, source):
		if source < 0 or source >= self.HISTORY_SIZE:
			raise BulkCompressionError(
				'RDP 6.1 match source is outside the history buffer'
			)
		if start_offset <= source < start_offset + len(output):
			return output[source - start_offset]
		return history[source]

	def _decode_level1_compressed(self, data, history, start_offset):
		if len(data) < 2:
			raise BulkCompressionError(
				'Truncated RDP 6.1 match-count field'
			)
		match_count = int.from_bytes(data[:2], 'little')
		if match_count == 0:
			raise BulkCompressionError(
				'RDP 6.1 compressed packet contains no matches'
			)
		details_end = 2 + match_count * self.MATCH_DETAILS_SIZE
		if details_end > len(data):
			raise BulkCompressionError(
				'Truncated RDP 6.1 match-details array'
			)

		details = []
		offset = 2
		for _ in range(match_count):
			match_length, output_offset, history_offset = struct.unpack_from(
				'<HHI',
				data,
				offset,
			)
			offset += self.MATCH_DETAILS_SIZE
			if match_length == 0 or match_length > self.MAX_BLOCK_SIZE:
				raise BulkCompressionError(
					'Invalid RDP 6.1 match length'
				)
			if history_offset >= self.HISTORY_SIZE:
				raise BulkCompressionError(
					'RDP 6.1 match source is outside the history buffer'
				)
			details.append((match_length, output_offset, history_offset))

		literals = data[details_end:]
		literals_offset = 0
		output = bytearray()
		for match_length, output_offset, history_offset in details:
			if output_offset < len(output):
				raise BulkCompressionError(
					'RDP 6.1 matches are not in stream order'
				)
			literal_count = output_offset - len(output)
			if literals_offset + literal_count > len(literals):
				raise BulkCompressionError(
					'RDP 6.1 match output offset exceeds literal data'
				)
			if len(output) + literal_count > self.max_output_size:
				raise BulkCompressionError(
					'RDP 6.1 output exceeds the configured decompression limit'
				)
			output.extend(
				literals[literals_offset:literals_offset + literal_count]
			)
			literals_offset += literal_count

			if len(output) + match_length > self.max_output_size:
				raise BulkCompressionError(
					'RDP 6.1 output exceeds the configured decompression limit'
				)
			for index in range(match_length):
				source = history_offset + index
				output.append(
					self._history_value(
						history,
						start_offset,
						output,
						source,
					)
				)

		remaining_literals = literals[literals_offset:]
		if len(output) + len(remaining_literals) > self.max_output_size:
			raise BulkCompressionError(
				'RDP 6.1 output exceeds the configured decompression limit'
			)
		output.extend(remaining_literals)
		return bytes(output)

	def _decode_level1(self, data, flags, history, start_offset):
		if flags & L1_NO_COMPRESSION:
			if len(data) > self.max_output_size:
				raise BulkCompressionError(
					'RDP 6.1 output exceeds the configured decompression limit'
				)
			return bytes(data)
		return self._decode_level1_compressed(
			data,
			history,
			start_offset,
		)

	def decompress(self, data, flags, expected_size=None):
		flags = self._validate_outer_flags(flags)
		data = bytes(data)

		outer_flushed = bool(flags & BulkCompressionFlags.FLUSHED)
		if outer_flushed:
			working_history = bytearray(self.HISTORY_SIZE)
			start_offset = 0
			working_level2 = MppcDecoder(
				BulkCompressionType.RDP5_64K,
				65535,
			)
		else:
			working_history = self.history
			start_offset = self.history_offset
			working_level2 = self.level2.clone()

		if not flags & BulkCompressionFlags.COMPRESSED:
			if expected_size is not None and len(data) != expected_size:
				raise BulkCompressionError(
					'Uncompressed packet length does not match its declaration'
				)
			if outer_flushed:
				self.history = working_history
				self.history_offset = 0
				self.level2 = working_level2
			return data

		if len(data) < 2:
			raise BulkCompressionError(
				'Truncated RDP 6.1 compression header'
			)
		level1_flags = data[0]
		level2_flags = data[1]
		self._validate_level1_flags(level1_flags)

		if level1_flags & L1_PACKET_AT_FRONT:
			working_history = bytearray(self.HISTORY_SIZE)
			start_offset = 0
		elif flags & BulkCompressionFlags.AT_FRONT:
			raise BulkCompressionError(
				'RDP 6.1 PACKET_AT_FRONT is missing its level-1 equivalent'
			)

		level1_data = data[2:]
		if level1_flags & L1_INNER_COMPRESSION:
			level2_type = (
				level2_flags & int(BulkCompressionFlags.TYPE_MASK)
			)
			if (
				level2_type != BulkCompressionType.RDP5_64K
				and (
					level2_type != 0
					or level2_flags & BulkCompressionFlags.COMPRESSED
				)
			):
				raise BulkCompressionError(
					'RDP 6.1 level-2 compressor is not RDP 5.0'
				)
			# The specification's raw level-2 example uses PACKET_FLUSHED
			# without repeating the 64K type nibble.  The local level-2
			# context is nevertheless always the RDP 5.0 compressor.
			effective_level2_flags = (
				level2_flags
				& ~int(BulkCompressionFlags.TYPE_MASK)
			) | BulkCompressionType.RDP5_64K
			level1_data = working_level2.decompress(
				level1_data,
				effective_level2_flags,
			)

		output = self._decode_level1(
			level1_data,
			level1_flags,
			working_history,
			start_offset,
		)
		if start_offset + len(output) > self.HISTORY_SIZE:
			raise BulkCompressionError(
				'RDP 6.1 output overruns the history buffer'
			)
		if expected_size is not None and len(output) != expected_size:
			raise BulkCompressionError(
				'Decompressed packet length does not match its declaration '
				'(%d != %d)' % (len(output), expected_size)
			)

		working_history[start_offset:start_offset + len(output)] = output
		self.history = working_history
		self.history_offset = start_offset + len(output)
		if level1_flags & L1_INNER_COMPRESSION:
			self.level2 = working_level2
		elif outer_flushed:
			self.level2 = working_level2
		return output
