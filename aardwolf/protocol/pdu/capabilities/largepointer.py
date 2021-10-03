import io
import enum

class LARGE_POINTER(enum.Enum):
	FLAG_96x96 = 0x00000001 #Mouse pointer shapes of up to 96x96 pixels in size are supported.
	FLAG_384x384 = 0x00000002 #Mouse pointer shapes of up to 384x384 pixels in size, and the Fast-Path Large Pointer Update (section 2.2.9.1.2.1.11), are supported.
	FLAG_3_UNK = 0x00000003

class TS_LARGE_POINTER_CAPABILITYSET:
	def __init__(self):
		self.largePointerSupportFlags:LARGE_POINTER = None

	def to_bytes(self):
		t = self.largePointerSupportFlags.value.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_LARGE_POINTER_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_LARGE_POINTER_CAPABILITYSET()
		msg.largePointerSupportFlags = LARGE_POINTER(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_LARGE_POINTER_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t