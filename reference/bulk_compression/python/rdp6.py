"""Specification-derived RDP 6.0 bulk decompression.

The fixed tables and decoding rules are transcribed from [MS-RDPEGDI]
sections 3.1.8.1.3 and 3.1.8.1.4 (tables 1 through 6).
"""

from .bitstream import (
	BitReader,
	BulkCompressionError,
	HuffmanDecoder,
)
from .types import (
	BulkCompressionFlags,
	BulkCompressionType,
	VALID_FLAG_MASK,
)


HUFF_LENGTH_LEC = (
	6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8,
	8, 8, 9, 8, 9, 9, 9, 9, 8, 8, 9, 9, 9, 9, 9, 9,
	8, 9, 9, 10, 9, 9, 9, 9, 9, 9, 9, 10, 9, 10, 10, 10,
	9, 9, 10, 9, 10, 9, 10, 9, 9, 9, 10, 10, 9, 10, 9, 9,
	8, 9, 9, 9, 9, 10, 10, 10, 9, 9, 10, 10, 10, 10, 10, 10,
	9, 9, 10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10,
	8, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
	9, 10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10, 9,
	7, 9, 9, 10, 9, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10, 10,
	9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
	10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 13, 10, 10, 10, 10,
	10, 10, 11, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
	9, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 9, 10, 10, 10,
	9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
	9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 9, 10,
	8, 9, 9, 10, 9, 10, 10, 10, 9, 10, 10, 10, 9, 9, 8, 7,
	13, 13, 7, 7, 10, 7, 7, 6, 6, 6, 6, 5, 6, 6, 6, 5,
	6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
	8, 5, 6, 7, 7,
)

HUFF_CODE_LEC = (
	0x4, 0x24, 0x14, 0x11, 0x51, 0x31, 0x71, 0x9,
	0x49, 0x29, 0x69, 0x15, 0x95, 0x55, 0xD5, 0x35,
	0xB5, 0x75, 0x1D, 0xF5, 0x11D, 0x9D, 0x19D, 0x5D,
	0xD, 0x8D, 0x15D, 0xDD, 0x1DD, 0x3D, 0x13D, 0xBD,
	0x4D, 0x1BD, 0x7D, 0x6B, 0x17D, 0xFD, 0x1FD, 0x3,
	0x103, 0x83, 0x183, 0x26B, 0x43, 0x16B, 0x36B, 0xEB,
	0x143, 0xC3, 0x2EB, 0x1C3, 0x1EB, 0x23, 0x3EB, 0x123,
	0xA3, 0x1A3, 0x1B, 0x21B, 0x63, 0x11B, 0x163, 0xE3,
	0xCD, 0x1E3, 0x13, 0x113, 0x93, 0x31B, 0x9B, 0x29B,
	0x193, 0x53, 0x19B, 0x39B, 0x5B, 0x25B, 0x15B, 0x35B,
	0x153, 0xD3, 0xDB, 0x2DB, 0x1DB, 0x3DB, 0x3B, 0x23B,
	0x13B, 0x1D3, 0x33B, 0xBB, 0x2BB, 0x1BB, 0x3BB, 0x7B,
	0x2D, 0x27B, 0x17B, 0x37B, 0xFB, 0x2FB, 0x1FB, 0x3FB,
	0x7, 0x207, 0x107, 0x307, 0x87, 0x287, 0x187, 0x387,
	0x33, 0x47, 0x247, 0x147, 0x347, 0xC7, 0x2C7, 0x1C7,
	0x133, 0x3C7, 0x27, 0x227, 0x127, 0x327, 0xA7, 0xB3,
	0x19, 0x1B3, 0x73, 0x2A7, 0x173, 0x1A7, 0x3A7, 0x67,
	0xF3, 0x267, 0x167, 0x367, 0xE7, 0x2E7, 0x1E7, 0x3E7,
	0x1F3, 0x17, 0x217, 0x117, 0x317, 0x97, 0x297, 0x197,
	0x397, 0x57, 0x257, 0x157, 0x357, 0xD7, 0x2D7, 0x1D7,
	0x3D7, 0x37, 0x237, 0x137, 0x337, 0xB7, 0x2B7, 0x1B7,
	0x3B7, 0x77, 0x277, 0x7FF, 0x177, 0x377, 0xF7, 0x2F7,
	0x1F7, 0x3F7, 0x3FF, 0xF, 0x20F, 0x10F, 0x30F, 0x8F,
	0x28F, 0x18F, 0x38F, 0x4F, 0x24F, 0x14F, 0x34F, 0xCF,
	0xB, 0x2CF, 0x1CF, 0x3CF, 0x2F, 0x22F, 0x10B, 0x12F,
	0x32F, 0xAF, 0x2AF, 0x1AF, 0x8B, 0x3AF, 0x6F, 0x26F,
	0x18B, 0x16F, 0x36F, 0xEF, 0x2EF, 0x1EF, 0x3EF, 0x1F,
	0x21F, 0x11F, 0x31F, 0x9F, 0x29F, 0x19F, 0x39F, 0x5F,
	0x4B, 0x25F, 0x15F, 0x35F, 0xDF, 0x2DF, 0x1DF, 0x3DF,
	0x3F, 0x23F, 0x13F, 0x33F, 0xBF, 0x2BF, 0x14B, 0x1BF,
	0xAD, 0xCB, 0x1CB, 0x3BF, 0x2B, 0x7F, 0x27F, 0x17F,
	0x12B, 0x37F, 0xFF, 0x2FF, 0xAB, 0x1AB, 0x6D, 0x59,
	0x17FF, 0xFFF, 0x39, 0x79, 0x1FF, 0x5, 0x45, 0x34,
	0xC, 0x2C, 0x1C, 0x0, 0x3C, 0x2, 0x22, 0x10,
	0x12, 0x8, 0x32, 0xA, 0x2A, 0x1A, 0x3A, 0x6,
	0x26, 0x16, 0x36, 0xE, 0x2E, 0x1E, 0x3E, 0x1,
	0xED, 0x18, 0x21, 0x25, 0x65,
)

