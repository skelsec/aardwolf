
import io
from aardwolf.protocol.T124.userdata.constants import *

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/379a020e-9925-4b4f-98f3-7d634e10b411
class TS_UD_SC_SEC1:
	def __init__(self):
		self.length:int = None
		self.type:TS_UD_TYPE = TS_UD_TYPE.SC_SECURITY
		self.encryptionMethod:ENCRYPTION_FLAG = None
		self.encryptionLevel:ENCRYPTION_LEVEL = None
		self.serverRandomLen:int = None
		self.serverCertLen:int = None
		self.serverRandom:bytes = None
		self.serverCertificate:bytes = None
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.encryptionMethod.value.to_bytes(4, byteorder='little', signed = False)
		t += self.encryptionLevel.value.to_bytes(4, byteorder='little', signed = False)
		t += len(self.serverRandom).to_bytes(4, byteorder='little', signed = False)
		t += len(self.serverCertificate).to_bytes(4, byteorder='little', signed = False)
		t += self.serverRandom
		t += self.serverCertificate
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_SC_SEC1.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_SC_SEC1()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.encryptionMethod = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.encryptionLevel = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.serverRandomLen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.serverCertLen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.serverRandom = buff.read(msg.serverRandomLen)
		msg.serverCertificate = buff.read(msg.serverCertLen)
		return msg

	def __repr__(self):
		t = '==== TS_UD_SC_SEC1 ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t