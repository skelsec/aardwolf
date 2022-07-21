from ast import Import
import io
import rle
from PIL import Image
try:
	from PIL.ImageQt import ImageQt
except ImportError:
	print('No Qt installed! Converting to qt will not work')
	
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

#def RDPBitmapToPIL(width, height, bitsPerPixel, isCompress, data):
def rectconvert(width, height, bitsPerPixel, isCompress, data, output_format = 'qt'):
	image = None
	#allocate
	raw_data = data
	if bitsPerPixel == 15:
		if isCompress:
			buf = bytes(width * height * 2)
			rle.bitmap_decompress(buf, width, height, data, 2)
			data = buf
		
		# converting RGB555 to RGB888 (24 bit) for PIL-compatilbility
		image = b''
		for c in chunker(data, 2):
			x = int.from_bytes(c, byteorder='little', signed=False)
			r = x >> 11
			g = (x >> 5) & 0b11111
			b = x & 0x1F
			r = min(r*8,255)
			g = min(g*8,255)
			b = min(b*8,255)
			image += bytes([r,g,b, 255])
		
		if output_format != 'raw':
			image = Image.frombytes('RGBA', [width, height], image)
	
	elif bitsPerPixel == 16:
		if isCompress:
			buf = bytes(width * height * 2)
			rle.bitmap_decompress(buf, width, height, data, 2)
			data = buf
		# converting RGB565 to RGB32 (32 bit, RGB888+alpha) for PIL-compatilbility
		image = b''
		for c in chunker(data, 2):
			x = int.from_bytes(c, byteorder='little', signed=False)
			r = x >> 11
			g = (x >> 5) & 0b111111
			b = x & 0x1F
			r = min(r*8,255)
			g = min(g*4,255)
			b = min(b*8,255)
			image += bytes([r,g,b, 255])
		
		if output_format != 'raw':
			image = Image.frombytes('RGBA', [width, height], image)
	
	elif bitsPerPixel == 24:
		if isCompress:
			buf = bytes(width * height * 3)
			rle.bitmap_decompress(buf, width, height, data, 3)
			data = buf
		
		image = b''
		# adding the alpha channel
		for i, c in enumerate(data):
			image += bytes([c])
			if i %3 == 0:
				image += b'\xFF'
		
		if output_format != 'raw':
			image = Image.frombytes('RGBA', [width, height], data)
			
	elif bitsPerPixel == 32:
		if isCompress:
			buf = bytes(width * height * 4)
			rle.bitmap_decompress(buf, width, height, data, 4)
			data = buf
		
		image = data
		if output_format != 'raw':
			image = Image.frombytes('RGBA', [width, height], image)
	else:
		raise ValueError("bitsPerPixel value of %s is not supported!" % bitsPerPixel)
	
	if output_format == 'pil' or output_format == 'pillow' or output_format == 'raw':
		return image
	
	if output_format == 'qt':
		image = ImageQt(image)
	
	elif output_format == 'png':
		img_byte_arr = io.BytesIO()
		image.save(img_byte_arr, format=output_format.upper())
		image = img_byte_arr.getvalue()
	else:
		raise ValueError('Output format of "%s" is not supported!' % output_format)
	return image