
import io
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, MultitransportFlags

#https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/f50e791c-de03-4b25-b17e-e914c9020bc3

class TS_UD_CS_MULTITRANSPORT:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_MULTITRANSPORT
		self.length:int = None
		self.flags:MultitransportFlags = 0 #not used?
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.flags.to_bytes(4, byteorder='little', signed = False)
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_MULTITRANSPORT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_CS_MULTITRANSPORT()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.flags = MultitransportFlags(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_MULTITRANSPORT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t