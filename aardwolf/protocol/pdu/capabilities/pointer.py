import io
import enum


class TS_POINTER_CAPABILITYSET:
	def __init__(self):
		self.colorPointerFlag:bool = False
		self.colorPointerCacheSize:int = 20
		self.pointerCacheSize:int = 20 #0 # ???

	def to_bytes(self):
		t = int(self.colorPointerFlag).to_bytes(2, byteorder='little', signed = False)
		t += self.colorPointerCacheSize.to_bytes(2, byteorder='little', signed = False)
		t += self.pointerCacheSize.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_POINTER_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_POINTER_CAPABILITYSET()
		msg.colorPointerFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.colorPointerCacheSize = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pointerCacheSize = int.from_bytes(buff.read(2), byteorder='little', signed = False)	
		return msg

	def __repr__(self):
		t = '==== TS_POINTER_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t