import io
import enum

class TS_OFFSCREEN_CAPABILITYSET:
	def __init__(self):
		self.offscreenSupportLevel:bool = False
		self.offscreenCacheSize:int = 0
		self.offscreenCacheEntries:int = 0

	def to_bytes(self):
		t = int(self.offscreenSupportLevel).to_bytes(4, byteorder='little', signed = False)
		t += self.offscreenCacheSize.to_bytes(2, byteorder='little', signed = False)
		t += self.offscreenCacheEntries.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_OFFSCREEN_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_OFFSCREEN_CAPABILITYSET()
		msg.offscreenSupportLevel = bool(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.offscreenCacheSize = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.offscreenCacheEntries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_OFFSCREEN_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t