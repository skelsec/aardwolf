import io
import enum

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/17e80f50-d163-49de-a23b-fd6456aa472f
# TODO
class TS_BITMAPCODECS_CAPABILITYSET:
	def __init__(self):
		self.supportedBitmapCodecs:bytes = None

	def to_bytes(self):
		t = self.supportedBitmapCodecs
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCODECS_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCODECS_CAPABILITYSET()
		msg.supportedBitmapCodecs = buff.read()
		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCODECS_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t