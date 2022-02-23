from ast import Import
import io
import rle
from PIL import Image

from aardwolf.commons.queuedata.constants import VIDEO_FORMAT

bpp_2_bytes = {
	15: 2,
	16: 2,
	24: 3,
	32: 4,
}

def rectconvert(width, height, bitsPerPixel, isCompress, data):
	if bitsPerPixel not in bpp_2_bytes:
		raise ValueError("bitsPerPixel value of %s is not supported!" % bitsPerPixel)
	image = bytes(width * height * 4)
	rle.bitmap_decompress(image, width, height, data, bitsPerPixel, bpp_2_bytes[bitsPerPixel], int(isCompress))
	return Image.frombytes('RGBA', [width, height], image)