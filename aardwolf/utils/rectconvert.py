from ast import Import
import io
import rle
from PIL import Image
try:
	from PIL.ImageQt import ImageQt
except ImportError:
	print('No Qt installed! Converting to qt will not work')

from aardwolf.commons.queuedata.constants import VIDEO_FORMAT

bpp_2_bytes = {
	15: 2,
	16: 2,
	24: 3,
	32: 4,
}

def rectconvert(width, height, bitsPerPixel, isCompress, data, output_format = VIDEO_FORMAT.PIL):
	if bitsPerPixel not in bpp_2_bytes:
		raise ValueError("bitsPerPixel value of %s is not supported!" % bitsPerPixel)
	image = bytes(width * height * 4)
	rle.bitmap_decompress(image, width, height, data, bitsPerPixel, bpp_2_bytes[bitsPerPixel], int(isCompress))

	if output_format == VIDEO_FORMAT.RAW:
		return image
	
	image = Image.frombytes('RGBA', [width, height], image)

	if output_format == VIDEO_FORMAT.PIL:
		return image
	
	if output_format == VIDEO_FORMAT.QT5:
		image = ImageQt(image)
	
	elif output_format == VIDEO_FORMAT.PNG:
		img_byte_arr = io.BytesIO()
		image.save(img_byte_arr, format=output_format.upper())
		image = img_byte_arr.getvalue()
	else:
		raise ValueError('Output format of "%s" is not supported!' % output_format)
	return image