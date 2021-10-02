import io
import enum

class TS_WINDOW_LEVEL(enum.Enum):
	NOT_SUPPORTED = 0x00000000 #The client or server is not capable of supporting Windowing Alternate Secondary Drawing Orders.
	SUPPORTED = 0x00000001 #The client or server is capable of supporting Windowing Alternate Secondary Drawing Orders.
	SUPPORTED_EX = 0x00000002 #The client or server is capable of supporting Windowing Alternate Secondary Drawing Orders 

class TS_WINDOW_LIST_CAP_SET:
	def __init__(self):
		self.WndSupportLevel:TS_WINDOW_LEVEL = TS_WINDOW_LEVEL.NOT_SUPPORTED
		self.NumIconCaches:int = None
		self.NumIconCacheEntries:int = None

	def to_bytes(self):
		t = self.WndSupportLevel.value.to_bytes(4, byteorder='little', signed = False)
		t += self.NumIconCaches.to_bytes(1, byteorder='little', signed = False)
		t += self.NumIconCacheEntries.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_WINDOW_LIST_CAP_SET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_WINDOW_LIST_CAP_SET()
		msg.WndSupportLevel = TS_WINDOW_LEVEL(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.NumIconCaches = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.NumIconCacheEntries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_WINDOW_LIST_CAP_SET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t