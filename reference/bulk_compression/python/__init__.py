"""Connection-scoped server-to-client RDP bulk decompression.

Implementation provenance is limited to the normative wire descriptions in
[MS-RDPBCGR], [MS-RDPEGDI], and RFC 2118.  No third-party codec code is used.
"""

from .bitstream import BulkCompressionError
from .mppc import MppcDecoder
from .rdp6 import Rdp6Decoder
from .rdp61 import Rdp61Decoder
from .types import (
	BulkCompressionFlags,
	BulkCompressionType,
	VALID_FLAG_MASK,
)


class BulkDecompressor:
	"""Dispatch packets through one lazily-created, connection-owned codec."""

	def __init__(
		self,
		max_compression_type=BulkCompressionType.RDP61,
		max_output_size=None,
	):
		self.max_compression_type = BulkCompressionType(max_compression_type)
		if max_output_size is not None and max_output_size <= 0:
			raise ValueError('Maximum decompressed size must be positive')
		self.max_output_size = max_output_size
		self.selected_type = None
		self._decoder = None
		self.packet_count = 0
		self.compressed_packet_count = 0
		self.compressed_byte_count = 0
		self.decompressed_byte_count = 0

	def _create_decoder(self, compression_type):
		if compression_type == BulkCompressionType.RDP4_8K:
			return MppcDecoder(
				BulkCompressionType.RDP4_8K,
				self.max_output_size,
			)
		if compression_type == BulkCompressionType.RDP5_64K:
			return MppcDecoder(
				BulkCompressionType.RDP5_64K,
				self.max_output_size,
			)
		if compression_type == BulkCompressionType.RDP6:
			return Rdp6Decoder(self.max_output_size)
		if compression_type == BulkCompressionType.RDP61:
			return Rdp61Decoder(self.max_output_size)
		raise BulkCompressionError(
			'Unsupported RDP bulk-compression type %d' % compression_type
		)

	def _select_decoder(self, flags):
		flags = int(flags)
		if flags & ~int(VALID_FLAG_MASK):
			raise BulkCompressionError('Reserved bulk-compression flag is set')
		try:
			compression_type = BulkCompressionType(
				flags & int(BulkCompressionFlags.TYPE_MASK)
			)
		except ValueError as exc:
			raise BulkCompressionError(
				'Unsupported RDP bulk-compression type'
			) from exc
		if compression_type > self.max_compression_type:
			raise BulkCompressionError(
				'Server selected bulk-compression type %d above negotiated %d'
				% (compression_type, self.max_compression_type)
			)

		if self.selected_type is None:
			self.selected_type = compression_type
			self._decoder = self._create_decoder(compression_type)
		elif compression_type != self.selected_type:
			raise BulkCompressionError(
				'Server changed bulk-compression type from %d to %d'
				% (self.selected_type, compression_type)
			)
		return self._decoder

	def decompress(self, data, flags, expected_size=None):
		data = bytes(data)
		flags = int(flags)
		# A zero compressionFlags byte does not identify a codec and carries
		# no history transition.  Servers can include it on raw fast-path
		# fragments before sending the first compressed fragment.
		if flags == 0:
			if expected_size is not None and len(data) != expected_size:
				raise BulkCompressionError(
					'Uncompressed packet length does not match its declaration'
				)
			self.packet_count += 1
			return data

		decoder = self._select_decoder(flags)
		output = decoder.decompress(data, flags, expected_size)
		self.packet_count += 1
		if int(flags) & BulkCompressionFlags.COMPRESSED:
			self.compressed_packet_count += 1
			self.compressed_byte_count += len(data)
			self.decompressed_byte_count += len(output)
		return output


__all__ = [
	'BulkCompressionError',
	'BulkCompressionFlags',
	'BulkCompressionType',
	'BulkDecompressor',
]
