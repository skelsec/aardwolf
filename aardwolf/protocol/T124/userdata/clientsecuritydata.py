
import io
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, ENCRYPTION_FLAG

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/6b58e11e-a32b-4903-b736-339f3cfe46ec
class TS_UD_CS_SEC:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_SECURITY
		self.length:int = None
		self.encryptionMethods:ENCRYPTION_FLAG = None
		self.extEncryptionMethods:ENCRYPTION_FLAG = None
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.encryptionMethods.value.to_bytes(4, byteorder='little', signed = False)
		t += self.extEncryptionMethods.value.to_bytes(4, byteorder='little', signed = False)
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_SEC.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_CS_SEC()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.encryptionMethods = ENCRYPTION_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.extEncryptionMethods = ENCRYPTION_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_SEC ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t