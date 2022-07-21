
import io
from typing import List
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, MonitorConfig

class TS_MONITOR_DEF:
	def __init__(self):
		self.left:int = None
		self.top:int = None
		self.right:int = None
		self.bottom:int = None
		self.flags:MonitorConfig = None
		
	def to_bytes(self):
		t = self.left.to_bytes(4, byteorder='little', signed = True)
		t += self.top.to_bytes(4, byteorder='little', signed = True)
		t += self.right.to_bytes(4, byteorder='little', signed = True)
		t += self.bottom.to_bytes(4, byteorder='little', signed = True)
		t += self.flags.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_MONITOR_DEF.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_MONITOR_DEF()
		msg.left = int.from_bytes(buff.read(4), byteorder='little', signed = True)
		msg.top = int.from_bytes(buff.read(4), byteorder='little', signed = True)
		msg.right = int.from_bytes(buff.read(4), byteorder='little', signed = True)
		msg.bottom = int.from_bytes(buff.read(4), byteorder='little', signed = True)
		msg.flags = MonitorConfig(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_MONITOR_DEF ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/6b58e11e-a32b-4903-b736-339f3cfe46ec
class TS_UD_CS_MONITOR:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_MONITOR
		self.length:int = None
		self.monitorCount:int = None
		self.monitorDefArray:List[TS_MONITOR_DEF] = []
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = len(self.monitorDefArray).value.to_bytes(4, byteorder='little', signed = False)
		for cd in self.monitorDefArray:
			t += cd.to_bytes()
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_MONITOR.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_CS_MONITOR()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.channelCount = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		for _ in range(msg.channelCount):
			msg.monitorDefArray.append(TS_MONITOR_DEF.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_NET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t