
import io
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, RNS_UD_SC

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/379a020e-9925-4b4f-98f3-7d634e10b411
class TS_UD_SC_CORE:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.SC_CORE
		self.length:int = None
		self.version:int = None
		self.clientRequestedProtocols:int = None
		self.earlyCapabilityFlags:RNS_UD_SC = None
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.version.to_bytes(4, byteorder='little', signed = False)
		t += self.clientRequestedProtocols.to_bytes(4, byteorder='little', signed = False)
		t += self.earlyCapabilityFlags.to_bytes(4, byteorder='little', signed = False)
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_SC_CORE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		def is_end(buff, start, size):
			return buff.tell() - start >= size
		start = buff.tell()
		msg = TS_UD_SC_CORE()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		if is_end(buff,start, msg.length):
			return msg
		msg.version = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_end(buff,start, msg.length):
			return msg
		msg.clientRequestedProtocols = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_end(buff,start, msg.length):
			return msg
		msg.earlyCapabilityFlags = RNS_UD_SC(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		if is_end(buff,start, msg.length):
			return msg
		return msg

	def __repr__(self):
		t = '==== TS_UD_SC_CORE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t