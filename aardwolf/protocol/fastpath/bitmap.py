import io
import enum
from typing import List

class TS_CD_HEADER:
	def __init__(self):
		self.cbCompFirstRowSize:int = None
		self.cbCompMainBodySize:int = None
		self.cbScanWidth:int = None
		self.cbUncompressedSize:int = None

	def to_bytes(self):
		t = self.cbCompFirstRowSize.to_bytes(2, byteorder='little', signed=False)
		t += self.cbCompMainBodySize.to_bytes(2, byteorder='little', signed=False)
		t += self.cbScanWidth.to_bytes(2, byteorder='little', signed=False)
		t += self.cbUncompressedSize.to_bytes(2, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_CD_HEADER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_CD_HEADER()
		msg.cbCompFirstRowSize = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.cbCompMainBodySize = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.cbScanWidth = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.cbUncompressedSize = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_CD_HEADER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_BITMAP_FLAG(enum.IntFlag):
	BITMAP_COMPRESSION = 0x0001 #Indicates that the bitmap data is compressed. The bitmapComprHdr field MUST be present if the NO_BITMAP_COMPRESSION_HDR (0x0400) flag is not set.
	NO_BITMAP_COMPRESSION_HDR = 0x0400 #Indicates that the bitmapComprHdr field is not present (removed for bandwidth efficiency to save 8 bytes).

class TS_BITMAP_DATA:
	def __init__(self):
		self.destLeft:int = None
		self.destTop:int = None
		self.destRight:int = None
		self.destBottom:int = None
		self.width:int = None
		self.height:int = None
		self.bitsPerPixel:int = None
		self.flagsInt:int = None
		self.flags:TS_BITMAP_FLAG = None
		self.bitmapLength:int = None
		self.bitmapComprHdr:TS_CD_HEADER = None
		self.bitmapDataStream:bytes = None


	def to_bytes(self):
		data = b''
		if TS_BITMAP_FLAG.BITMAP_COMPRESSION in self.flags and TS_BITMAP_FLAG.NO_BITMAP_COMPRESSION_HDR not in self.flags:
			data += self.bitmapComprHdr.to_bytes()
		data += self.bitmapDataStream

		t = self.destLeft.to_bytes(2, byteorder='little', signed=False)
		t += self.destTop.to_bytes(2, byteorder='little', signed=False)
		t += self.destRight.to_bytes(2, byteorder='little', signed=False)
		t += self.destBottom.to_bytes(2, byteorder='little', signed=False)
		t += self.width.to_bytes(2, byteorder='little', signed=False)
		t += self.height.to_bytes(2, byteorder='little', signed=False)
		t += self.bitsPerPixel.to_bytes(2, byteorder='little', signed=False)
		t += self.flags.to_bytes(2, byteorder='little', signed=False)
		t += len(data).to_bytes(2, byteorder='little', signed=False)
		t += data
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAP_DATA.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAP_DATA()
		msg.destLeft = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destTop = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destRight = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destBottom = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.width = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.height = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.bitsPerPixel = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.flagsInt = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.flags = TS_BITMAP_FLAG(msg.flagsInt)
		msg.bitmapLength = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		rl = msg.bitmapLength
		if TS_BITMAP_FLAG.NO_BITMAP_COMPRESSION_HDR not in msg.flags and TS_BITMAP_FLAG.BITMAP_COMPRESSION in msg.flags:
			msg.bitmapComprHdr = TS_CD_HEADER.from_buffer(buff)
			#rl -= 8
		msg.bitmapDataStream = buff.read(rl)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAP_DATA ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_UPDATE_BITMAP_DATA:
	def __init__(self):
		self.updateType:int = 0x0001
		self.numberRectangles:int = None
		self.rectangles:List[TS_BITMAP_DATA] = []

	def to_bytes(self):
		t = self.updateType.to_bytes(2, byteorder='little', signed=False)
		t += len(self.rectangles).to_bytes(2, byteorder='little', signed=False)
		for pal in self.rectangles:
			t += pal.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UPDATE_BITMAP_DATA.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UPDATE_BITMAP_DATA()
		msg.updateType = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.numberRectangles = int.from_bytes(buff.read(2), byteorder='little', signed=False)		
		for _ in range(msg.numberRectangles):
			msg.rectangles.append(TS_BITMAP_DATA.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== TS_UPDATE_PALETTE_DATA ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

