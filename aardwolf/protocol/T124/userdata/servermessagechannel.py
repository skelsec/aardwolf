
import io
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/9269d58a-3d85-48a2-942a-bb0bbe5a55aa
class TS_UD_SC_MCS_MSGCHANNEL:
	def __init__(self):
		self.length:int = None
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_MCS_MSGCHANNEL
		self.MCSChannelID:int = None
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.MCSChannelID.to_bytes(2, byteorder='little', signed = False)
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_SC_MCS_MSGCHANNEL.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_SC_MCS_MSGCHANNEL()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.MCSChannelID = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_UD_SC_MCS_MSGCHANNEL ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t