"""Pythonic facade for the native server-to-client bulk decompressor.

The production codec is implemented in Rust.  A complete specification-derived
Python reference remains available under ``reference/bulk_compression`` for
education and conformance work, but is never imported at runtime.
"""

from aardwolf._bulk import (
	BulkCompressionError,
	NativeBulkDecompressor,
)
from aardwolf.protocol.compression.types import (
	BulkCompressionFlags,
	BulkCompressionType,
)


class BulkDecompressor:
	"""Connection-scoped facade over the stateful native codec."""

	def __init__(
		self,
		max_compression_type=BulkCompressionType.RDP61,
		max_output_size=None,
	):
		self._native = NativeBulkDecompressor(
			int(max_compression_type),
			max_output_size,
		)

	def decompress(self, data, flags, expected_size=None):
		return self._native.decompress(data, int(flags), expected_size)

	@property
	def max_compression_type(self):
		return BulkCompressionType(self._native.max_compression_type)

	@property
	def selected_type(self):
		selected_type = self._native.selected_type
		if selected_type is None:
			return None
		return BulkCompressionType(selected_type)

	@property
	def packet_count(self):
		return self._native.packet_count

	@property
	def compressed_packet_count(self):
		return self._native.compressed_packet_count

	@property
	def compressed_byte_count(self):
		return self._native.compressed_byte_count

	@property
	def decompressed_byte_count(self):
		return self._native.decompressed_byte_count

	@property
	def history_offset(self):
		return self._native.history_offset

	@property
	def history_size(self):
		return self._native.history_size

	@property
	def offset_cache_len(self):
		return self._native.offset_cache_len

	@property
	def level2_history_offset(self):
		return self._native.level2_history_offset


__all__ = [
	'BulkCompressionError',
	'BulkCompressionFlags',
	'BulkCompressionType',
	'BulkDecompressor',
]
