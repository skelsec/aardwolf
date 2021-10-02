import io
import enum

class TS_MULTIFRAGMENTUPDATE_CAPABILITYSET:
	def __init__(self):
		self.MaxRequestSize:int = 0

	def to_bytes(self):
		t = self.MaxRequestSize.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_MULTIFRAGMENTUPDATE_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_MULTIFRAGMENTUPDATE_CAPABILITYSET()
		msg.MaxRequestSize = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_MULTIFRAGMENTUPDATE_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t