
import io
from typing import List
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, ChannelOption

class CHANNEL_DEF:
	def __init__(self):
		self.name:str = None
		self.options:ChannelOption = None
		
	def to_bytes(self):
		name = self.name.encode('ascii')
		name = name.ljust(8,b'\x00')
		t = name
		t += self.options.to_bytes(4, byteorder='big', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CHANNEL_DEF.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CHANNEL_DEF()
		msg.name = buff.read(8).decode('ascii').replace('\x00','')
		msg.options = ChannelOption(int.from_bytes(buff.read(4), byteorder='big', signed = False))
		return msg

	def __repr__(self):
		t = '==== CHANNEL_DEF ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/6b58e11e-a32b-4903-b736-339f3cfe46ec
class TS_UD_CS_NET:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_NET
		self.length:int = None
		self.channelCount:int = None
		self.channelDefArray:List[CHANNEL_DEF] = []
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = len(self.channelDefArray).to_bytes(4, byteorder='little', signed = False)
		for cd in self.channelDefArray:
			t += cd.to_bytes()
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_NET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_CS_NET()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.channelCount = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		for _ in range(msg.channelCount):
			msg.channelDefArray.append(CHANNEL_DEF.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_NET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t