HUFF_LENGTH_LOM = (
	4, 2, 3, 4, 3, 4, 4, 5,
	4, 5, 5, 6, 6, 7, 7, 8,
	7, 8, 8, 9, 9, 8, 9, 9,
	9, 9, 9, 9, 9, 9, 9, 9,
)

HUFF_CODE_LOM = (
	0x1, 0x0, 0x2, 0x9, 0x6, 0x5, 0xD, 0xB,
	0x3, 0x1B, 0x7, 0x17, 0x37, 0xF, 0x4F, 0x6F,
	0x2F, 0xEF, 0x1F, 0x5F, 0x15F, 0x9F, 0xDF, 0x1DF,
	0x3F, 0x13F, 0xBF, 0x1BF, 0x7F, 0x17F, 0xFF, 0x1FF,
)

COPY_OFFSET_BITS = (
	0, 0, 0, 0, 1, 1, 2, 2,
	3, 3, 4, 4, 5, 5, 6, 6,
	7, 7, 8, 8, 9, 9, 10, 10,
	11, 11, 12, 12, 13, 13, 14, 14,
)
COPY_OFFSET_BASE = (
	1, 2, 3, 4, 5, 7, 9, 13,
	17, 25, 33, 49, 65, 97, 129, 193,
	257, 385, 513, 769, 1025, 1537, 2049, 3073,
	4097, 6145, 8193, 12289, 16385, 24577, 32769, 49153,
)
MATCH_LENGTH_BITS = (
	0, 0, 0, 0, 0, 0, 0, 0,
	1, 1, 1, 1, 2, 2, 2, 2,
	3, 3, 3, 3, 4, 4, 4, 4,
	6, 6, 8, 8, 14, 14,
)
MATCH_LENGTH_BASE = (
	2, 3, 4, 5, 6, 7, 8, 9,
	10, 12, 14, 16, 18, 22, 26, 30,
	34, 42, 50, 58, 66, 82, 98, 114,
	130, 194, 258, 514, 2, 2,
)

# RDP 6.0 writes the least-significant code bit first.  Reversing the
# specification's numeric code words yields prefix codes in stream order.
LEC_DECODER = HuffmanDecoder(
	HUFF_CODE_LEC,
	HUFF_LENGTH_LEC,
	least_significant_bit_first=True,
)
LOM_DECODER = HuffmanDecoder(
	HUFF_CODE_LOM,
	HUFF_LENGTH_LOM,
	least_significant_bit_first=True,
)


