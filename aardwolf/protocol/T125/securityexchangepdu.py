
import enum
import io

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/ca73831d-3661-4700-9357-8f247640c02e1
class TS_SECURITY_PACKET:
	def __init__(self):
		self.length = None
		self.encryptedClientRandom:bytes = None

	def to_bytes(self):
		t = (len(self.encryptedClientRandom)).to_bytes(4, byteorder='little', signed=False)
		t += self.encryptedClientRandom
		return t
		#return self.encryptedClientRandom

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SECURITY_PACKET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SECURITY_PACKET()
		msg.encryptedClientRandom = buff.read()
		return msg

	def __repr__(self):
		t = '==== TS_SECURITY_PACKET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t