
import io
import enum
from typing import List
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, ClusterInfo

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/d68c629f-36a1-4a40-afd0-8b3e56d29aac
class TS_UD_CS_CLUSTER:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_CLUSTER
		self.length:int = None
		self.Flags:ClusterInfo = None
		self.RedirectedSessionID: int = None
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.Flags.to_bytes(4, byteorder='little', signed = False)
		t += self.RedirectedSessionID.to_bytes(4, byteorder='little', signed = False)
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_CLUSTER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_CS_CLUSTER()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.Flags = ClusterInfo(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.RedirectedSessionID = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_CLUSTER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t