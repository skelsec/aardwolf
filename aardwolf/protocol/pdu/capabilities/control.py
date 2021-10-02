import io
import enum


class TS_CONTROL_CAPABILITYSET:
	def __init__(self):
		self.controlFlags:int = 0
		self.remoteDetachFlag:bool = False
		self.controlInterest:int = 2
		self.detachInterest:int = 2

	def to_bytes(self):
		t = self.controlFlags.to_bytes(2, byteorder='little', signed = False)
		t += int(self.remoteDetachFlag).to_bytes(2, byteorder='little', signed = False)
		t += self.controlInterest.to_bytes(2, byteorder='little', signed = False)
		t += self.detachInterest.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_CONTROL_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_CONTROL_CAPABILITYSET()
		msg.controlFlags = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.remoteDetachFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.controlInterest = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.detachInterest = int.from_bytes(buff.read(2), byteorder='little', signed = False)	
		return msg

	def __repr__(self):
		t = '==== TS_CONTROL_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t