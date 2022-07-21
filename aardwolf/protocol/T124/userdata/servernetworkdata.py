
import io
import enum
from typing import List
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/89fa11de-5275-4106-9cf1-e5aa7709436c
class TS_UD_SC_NET:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.SC_NET
		self.length:int = None
		self.MCSChannelId:int = None
		self.channelCount:int = None
		self.channelIdArray:List[int] = []
		self.Pad = None #optional
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.MCSChannelId.to_bytes(4, byteorder='little', signed = False)
		t += len(self.channelIdArray).to_bytes(2, byteorder='little', signed = False)
		for cd in self.channelIdArray:
			t += cd.to_bytes(2, byteorder='little', signed = False)
		if len(self.channelIdArray) % 2 != 0:
			t+= b'\x00\x00' # padding to multiple of 4
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_SC_NET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_SC_NET()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.MCSChannelId = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.channelCount = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		for _ in range(msg.channelCount):
			msg.channelIdArray.append(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		if msg.channelCount % 2 != 0:
			msg.Pad = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_UD_SC_NET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t