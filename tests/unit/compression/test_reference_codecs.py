"""Pure-Python reference codec edge cases collected by the canonical suite."""

import unittest

import pytest

from reference.bulk_compression.python import (
	BulkCompressionError,
	BulkCompressionType,
	BulkDecompressor,
)
from reference.bulk_compression.python.mppc import MppcDecoder
from reference.bulk_compression.python.rdp6 import (
	COPY_OFFSET_BASE,
	COPY_OFFSET_BITS,
	HUFF_CODE_LEC,
	HUFF_CODE_LOM,
	HUFF_LENGTH_LEC,
	HUFF_LENGTH_LOM,
	MATCH_LENGTH_BASE,
	MATCH_LENGTH_BITS,
	Rdp6Decoder,
)


pytestmark = pytest.mark.unit


class BitWriter:
	def __init__(self):
		self.bits = ''

	def add(self, value, width):
		if value < 0 or value >= 1 << width:
			raise ValueError('Value does not fit')
		if width == 0:
			return
		self.bits += format(value, '0%db' % width)

	def add_text(self, value):
		self.bits += value

	def add_lsb(self, value, width):
		if width:
			self.add_text(format(value, '0%db' % width)[::-1])

	def to_bytes(self):
		bits = self.bits + ('0' * (-len(self.bits) % 8))
		if not bits:
			return b''
		return int(bits, 2).to_bytes(len(bits) // 8, 'big')

	def to_lsb_first_bytes(self):
		bits = self.bits + ('0' * (-len(self.bits) % 8))
		return bytes(
			int(bits[index:index + 8][::-1], 2)
			for index in range(0, len(bits), 8)
		)


def encode_mppc_literal(writer, value):
	if value < 0x80:
		writer.add(value, 8)
	else:
		writer.add_text('10')
		writer.add(value & 0x7F, 7)


def encode_mppc_offset(writer, value, is_64k=False):
	if value < 64:
		writer.add_text('11111' if is_64k else '1111')
		writer.add(value, 6)
	elif value < 320:
		writer.add_text('11110' if is_64k else '1110')
		writer.add(value - 64, 8)
	elif not is_64k:
		writer.add_text('110')
		writer.add(value - 320, 13)
	elif value < 2368:
		writer.add_text('1110')
		writer.add(value - 320, 11)
	else:
		writer.add_text('110')
		writer.add(value - 2368, 16)


def encode_mppc_length(writer, value):
	if value == 3:
		writer.add_text('0')
		return
	extra_bits = value.bit_length() - 1
	writer.add_text(('1' * (extra_bits - 1)) + '0')
	writer.add(value & ((1 << extra_bits) - 1), extra_bits)


def encode_mppc_copy(copy_offset, match_length, is_64k=False):
	writer = BitWriter()
	encode_mppc_offset(writer, copy_offset, is_64k)
	encode_mppc_length(writer, match_length)
	return writer.to_bytes()


def reverse_code(code, width):
	return format(code, '0%db' % width)[::-1]


def encode_rdp6_symbol(writer, symbol):
	writer.add_text(reverse_code(HUFF_CODE_LEC[symbol], HUFF_LENGTH_LEC[symbol]))


def encode_rdp6_length(writer, length, forced_index=None):
	if forced_index is None:
		if length >= 770:
			index = 28
		else:
			index = max(
				i
				for i in range(28)
				if MATCH_LENGTH_BASE[i] <= length
			)
	else:
		index = forced_index
	writer.add_text(
		reverse_code(HUFF_CODE_LOM[index], HUFF_LENGTH_LOM[index])
	)
	writer.add_lsb(
		length - MATCH_LENGTH_BASE[index],
		MATCH_LENGTH_BITS[index],
	)


def encode_rdp6_offset(writer, copy_offset):
	index = max(
		i
		for i, base in enumerate(COPY_OFFSET_BASE)
		if base <= copy_offset + 1
	)
	encode_rdp6_symbol(writer, index + 257)
	writer.add_lsb(
		copy_offset + 1 - COPY_OFFSET_BASE[index],
		COPY_OFFSET_BITS[index],
	)


def finish_rdp6(writer):
	encode_rdp6_symbol(writer, 256)
	return writer.to_lsb_first_bytes()


class MppcDecoderTests(unittest.TestCase):
	def test_rdp4_literals_and_overlap_copy(self):
		writer = BitWriter()
		for value in b'abc':
			encode_mppc_literal(writer, value)
		encode_mppc_offset(writer, 3)
		encode_mppc_length(writer, 6)

		decoder = MppcDecoder(BulkCompressionType.RDP4_8K)
		self.assertEqual(
			decoder.decompress(writer.to_bytes(), 0x60),
			b'abcabcabc',
		)

	def test_rdp5_high_literal(self):
		writer = BitWriter()
		encode_mppc_literal(writer, 0xE7)
		encode_mppc_literal(writer, ord('A'))

		decoder = MppcDecoder(BulkCompressionType.RDP5_64K)
		self.assertEqual(decoder.decompress(writer.to_bytes(), 0x61), b'\xE7A')

	def test_copy_offset_encoding_boundaries(self):
		for compression_type, offsets in (
			(BulkCompressionType.RDP4_8K, (1, 63, 64, 319, 320, 4000)),
			(BulkCompressionType.RDP5_64K, (1, 63, 64, 319, 320, 2367, 2368, 4000)),
		):
			for copy_offset in offsets:
				with self.subTest(
					compression_type=compression_type,
					copy_offset=copy_offset,
				):
					decoder = MppcDecoder(compression_type)
					decoder.history_offset = 5000
					source = 5000 - copy_offset
					decoder.history[source:source + 3] = b'zzz'
					stream = encode_mppc_copy(
						copy_offset,
						3,
						compression_type == BulkCompressionType.RDP5_64K,
					)
					self.assertEqual(
						decoder.decompress(stream, int(compression_type) | 0x20),
						b'zzz',
					)

	def test_length_encoding_boundaries(self):
		for compression_type, lengths in (
			(
				BulkCompressionType.RDP4_8K,
				(3, 4, 7, 8, 31, 32, 127, 128, 511, 512, 4095, 4096, 8190),
			),
			(
				BulkCompressionType.RDP5_64K,
				(3, 4, 15, 16, 255, 256, 8191, 8192, 32767, 32768, 65534),
			),
		):
			for length in lengths:
				with self.subTest(
					compression_type=compression_type,
					length=length,
				):
					decoder = MppcDecoder(compression_type)
					decoder.history[0] = ord('z')
					decoder.history_offset = 1
					stream = encode_mppc_copy(
						1,
						length,
						compression_type == BulkCompressionType.RDP5_64K,
					)
					self.assertEqual(
						decoder.decompress(stream, int(compression_type) | 0x20),
						b'z' * length,
					)

	def test_flush_front_and_raw_transitions(self):
		decoder = MppcDecoder(BulkCompressionType.RDP4_8K)
		writer = BitWriter()
		for value in b'abc':
			encode_mppc_literal(writer, value)
		self.assertEqual(decoder.decompress(writer.to_bytes(), 0xE0), b'abc')
		self.assertEqual(decoder.history_offset, 3)

		writer = BitWriter()
		encode_mppc_literal(writer, ord('d'))
		self.assertEqual(decoder.decompress(writer.to_bytes(), 0x20), b'd')
		self.assertEqual(decoder.history_offset, 4)

		writer = BitWriter()
		encode_mppc_literal(writer, ord('x'))
		self.assertEqual(decoder.decompress(writer.to_bytes(), 0x60), b'x')
		self.assertEqual(decoder.history_offset, 1)
		self.assertEqual(decoder.decompress(b'raw', 0x80), b'raw')
		self.assertEqual(decoder.history_offset, 0)
		self.assertEqual(decoder.history[:4], b'\x00' * 4)

	def test_copy_offset_wraps_across_history_front(self):
		decoder = MppcDecoder(BulkCompressionType.RDP4_8K)
		decoder.history[-3:] = b'abc'
		self.assertEqual(
			decoder.decompress(encode_mppc_copy(3, 3), 0x60),
			b'abc',
		)

	def test_malformed_stream_is_transactional(self):
		decoder = MppcDecoder(BulkCompressionType.RDP4_8K)
		decoder.history[:4] = b'seed'
		decoder.history_offset = 4
		before = bytes(decoder.history)

		with self.assertRaises(BulkCompressionError):
			decoder.decompress(b'\xff', 0x20)

		self.assertEqual(decoder.history_offset, 4)
		self.assertEqual(bytes(decoder.history), before)

	def test_output_limit_stops_decompression_bomb(self):
		decoder = MppcDecoder(
			BulkCompressionType.RDP4_8K,
			max_output_size=3,
		)
		decoder.history[0] = ord('a')
		decoder.history_offset = 1

		with self.assertRaisesRegex(BulkCompressionError, 'limit'):
			decoder.decompress(encode_mppc_copy(1, 4), 0x20)


class Rdp6DecoderTests(unittest.TestCase):
	def test_literals_copy_and_offset_cache(self):
		writer = BitWriter()
		encode_rdp6_symbol(writer, ord('a'))
		encode_rdp6_offset(writer, 1)
		encode_rdp6_length(writer, 2)
		encode_rdp6_symbol(writer, 289)
		encode_rdp6_length(writer, 2)

		decoder = Rdp6Decoder()
		self.assertEqual(decoder.decompress(finish_rdp6(writer), 0x62), b'aaaaa')
		self.assertEqual(decoder.offset_cache, [1])

	def test_length_boundaries(self):
		for length in (2, 3, 9, 10, 17, 18, 65, 66, 129, 130, 257, 258, 769, 770, 16382):
			with self.subTest(length=length):
				decoder = Rdp6Decoder()
				decoder.history[0] = ord('q')
				decoder.history_offset = 1
				writer = BitWriter()
				encode_rdp6_offset(writer, 1)
				encode_rdp6_length(writer, length)
				self.assertEqual(
					decoder.decompress(finish_rdp6(writer), 0x22),
					b'q' * length,
				)

	def test_slide_back_places_output_at_middle(self):
		decoder = Rdp6Decoder()
		decoder.history[17232:17236] = b'abcd'
		decoder.history_offset = 50000
		writer = BitWriter()
		encode_rdp6_symbol(writer, ord('x'))

		self.assertEqual(decoder.decompress(finish_rdp6(writer), 0x62), b'x')
		self.assertEqual(decoder.history[:4], b'abcd')
		self.assertEqual(decoder.history_offset, 32769)
		self.assertEqual(decoder.history[32768], ord('x'))

	def test_copy_offset_wraps_across_history_front(self):
		decoder = Rdp6Decoder()
		decoder.history[-3:] = b'abc'
		writer = BitWriter()
		encode_rdp6_offset(writer, 3)
		encode_rdp6_length(writer, 3)
		self.assertEqual(
			decoder.decompress(finish_rdp6(writer), 0x22),
			b'abc',
		)

	def test_invalid_cache_reference_is_transactional(self):
		decoder = Rdp6Decoder()
		writer = BitWriter()
		encode_rdp6_symbol(writer, 289)
		encode_rdp6_length(writer, 2)

		with self.assertRaisesRegex(BulkCompressionError, 'not initialized'):
			decoder.decompress(finish_rdp6(writer), 0x22)

		self.assertEqual(decoder.history_offset, 0)
		self.assertEqual(decoder.offset_cache, [])

	def test_missing_eos_is_rejected(self):
		writer = BitWriter()
		encode_rdp6_symbol(writer, ord('x'))
		with self.assertRaises(BulkCompressionError):
			Rdp6Decoder().decompress(writer.to_lsb_first_bytes(), 0x22)

	def test_eos_terminates_before_trailing_storage(self):
		writer = BitWriter()
		encode_rdp6_symbol(writer, ord('x'))
		stream = finish_rdp6(writer)
		self.assertEqual(
			Rdp6Decoder().decompress(stream + b'\xff\xff', 0x22),
			b'x',
		)


class Rdp61DecoderTests(unittest.TestCase):
	def test_official_raw_and_match_examples(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		self.assertEqual(
			decoder.decompress(b'\x16\x80abcdefghij', 0x23),
			b'abcdefghij',
		)
		second = bytes.fromhex(
			'01 00 02 00 '
			'09 00 05 00 03 00 00 00 '
			'04 00 0e 00 00 00 00 00 '
			'6b 6c 6d 6e 6f 75'
		)
		self.assertEqual(
			decoder.decompress(second, 0x23),
			b'klmnodefghijklabcdu',
		)

	def test_level2_chaining(self):
		level1_bytes = b'chain me'
		writer = BitWriter()
		for value in level1_bytes:
			encode_mppc_literal(writer, value)
		packet = bytes([0x16, 0xE1]) + writer.to_bytes()

		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		self.assertEqual(decoder.decompress(packet, 0x23), level1_bytes)

	def test_invalid_match_order_does_not_mutate_history(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		decoder.decompress(b'\x06\x00seed', 0x23)
		codec = decoder._decoder
		before_offset = codec.history_offset
		before = bytes(codec.history[:before_offset])
		packet = bytes.fromhex(
			'01 00 02 00 '
			'03 00 02 00 00 00 00 00 '
			'03 00 01 00 00 00 00 00 '
			'61 62'
		)

		with self.assertRaisesRegex(BulkCompressionError, 'stream order'):
			decoder.decompress(packet, 0x23)

		self.assertEqual(codec.history_offset, before_offset)
		self.assertEqual(bytes(codec.history[:before_offset]), before)

	def test_match_count_truncation_is_rejected(self):
		with self.assertRaisesRegex(BulkCompressionError, 'match-details'):
			BulkDecompressor(BulkCompressionType.RDP61).decompress(
				b'\x01\x00\x01\x00',
				0x23,
			)


class DispatcherAndPathTests(unittest.TestCase):
	def test_rejects_codec_above_negotiated_maximum(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP4_8K)
		with self.assertRaisesRegex(BulkCompressionError, 'above negotiated'):
			decoder.decompress(b'', 0x21)

	def test_rejects_midstream_codec_transition(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		decoder.decompress(b'', 0x80)
		with self.assertRaisesRegex(BulkCompressionError, 'changed'):
			decoder.decompress(b'raw', 0x01)

	def test_zero_flags_do_not_select_the_ambiguous_8k_type(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		self.assertEqual(decoder.decompress(b'raw', 0x00), b'raw')
		self.assertIsNone(decoder.selected_type)
		self.assertEqual(decoder.compressed_packet_count, 0)
		self.assertEqual(decoder.compressed_byte_count, 0)
		self.assertEqual(
			decoder.decompress(b'\x06\x00data', 0x23),
			b'data',
		)
		self.assertEqual(decoder.selected_type, BulkCompressionType.RDP61)
		self.assertEqual(decoder.compressed_packet_count, 1)
		self.assertEqual(decoder.compressed_byte_count, 6)
		self.assertEqual(decoder.decompressed_byte_count, 4)


if __name__ == '__main__':
	unittest.main()
