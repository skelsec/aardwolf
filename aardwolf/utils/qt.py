from aardwolf.protocol.fastpath import TS_FP_UPDATE_PDU
import rle                                                                 
from PyQt5.QtGui import QImage, QTransform

def RDPBitmapToQtImage(width, height, bitsPerPixel, isCompress, data):
	"""
	@summary: Bitmap transformation to Qt object
	@param width: width of bitmap
	@param height: height of bitmap
	@param bitsPerPixel: number of bit per pixel
	@param isCompress: use RLE compression
	@param data: bitmap data
	"""
	image = None
	#allocate
	
	if bitsPerPixel == 15:
		if isCompress:
			buf = bytes(width * height * 2)
			rle.bitmap_decompress(buf, width, height, data, 2)
			image = QImage(buf, width, height, QImage.Format_RGB555)
		else:
			image = QImage(data, width, height, QImage.Format_RGB555).transformed(QTransform(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
	
	elif bitsPerPixel == 16:
		if isCompress:
			buf = bytes(width * height * 2)
			rle.bitmap_decompress(buf, width, height, data, 2)
			image = QImage(buf, width, height, QImage.Format_RGB16)
		else:
			image = QImage(data, width, height, QImage.Format_RGB16).transformed(QTransform(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
	
	elif bitsPerPixel == 24:
		if isCompress:
			buf = bytes(width * height * 3)
			rle.bitmap_decompress(buf, width, height, data, 3)
			image = QImage(buf, width, height, QImage.Format_RGB888)
		else:
			image = QImage(data, width, height, QImage.Format_RGB888).transformed(QTransform(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
			
	elif bitsPerPixel == 32:
		if isCompress:
			buf = bytes(width * height * 4)
			rle.bitmap_decompress(buf, width, height, data, 4)
			image = QImage(buf, width, height, QImage.Format_RGB32)
		else:
			image = QImage(data, width, height, QImage.Format_RGB32).transformed(QTransform(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
	else:
		print("Receive image in bad format")
		image = QImage(width, height, QImage.Format_RGB32)
	return image