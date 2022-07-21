
import io
from typing import List
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, ORIENTATION

class TS_MONITOR_ATTRIBUTES:
	def __init__(self):
		self.physicalWidth:int = None
		self.physicalHeight:int = None
		self.orientation:ORIENTATION = None
		self.desktopScaleFactor:int = None
		self.deviceScaleFactor:int = None
		
	def to_bytes(self):
		t = self.physicalWidth.to_bytes(4, byteorder='little', signed = False)
		t += self.physicalHeight.to_bytes(4, byteorder='little', signed = False)
		t += self.orientation.value.to_bytes(4, byteorder='little', signed = False)
		t += self.desktopScaleFactor.to_bytes(4, byteorder='little', signed = False)
		t += self.deviceScaleFactor.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_MONITOR_ATTRIBUTES.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_MONITOR_ATTRIBUTES()
		msg.physicalWidth = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.physicalHeight = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.orientation = ORIENTATION(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.desktopScaleFactor = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.deviceScaleFactor = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_MONITOR_ATTRIBUTES ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/dfaf8842-c20c-4626-bd3b-8b7d0463bc0f
class TS_UD_CS_MONITOR_EX:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_MONITOR_EX
		self.length:int = None
		self.flags = 0 #not used
		self.monitorAttributeSize = None
		self.monitorCount:int = None
		self.monitorAttributesArray:List[TS_MONITOR_ATTRIBUTES] = []
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.flags.to_bytes(4, byteorder='little', signed = False)
		t += self.monitorAttributeSize.to_bytes(4, byteorder='little', signed = False)
		t += len(self.monitorCount).to_bytes(4, byteorder='little', signed = False)
		for cd in self.monitorAttributesArray:
			t += cd.to_bytes()
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_MONITOR_EX.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_CS_MONITOR_EX()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.flags = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.monitorAttributeSize = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.monitorCount = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		for _ in range(msg.monitorCount):
			msg.monitorAttributesArray.append(TS_MONITOR_ATTRIBUTES.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_MONITOR_EX ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t