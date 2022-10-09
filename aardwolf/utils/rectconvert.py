import librlers
from PIL import Image

bpp_2_bytes = {
	16: 2,
	24: 3,
	32: 4,
}

def rectconvert(width, height, bitsPerPixel, isCompress, data):
	if bitsPerPixel not in bpp_2_bytes:
		raise ValueError("bitsPerPixel value of %s is not supported!" % bitsPerPixel)
	image = librlers.bitmap_decompress(data, width, height, 16, int(isCompress))
	return Image.frombytes('RGBA', [width, height], bytes(image))