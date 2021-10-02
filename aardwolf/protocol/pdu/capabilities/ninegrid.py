import io
import enum

class DRAW_NINEGRID(enum.IntFlag):
	NO_SUPPORT = 0x00000000 #NineGrid bitmap caching and rendering is not supported.
	SUPPORTED = 0x00000001 #Revision 1 NineGrid bitmap caching and rendering is supported. The Revision 1 versions of the stream bitmap alternate secondary orders (see section 2.2.2.2.1.3.5) MUST be used to send the NineGrid bitmap from server to client.
	SUPPORTED_REV2 = 0x00000002 #Revision 2 NineGrid bitmap caching and rendering is supported. The Revision 2 versions of the stream bitmap alternate secondary orders (see section 2.2.2.2.1.3.5) MUST be used to send the NineGrid bitmap from server to client.

class TS_DRAW_NINEGRID_CAPABILITYSET:
	def __init__(self):
		self.drawNineGridSupportLevel:DRAW_NINEGRID = None
		self.drawNineGridCacheSize:int = None
		self.drawNineGridCacheEntries:int = None

	def to_bytes(self):
		t = self.drawNineGridSupportLevel.to_bytes(4, byteorder='little', signed = False)
		t += self.drawNineGridCacheSize.to_bytes(2, byteorder='little', signed = False)
		t += self.drawNineGridCacheEntries.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_DRAW_NINEGRID_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_DRAW_NINEGRID_CAPABILITYSET()
		msg.drawNineGridSupportLevel = DRAW_NINEGRID(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.drawNineGridCacheSize = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.drawNineGridCacheEntries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_DRAW_NINEGRID_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t