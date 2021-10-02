import io
import enum

class TS_UNUSED_EVENT:
	def __init__(self):
		self.pad4Octets:bytes = None
		self.pad2Octets:bytes = None

	def to_bytes(self):
		t = self.pad4Octets
		t += self.pad2Octets
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UNUSED_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UNUSED_EVENT()
		msg.pad4Octets = buff.read(4)
		msg.pad2Octets = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_UNUSED_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t