"""Native bulk-compression decoder parity with the Python reference."""

import unittest

import pytest

from aardwolf.protocol.compression import (
	BulkCompressionError,
	BulkCompressionFlags,
	BulkCompressionType,
	BulkDecompressor,
)
from reference.bulk_compression.python import (
	BulkDecompressor as ReferenceBulkDecompressor,
)


pytestmark = pytest.mark.unit


class BitWriter:
	"""Small, decoder-independent writer for specification-level test vectors."""

	def __init__(self):
		self.bits = []

	def add_msb(self, value, width):
		if value < 0 or value >= 1 << width:
			raise ValueError('Value does not fit')
		self.bits.extend((value >> shift) & 1 for shift in reversed(range(width)))

	def add_lsb(self, value, width):
		if value < 0 or value >= 1 << width:
			raise ValueError('Value does not fit')
		self.bits.extend((value >> shift) & 1 for shift in range(width))

	def add_text(self, value):
		if any(bit not in '01' for bit in value):
			raise ValueError('Bit text contains a non-bit character')
		self.bits.extend(int(bit) for bit in value)

	def _padded_bits(self):
		return self.bits + ([0] * (-len(self.bits) % 8))

	def to_msb_bytes(self):
		bits = self._padded_bits()
		return bytes(
			sum(bit << (7 - offset) for offset, bit in enumerate(bits[index:index + 8]))
			for index in range(0, len(bits), 8)
		)

	def to_lsb_bytes(self):
		bits = self._padded_bits()
		return bytes(
			sum(bit << offset for offset, bit in enumerate(bits[index:index + 8]))
			for index in range(0, len(bits), 8)
		)


def add_mppc_literal(writer, value):
	if value < 0x80:
		writer.add_msb(value, 8)
	else:
		writer.add_text('10')
		writer.add_msb(value & 0x7F, 7)


def add_mppc_offset(writer, copy_offset, is_64k):
	if copy_offset < 1:
		raise ValueError('Copy offsets are one-based')
	if copy_offset < 64:
		writer.add_text('11111' if is_64k else '1111')
		writer.add_msb(copy_offset, 6)
	elif copy_offset < 320:
		writer.add_text('11110' if is_64k else '1110')
		writer.add_msb(copy_offset - 64, 8)
	elif not is_64k:
		writer.add_text('110')
		writer.add_msb(copy_offset - 320, 13)
	elif copy_offset < 2368:
		writer.add_text('1110')
		writer.add_msb(copy_offset - 320, 11)
	else:
		writer.add_text('110')
		writer.add_msb(copy_offset - 2368, 16)


def add_mppc_length(writer, match_length):
	if match_length < 3:
		raise ValueError('MPPC matches contain at least three bytes')
	if match_length == 3:
		writer.add_text('0')
		return
	extra_bits = match_length.bit_length() - 1
	writer.add_text(('1' * (extra_bits - 1)) + '0')
	writer.add_msb(match_length & ((1 << extra_bits) - 1), extra_bits)


def make_mppc_vector(literals=b'', copies=(), is_64k=False):
	writer = BitWriter()
	for value in literals:
		add_mppc_literal(writer, value)
	for copy_offset, match_length in copies:
		add_mppc_offset(writer, copy_offset, is_64k)
		add_mppc_length(writer, match_length)
	return writer.to_msb_bytes()


# These are the small subset of the fixed RDP 6.0 Huffman codebook needed by
# these vectors. Codes are numeric code words and are written low bit first.
RDP6_LEC_CODEWORDS = {
	ord('a'): (0x27B, 10),
	ord('b'): (0x17B, 10),
	256: (0x17FF, 13),  # EOS
	258: (0x39, 7),  # new copy offset with base 2
	259: (0x79, 7),  # new copy offset with base 3
	289: (0x18, 5),  # offset-cache entry 0
	290: (0x21, 6),
	291: (0x25, 7),
	292: (0x65, 7),  # offset-cache entry 3
}
RDP6_COPY_CLASSES = {
	1: (258, 2, 0),
	2: (259, 3, 0),
}
RDP6_LENGTH_CODEWORDS = {
	2: (0x1, 4, 0, 0),
	4: (0x2, 3, 0, 0),
}


