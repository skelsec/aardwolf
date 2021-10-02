import io
import enum

class COMPDESK(enum.Enum):
	NOT_SUPPORTED = 0x0000 #Desktop composition services are not supported.
	SUPPORTED = 0x0001 #Desktop composition services are supported.

class TS_COMPDESK_CAPABILITYSET:
	def __init__(self):
		self.WndSupportLevel:COMPDESK = COMPDESK.NOT_SUPPORTED

	def to_bytes(self):
		t = self.WndSupportLevel.value.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_COMPDESK_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_COMPDESK_CAPABILITYSET()
		msg.WndSupportLevel = COMPDESK(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_COMPDESK_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t