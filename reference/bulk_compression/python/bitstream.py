"""Bounded bit-stream primitives used by the RDP bulk decompressors."""


class BulkCompressionError(ValueError):
	"""Raised when a bulk-compressed stream violates the wire format."""


class BitReader:
	"""Read a byte string in either documented bulk-codec bit order."""

	def __init__(self, data, least_significant_bit_first=False):
		self._data = memoryview(data)
		self._bit_position = 0
		self._least_significant_bit_first = least_significant_bit_first

	@property
	def bit_position(self):
		return self._bit_position

	@property
	def remaining_bits(self):
		return len(self._data) * 8 - self._bit_position

	def read_bits(self, count):
		if count < 0:
			raise ValueError('Bit count cannot be negative')
		if count > self.remaining_bits:
			raise BulkCompressionError(
				'Truncated bulk-compression bit stream '
				'(wanted %d bits, only %d remain)' % (count, self.remaining_bits)
			)

		value = 0
		for value_bit in range(count):
			byte_index, bit_index = divmod(self._bit_position, 8)
			if self._least_significant_bit_first:
				shift = bit_index
			else:
				shift = 7 - bit_index
			bit = (self._data[byte_index] >> shift) & 1
			if self._least_significant_bit_first:
				value |= bit << value_bit
			else:
				value = (value << 1) | bit
			self._bit_position += 1
		return value

	def padding_is_zero(self):
		position = self._bit_position
		try:
			while self.remaining_bits:
				if self.read_bits(1):
					return False
			return True
		finally:
			self._bit_position = position


class HuffmanDecoder:
	"""A small validating decoder for a fixed, specification-defined codebook."""

	def __init__(self, codes, lengths, least_significant_bit_first=False):
		if len(codes) != len(lengths):
			raise ValueError('Huffman code and length tables differ in size')

		self._codes = {}
		self._max_length = 0
		for symbol, (code, length) in enumerate(zip(codes, lengths)):
			if length <= 0:
				raise ValueError('Huffman code lengths must be positive')
			if code >= (1 << length):
				raise ValueError('Huffman code does not fit its declared length')
			if least_significant_bit_first:
				reversed_code = 0
				for index in range(length):
					reversed_code = (
						(reversed_code << 1) | ((code >> index) & 1)
					)
				code = reversed_code
			key = (length, code)
			if key in self._codes:
				raise ValueError('Duplicate Huffman code')
			self._codes[key] = symbol
			self._max_length = max(self._max_length, length)

	def decode(self, reader):
		code = 0
		for length in range(1, self._max_length + 1):
			code = (code << 1) | reader.read_bits(1)
			symbol = self._codes.get((length, code))
			if symbol is not None:
				return symbol
		raise BulkCompressionError('Invalid bulk-compression Huffman code')
