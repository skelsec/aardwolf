"""RDP 4.0 and RDP 5.0 bulk decompression.

The token formats in this module are independently implemented from
[MS-RDPBCGR] sections 3.1.8.3 and 3.1.8.4 and RFC 2118.
"""

from .bitstream import BitReader, BulkCompressionError
from .types import (
	BulkCompressionFlags,
	BulkCompressionType,
	VALID_FLAG_MASK,
)


class MppcDecoder:
	def __init__(self, compression_type, max_output_size=None):
		self.compression_type = BulkCompressionType(compression_type)
		if self.compression_type == BulkCompressionType.RDP4_8K:
			self.history_size = 8192
		elif self.compression_type == BulkCompressionType.RDP5_64K:
			self.history_size = 65536
		else:
			raise ValueError('MPPC supports only the RDP 4.0 and RDP 5.0 types')

		codec_limit = self.history_size - 1
		if max_output_size is None:
			self.max_output_size = codec_limit
		else:
			if max_output_size <= 0:
				raise ValueError('Maximum decompressed size must be positive')
			self.max_output_size = min(max_output_size, codec_limit)
		self.history = bytearray(self.history_size)
		self.history_offset = 0

	def clone(self):
		clone = MppcDecoder(self.compression_type, self.max_output_size)
		clone.history[:] = self.history
		clone.history_offset = self.history_offset
		return clone

	def _validate_flags(self, flags):
		flags = int(flags)
		if flags & ~int(VALID_FLAG_MASK):
			raise BulkCompressionError('Reserved bulk-compression flag is set')
		packet_type = flags & int(BulkCompressionFlags.TYPE_MASK)
		if packet_type != self.compression_type:
			raise BulkCompressionError(
				'Bulk-compression type changed from %d to %d'
				% (self.compression_type, packet_type)
			)
		if (
			flags & BulkCompressionFlags.AT_FRONT
			and not flags & BulkCompressionFlags.COMPRESSED
		):
			raise BulkCompressionError(
				'PACKET_AT_FRONT requires PACKET_COMPRESSED'
			)
		return flags

	def _decode_copy_offset(self, reader):
		# The caller has consumed the initial "11" copy-tuple prefix.
		if self.compression_type == BulkCompressionType.RDP4_8K:
			if reader.read_bits(1) == 0:
				return 320 + reader.read_bits(13)
			if reader.read_bits(1) == 0:
				return 64 + reader.read_bits(8)
			return reader.read_bits(6)

		if reader.read_bits(1) == 0:
			return 2368 + reader.read_bits(16)
		if reader.read_bits(1) == 0:
			return 320 + reader.read_bits(11)
		if reader.read_bits(1) == 0:
			return 64 + reader.read_bits(8)
		return reader.read_bits(6)

	def _decode_match_length(self, reader):
		if reader.read_bits(1) == 0:
			return 3

		max_extra_bits = (
			12
			if self.compression_type == BulkCompressionType.RDP4_8K
			else 15
		)
		extra_bits = 2
		while True:
			if reader.read_bits(1) == 0:
				break
			extra_bits += 1
			if extra_bits > max_extra_bits:
				raise BulkCompressionError(
					'Invalid MPPC length-of-match prefix'
				)
		return (1 << extra_bits) | reader.read_bits(extra_bits)

	def _append_copy(self, output, history, start_offset, copy_offset, length):
		if copy_offset <= 0 or copy_offset >= self.history_size:
			raise BulkCompressionError(
				'MPPC copy offset is outside the history window'
			)
		if length < 3:
			raise BulkCompressionError('MPPC match is shorter than three bytes')
		if len(output) + length > self.max_output_size:
			raise BulkCompressionError(
				'MPPC output exceeds the configured decompression limit'
			)
		if start_offset + len(output) + length > self.history_size:
			raise BulkCompressionError('MPPC output overruns the history buffer')

		for _ in range(length):
			source = (
				start_offset + len(output) - copy_offset
			) % self.history_size
			if start_offset <= source < start_offset + len(output):
				value = output[source - start_offset]
			else:
				value = history[source]
			output.append(value)

	def _decode_stream(self, data, history, start_offset):
		reader = BitReader(data)
		output = bytearray()

		while reader.remaining_bits >= 8:
			if reader.read_bits(1) == 0:
				output.append(reader.read_bits(7))
			elif reader.read_bits(1) == 0:
				output.append(0x80 | reader.read_bits(7))
			else:
				copy_offset = self._decode_copy_offset(reader)
				match_length = self._decode_match_length(reader)
				self._append_copy(
					output,
					history,
					start_offset,
					copy_offset,
					match_length,
				)

			if len(output) > self.max_output_size:
				raise BulkCompressionError(
					'MPPC output exceeds the configured decompression limit'
				)
			if start_offset + len(output) > self.history_size:
				raise BulkCompressionError('MPPC output overruns the history buffer')

		if not reader.padding_is_zero():
			raise BulkCompressionError('Nonzero MPPC padding bits')
		return bytes(output)

	def decompress(self, data, flags, expected_size=None):
		flags = self._validate_flags(flags)
		data = bytes(data)

		if flags & BulkCompressionFlags.FLUSHED:
			working_history = bytearray(self.history_size)
			start_offset = 0
		else:
			working_history = self.history
			start_offset = self.history_offset

		if not flags & BulkCompressionFlags.COMPRESSED:
			if expected_size is not None and len(data) != expected_size:
				raise BulkCompressionError(
					'Uncompressed packet length does not match its declaration'
				)
			if flags & BulkCompressionFlags.FLUSHED:
				self.history = working_history
				self.history_offset = 0
			return data

		if flags & BulkCompressionFlags.AT_FRONT:
			start_offset = 0

		output = self._decode_stream(data, working_history, start_offset)
		if expected_size is not None and len(output) != expected_size:
			raise BulkCompressionError(
				'Decompressed packet length does not match its declaration '
				'(%d != %d)' % (len(output), expected_size)
			)

		if working_history is self.history:
			target_history = self.history
		else:
			target_history = working_history
		target_history[start_offset:start_offset + len(output)] = output
		self.history = target_history
		self.history_offset = start_offset + len(output)
		return output