def add_rdp6_symbol(writer, symbol):
	code, width = RDP6_LEC_CODEWORDS[symbol]
	writer.add_lsb(code, width)


def add_rdp6_offset(writer, copy_offset):
	symbol, base, extra_width = RDP6_COPY_CLASSES[copy_offset]
	add_rdp6_symbol(writer, symbol)
	writer.add_lsb(copy_offset + 1 - base, extra_width)


def add_rdp6_length(writer, match_length):
	code, width, base, extra_width = RDP6_LENGTH_CODEWORDS[match_length]
	writer.add_lsb(code, width)
	writer.add_lsb(match_length - base if extra_width else 0, extra_width)


def make_rdp6_vector(literals=b'', copies=(), cached_copies=(), include_eos=True):
	writer = BitWriter()
	for value in literals:
		add_rdp6_symbol(writer, value)
	for copy_offset, match_length in copies:
		add_rdp6_offset(writer, copy_offset)
		add_rdp6_length(writer, match_length)
	for cache_index, match_length in cached_copies:
		add_rdp6_symbol(writer, 289 + cache_index)
		add_rdp6_length(writer, match_length)
	if include_eos:
		add_rdp6_symbol(writer, 256)
	return writer.to_lsb_bytes()


RDP61_L1_COMPRESSED = 0x01
RDP61_L1_NO_COMPRESSION = 0x02
RDP61_L1_PACKET_AT_FRONT = 0x04
RDP61_L1_INNER_COMPRESSION = 0x10


def make_rdp61_inner_vector(payload, level2_flags, at_front=False):
	level1_flags = RDP61_L1_NO_COMPRESSION | RDP61_L1_INNER_COMPRESSION
	if at_front:
		level1_flags |= RDP61_L1_PACKET_AT_FRONT
	return bytes((level1_flags, int(level2_flags))) + payload


def make_rdp61_raw_vector(payload, at_front=False):
	level1_flags = RDP61_L1_NO_COMPRESSION
	if at_front:
		level1_flags |= RDP61_L1_PACKET_AT_FRONT
	return bytes((level1_flags, 0)) + payload


def make_rdp61_match_vector(matches, literals=b''):
	packet = bytearray((RDP61_L1_COMPRESSED, 0))
	packet.extend(len(matches).to_bytes(2, 'little'))
	for match_length, output_offset, history_offset in matches:
		packet.extend(match_length.to_bytes(2, 'little'))
		packet.extend(output_offset.to_bytes(2, 'little'))
		packet.extend(history_offset.to_bytes(4, 'little'))
	packet.extend(literals)
	return bytes(packet)


def compression_flags(compression_type, *flags):
	value = int(compression_type)
	for flag in flags:
		value |= int(flag)
	return BulkCompressionFlags(value)


def public_state(decoder):
	return (
		decoder.max_compression_type,
		decoder.selected_type,
		decoder.packet_count,
		decoder.compressed_packet_count,
		decoder.compressed_byte_count,
		decoder.decompressed_byte_count,
		decoder.history_offset,
		decoder.history_size,
		decoder.offset_cache_len,
		decoder.level2_history_offset,
	)


def make_seeded_decoder(compression_type, max_compression_type=None):
	decoder = BulkDecompressor(
		compression_type
		if max_compression_type is None
		else max_compression_type
	)
	if compression_type == BulkCompressionType.RDP4_8K:
		packet = make_mppc_vector(literals=b'abc')
		flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.AT_FRONT,
			BulkCompressionFlags.FLUSHED,
		)
		decoder.decompress(packet, flags, expected_size=3)
	elif compression_type == BulkCompressionType.RDP5_64K:
		packet = make_mppc_vector(literals=b'xy', is_64k=True)
		flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.AT_FRONT,
			BulkCompressionFlags.FLUSHED,
		)
		decoder.decompress(packet, flags, expected_size=2)
	elif compression_type == BulkCompressionType.RDP6:
		packet = make_rdp6_vector(literals=b'ab', copies=((2, 4),))
		flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.FLUSHED,
		)
		decoder.decompress(packet, flags, expected_size=6)
	else:
		level2 = make_mppc_vector(literals=b'chain', is_64k=True)
		packet = make_rdp61_inner_vector(
			level2,
			compression_flags(
				BulkCompressionType.RDP5_64K,
				BulkCompressionFlags.COMPRESSED,
				BulkCompressionFlags.AT_FRONT,
				BulkCompressionFlags.FLUSHED,
			),
			at_front=True,
		)
		flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
		)
		decoder.decompress(packet, flags, expected_size=5)
	return decoder


