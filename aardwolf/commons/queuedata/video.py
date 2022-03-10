import enum
import io
from aardwolf.protocol.fastpath.bitmap import TS_BITMAP_FLAG, TS_BITMAP_DATA

from aardwolf import logger
from aardwolf.commons.queuedata import RDPDATATYPE
from aardwolf.commons.queuedata.constants import VIDEO_FORMAT
from aardwolf.utils.rectconvert import rectconvert
try:
	from PIL.ImageQt import ImageQt
except ImportError:
	logger.debug('No Qt installed! Converting to qt will not work')

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
	def from_bitmapdata(bitmapdata:TS_BITMAP_DATA, output_format = VIDEO_FORMAT.QT5):
		res = RDP_VIDEO()
		res.type = RDPDATATYPE.VIDEO
		res.x = bitmapdata.destLeft
		res.y = bitmapdata.destTop
		res.width = bitmapdata.destRight - bitmapdata.destLeft + 1
		res.height = bitmapdata.destBottom - bitmapdata.destTop + 1
		res.bitsPerPixel = bitmapdata.bitsPerPixel
		res.is_compressed = TS_BITMAP_FLAG.BITMAP_COMPRESSION in bitmapdata.flags
		image_pil = rectconvert(res.width, res.height, res.bitsPerPixel, res.is_compressed, bitmapdata.bitmapDataStream)
		if output_format == VIDEO_FORMAT.PIL:
			image = image_pil

		elif output_format == VIDEO_FORMAT.RAW:
			image = image_pil.tobytes()

		elif output_format == VIDEO_FORMAT.QT5:
			image = ImageQt(image_pil)
		
		elif output_format == VIDEO_FORMAT.PNG:
			img_byte_arr = io.BytesIO()
			image_pil.save(img_byte_arr, format='PNG')
			image = img_byte_arr.getvalue()
		else:
			raise ValueError('Output format of "%s" is not supported!' % output_format)
		res.data = image
		
		return res, image_pil

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