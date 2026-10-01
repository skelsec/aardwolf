"""Compatibility facade for aardwolf's private native RLE extension."""

from aardwolf._rle import bitmap_decompress, decode_rre, mask_rgbx

__all__ = [
	'bitmap_decompress',
	'decode_rre',
	'mask_rgbx',
]