class Rdp6Decoder:
	HISTORY_SIZE = 65536
	SLIDE_OFFSET = 32768

	def __init__(self, max_output_size=None):
		codec_limit = self.HISTORY_SIZE - 1
		if max_output_size is None:
			self.max_output_size = codec_limit
		else:
			if max_output_size <= 0:
				raise ValueError('Maximum decompressed size must be positive')
			self.max_output_size = min(max_output_size, codec_limit)
		self.history = bytearray(self.HISTORY_SIZE)
		self.history_offset = 0
		self.offset_cache = []

	def _validate_flags(self, flags):
		flags = int(flags)
		if flags & ~int(VALID_FLAG_MASK):
			raise BulkCompressionError('Reserved bulk-compression flag is set')
		packet_type = flags & int(BulkCompressionFlags.TYPE_MASK)
		if packet_type != BulkCompressionType.RDP6:
			raise BulkCompressionError(
				'RDP 6.0 decoder received compression type %d' % packet_type
			)
		if (
			flags & BulkCompressionFlags.AT_FRONT
			and not flags & BulkCompressionFlags.COMPRESSED
		):
			raise BulkCompressionError(
				'PACKET_AT_FRONT requires PACKET_COMPRESSED'
			)
		return flags

	def _cache_new_offset(self, cache, copy_offset):
		if copy_offset in cache:
			cache.remove(copy_offset)
		cache.insert(0, copy_offset)
		del cache[4:]

	def _cache_offset(self, cache, index):
		if index >= len(cache):
			raise BulkCompressionError(
				'RDP 6.0 offset-cache reference is not initialized'
			)
		copy_offset = cache[index]
		cache[0], cache[index] = cache[index], cache[0]
		return copy_offset

	def _append_copy(
		self,
		output,
		history,
		start_offset,
		copy_offset,
		match_length,
	):
		if copy_offset <= 0 or copy_offset >= self.HISTORY_SIZE:
			raise BulkCompressionError(
				'RDP 6.0 copy offset is outside the history window'
			)
		if match_length < 2:
			raise BulkCompressionError(
				'RDP 6.0 match is shorter than two bytes'
			)
		if len(output) + match_length > self.max_output_size:
			raise BulkCompressionError(
				'RDP 6.0 output exceeds the configured decompression limit'
			)
		if start_offset + len(output) + match_length > self.HISTORY_SIZE:
			raise BulkCompressionError(
				'RDP 6.0 output overruns the history buffer'
			)

		for _ in range(match_length):
			source = (
				start_offset + len(output) - copy_offset
			) % self.HISTORY_SIZE
			if start_offset <= source < start_offset + len(output):
				value = output[source - start_offset]
			else:
				value = history[source]
			output.append(value)

	def _decode_stream(self, data, history, start_offset, cache):
		# OutputBits also packs numeric extra fields least-significant bit first.
		reader = BitReader(data, least_significant_bit_first=True)
		output = bytearray()
		saw_eos = False

		while reader.remaining_bits:
			symbol = LEC_DECODER.decode(reader)
			if symbol < 256:
				if len(output) >= self.max_output_size:
					raise BulkCompressionError(
						'RDP 6.0 output exceeds the configured decompression limit'
					)
				if start_offset + len(output) >= self.HISTORY_SIZE:
					raise BulkCompressionError(
						'RDP 6.0 output overruns the history buffer'
					)
				output.append(symbol)
				continue
			if symbol == 256:
				saw_eos = True
				break

			if 257 <= symbol <= 288:
				index = symbol - 257
				copy_offset = (
					COPY_OFFSET_BASE[index]
					+ reader.read_bits(COPY_OFFSET_BITS[index])
					- 1
				)
				self._cache_new_offset(cache, copy_offset)
			elif 289 <= symbol <= 292:
				copy_offset = self._cache_offset(cache, symbol - 289)
			else:
				raise BulkCompressionError(
					'Invalid RDP 6.0 literal/copy symbol'
				)

			length_index = LOM_DECODER.decode(reader)
			if length_index >= len(MATCH_LENGTH_BITS):
				raise BulkCompressionError(
					'Reserved RDP 6.0 length-of-match symbol'
				)
			match_length = (
				MATCH_LENGTH_BASE[length_index]
				+ reader.read_bits(MATCH_LENGTH_BITS[length_index])
			)
			self._append_copy(
				output,
				history,
				start_offset,
				copy_offset,
				match_length,
			)

		if not saw_eos:
			raise BulkCompressionError('RDP 6.0 stream has no EOS marker')
		# EOS defines the end of the encoded stream.  The remaining storage
		# bits are outside the logical compressed stream.
		return bytes(output)

	def decompress(self, data, flags, expected_size=None):
		flags = self._validate_flags(flags)
		data = bytes(data)
		cache = list(self.offset_cache)

		if flags & BulkCompressionFlags.FLUSHED:
			working_history = bytearray(self.HISTORY_SIZE)
			start_offset = 0
			cache = []
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
				self.offset_cache = []
			return data

		if flags & BulkCompressionFlags.AT_FRONT:
			if working_history is self.history:
				working_history = bytearray(self.history)
			recent_start = (
				start_offset - self.SLIDE_OFFSET
			) % self.HISTORY_SIZE
			recent_end = recent_start + self.SLIDE_OFFSET
			if recent_end <= self.HISTORY_SIZE:
				recent_history = working_history[recent_start:recent_end]
			else:
				recent_history = (
					working_history[recent_start:]
					+ working_history[:recent_end - self.HISTORY_SIZE]
				)
			working_history[:self.SLIDE_OFFSET] = recent_history
			start_offset = self.SLIDE_OFFSET

		output = self._decode_stream(
			data,
			working_history,
			start_offset,
			cache,
		)
		if expected_size is not None and len(output) != expected_size:
			raise BulkCompressionError(
				'Decompressed packet length does not match its declaration '
				'(%d != %d)' % (len(output), expected_size)
			)

		working_history[start_offset:start_offset + len(output)] = output
		self.history = working_history
		self.history_offset = start_offset + len(output)
		self.offset_cache = cache
		return output