class SuccessfulParityTests(unittest.TestCase):
	def assert_sequence_parity(self, compression_type, packets):
		native = BulkDecompressor(compression_type)
		reference = ReferenceBulkDecompressor(int(compression_type))
		for index, (packet, flags, expected) in enumerate(packets):
			with self.subTest(packet=index):
				native_output = native.decompress(
					packet,
					flags,
					expected_size=len(expected),
				)
				reference_output = reference.decompress(
					packet,
					int(flags),
					expected_size=len(expected),
				)
				self.assertEqual(native_output, expected)
				self.assertEqual(reference_output, expected)
				self.assertEqual(native_output, reference_output)
		return native

	def test_rdp4_multi_packet_parity(self):
		compression_type = BulkCompressionType.RDP4_8K
		first_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.AT_FRONT,
			BulkCompressionFlags.FLUSHED,
		)
		next_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
		)
		decoder = self.assert_sequence_parity(
			compression_type,
			(
				(make_mppc_vector(literals=b'abc'), first_flags, b'abc'),
				(make_mppc_vector(copies=((3, 6),)), next_flags, b'abcabc'),
			),
		)
		self.assertEqual(decoder.history_offset, 9)
		self.assertEqual(decoder.history_size, 8192)

	def test_rdp5_multi_packet_parity(self):
		compression_type = BulkCompressionType.RDP5_64K
		first_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.AT_FRONT,
			BulkCompressionFlags.FLUSHED,
		)
		next_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
		)
		decoder = self.assert_sequence_parity(
			compression_type,
			(
				(
					make_mppc_vector(literals=b'\xE7A', is_64k=True),
					first_flags,
					b'\xE7A',
				),
				(
					make_mppc_vector(copies=((2, 4),), is_64k=True),
					next_flags,
					b'\xE7A\xE7A',
				),
			),
		)
		self.assertEqual(decoder.history_offset, 6)
		self.assertEqual(decoder.history_size, 65536)

	def test_rdp6_multi_packet_parity(self):
		compression_type = BulkCompressionType.RDP6
		first_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.FLUSHED,
		)
		next_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
		)
		decoder = self.assert_sequence_parity(
			compression_type,
			(
				(
					make_rdp6_vector(literals=b'ab', copies=((2, 4),)),
					first_flags,
					b'ababab',
				),
				(
					make_rdp6_vector(cached_copies=((0, 4),)),
					next_flags,
					b'abab',
				),
			),
		)
		self.assertEqual(decoder.history_offset, 10)
		self.assertEqual(decoder.history_size, 65536)
		self.assertEqual(decoder.offset_cache_len, 1)

	def test_rdp61_level2_chaining_and_match_parity(self):
		compression_type = BulkCompressionType.RDP61
		outer_flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
		)
		level2_first = make_mppc_vector(literals=b'chain me', is_64k=True)
		first = make_rdp61_inner_vector(
			level2_first,
			compression_flags(
				BulkCompressionType.RDP5_64K,
				BulkCompressionFlags.COMPRESSED,
				BulkCompressionFlags.AT_FRONT,
				BulkCompressionFlags.FLUSHED,
			),
			at_front=True,
		)
		level2_second = make_mppc_vector(copies=((8, 8),), is_64k=True)
		second = make_rdp61_inner_vector(
			level2_second,
			compression_flags(
				BulkCompressionType.RDP5_64K,
				BulkCompressionFlags.COMPRESSED,
			),
		)
		third = make_rdp61_match_vector(((8, 0, 0),), literals=b'!')
		decoder = self.assert_sequence_parity(
			compression_type,
			(
				(first, outer_flags, b'chain me'),
				(second, outer_flags, b'chain me'),
				(third, outer_flags, b'chain me!'),
			),
		)
		self.assertEqual(decoder.history_offset, 25)
		self.assertEqual(decoder.history_size, 2_000_000)
		self.assertEqual(decoder.level2_history_offset, 16)


