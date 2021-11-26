import enum
from aardwolf.protocol.fastpath.bitmap import TS_BITMAP_FLAG, TS_BITMAP_DATA

from aardwolf.commons.queuedata import RDPDATATYPE


class RDP_VIDEO:
	def __init__(self):
		self.type = RDPDATATYPE.VIDEO
		self.x:int = None
		self.y:int = None
		self.width:int = None
		self.height:int = None
		self.bitsPerPixel:int = None
		self.is_compressed = None
		self.data:bytes = None
	
	@staticmethod
	def from_bitmapdata(bitmapdata:TS_BITMAP_DATA): #TS_BITMAP_DATA
		res = RDP_VIDEO()
		res.type = RDPDATATYPE.VIDEO
		res.x = bitmapdata.destLeft
		res.y = bitmapdata.destTop
		res.width = bitmapdata.destRight - bitmapdata.destLeft + 1
		res.height = bitmapdata.destBottom - bitmapdata.destTop + 1
		res.bitsPerPixel = bitmapdata.bitsPerPixel
		res.is_compressed = TS_BITMAP_FLAG.BITMAP_COMPRESSION in bitmapdata.flags
		res.data = bitmapdata.bitmapDataStream
		return res

	def __repr__(self):
		t = '==== RDP_VIDEO ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t