class PublicApiTests(unittest.TestCase):
	def test_zero_flags_passthrough_does_not_select_codec(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		payload = bytearray(b'raw')
		self.assertEqual(
			decoder.decompress(
				payload,
				BulkCompressionFlags(0),
				expected_size=3,
			),
			b'raw',
		)
		self.assertIsNone(decoder.selected_type)
		self.assertEqual(decoder.packet_count, 1)
		self.assertEqual(decoder.compressed_packet_count, 0)
		self.assertEqual(decoder.compressed_byte_count, 0)
		self.assertEqual(decoder.decompressed_byte_count, 0)
		self.assertIsNone(decoder.history_offset)
		self.assertIsNone(decoder.history_size)

	def test_enum_properties_and_compressed_bytes_like_input(self):
		compression_type = BulkCompressionType.RDP5_64K
		decoder = BulkDecompressor(compression_type)
		self.assertIs(decoder.max_compression_type, compression_type)
		self.assertIsNone(decoder.selected_type)

		packet = make_mppc_vector(literals=b'ok', is_64k=True)
		flags = compression_flags(
			compression_type,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.AT_FRONT,
			BulkCompressionFlags.FLUSHED,
		)
		self.assertIsInstance(flags, BulkCompressionFlags)
		self.assertEqual(
			decoder.decompress(memoryview(packet), flags, expected_size=2),
			b'ok',
		)
		self.assertIs(decoder.selected_type, compression_type)
		self.assertEqual(decoder.history_offset, 2)
		self.assertEqual(decoder.history_size, 65536)
		self.assertIsNone(decoder.offset_cache_len)
		self.assertIsNone(decoder.level2_history_offset)

	def test_metrics_count_only_successful_compressed_packets(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		self.assertEqual(decoder.decompress(b'zero', 0), b'zero')
		self.assertEqual(
			decoder.decompress(b'typed', BulkCompressionType.RDP61),
			b'typed',
		)
		self.assertEqual(decoder.history_offset, 0)

		packet = make_rdp61_raw_vector(b'data')
		flags = compression_flags(
			BulkCompressionType.RDP61,
			BulkCompressionFlags.COMPRESSED,
		)
		self.assertEqual(
			decoder.decompress(memoryview(packet), flags, expected_size=4),
			b'data',
		)
		self.assertEqual(decoder.packet_count, 3)
		self.assertEqual(decoder.compressed_packet_count, 1)
		self.assertEqual(decoder.compressed_byte_count, len(packet))
		self.assertEqual(decoder.decompressed_byte_count, 4)
		self.assertEqual(decoder.history_offset, 4)


class TransactionalFailureTests(unittest.TestCase):
	def test_malformed_packets_preserve_public_state_for_every_codec(self):
		malformed_packets = {
			BulkCompressionType.RDP4_8K: b'\xFF',
			BulkCompressionType.RDP5_64K: b'\xFF',
			BulkCompressionType.RDP6: make_rdp6_vector(
				cached_copies=((3, 2),)
			),
			BulkCompressionType.RDP61: make_rdp61_match_vector(
				(
					(3, 2, 0),
					(3, 1, 0),
				),
				literals=b'ab',
			),
		}
		for compression_type, packet in malformed_packets.items():
			with self.subTest(compression_type=compression_type):
				decoder = make_seeded_decoder(compression_type)
				before = public_state(decoder)
				flags = compression_flags(
					compression_type,
					BulkCompressionFlags.COMPRESSED,
				)
				with self.assertRaises(BulkCompressionError):
					decoder.decompress(packet, flags)
				self.assertEqual(public_state(decoder), before)

	def test_compressed_expected_size_failures_preserve_all_public_state(self):
		continuations = {
			BulkCompressionType.RDP4_8K: make_mppc_vector(
				copies=((3, 3),)
			),
			BulkCompressionType.RDP5_64K: make_mppc_vector(
				copies=((2, 3),),
				is_64k=True,
			),
			BulkCompressionType.RDP6: make_rdp6_vector(
				cached_copies=((0, 2),)
			),
			BulkCompressionType.RDP61: make_rdp61_inner_vector(
				make_mppc_vector(copies=((5, 5),), is_64k=True),
				compression_flags(
					BulkCompressionType.RDP5_64K,
					BulkCompressionFlags.COMPRESSED,
				),
			),
		}
		for compression_type, packet in continuations.items():
			with self.subTest(compression_type=compression_type):
				decoder = make_seeded_decoder(compression_type)
				before = public_state(decoder)
				flags = compression_flags(
					compression_type,
					BulkCompressionFlags.COMPRESSED,
				)
				with self.assertRaisesRegex(
					BulkCompressionError,
					'does not match',
				):
					decoder.decompress(packet, flags, expected_size=99)
				self.assertEqual(public_state(decoder), before)

	def test_zero_flag_expected_size_failure_is_transactional(self):
		decoder = BulkDecompressor(BulkCompressionType.RDP61)
		before = public_state(decoder)
		with self.assertRaisesRegex(BulkCompressionError, 'does not match'):
			decoder.decompress(bytearray(b'raw'), 0, expected_size=4)
		self.assertEqual(public_state(decoder), before)

	def test_reserved_flags_preserve_public_state_for_every_codec(self):
		for compression_type in BulkCompressionType:
			with self.subTest(compression_type=compression_type):
				decoder = make_seeded_decoder(compression_type)
				before = public_state(decoder)
				with self.assertRaisesRegex(BulkCompressionError, 'Reserved'):
					decoder.decompress(
						b'',
						int(compression_type) | 0x10,
					)
				self.assertEqual(public_state(decoder), before)

	def test_type_transition_and_negotiation_failures_are_transactional(self):
		decoder = make_seeded_decoder(
			BulkCompressionType.RDP4_8K,
			max_compression_type=BulkCompressionType.RDP61,
		)
		before = public_state(decoder)
		with self.assertRaisesRegex(BulkCompressionError, 'changed'):
			decoder.decompress(b'raw', BulkCompressionType.RDP5_64K)
		self.assertEqual(public_state(decoder), before)

		capped = BulkDecompressor(BulkCompressionType.RDP4_8K)
		before = public_state(capped)
		with self.assertRaisesRegex(BulkCompressionError, 'above negotiated'):
			capped.decompress(
				b'',
				compression_flags(
					BulkCompressionType.RDP5_64K,
					BulkCompressionFlags.COMPRESSED,
				),
			)
		self.assertEqual(public_state(capped), before)

	def test_output_limit_failure_preserves_history_and_metrics(self):
		decoder = BulkDecompressor(
			BulkCompressionType.RDP4_8K,
			max_output_size=3,
		)
		first_flags = compression_flags(
			BulkCompressionType.RDP4_8K,
			BulkCompressionFlags.COMPRESSED,
			BulkCompressionFlags.AT_FRONT,
			BulkCompressionFlags.FLUSHED,
		)
		decoder.decompress(
			make_mppc_vector(literals=b'abc'),
			first_flags,
			expected_size=3,
		)
		before = public_state(decoder)
		with self.assertRaisesRegex(BulkCompressionError, 'limit'):
			decoder.decompress(
				make_mppc_vector(copies=((1, 4),)),
				compression_flags(
					BulkCompressionType.RDP4_8K,
					BulkCompressionFlags.COMPRESSED,
				),
			)
		self.assertEqual(public_state(decoder), before)


if __name__ == '__main__':
	unittest.main()
