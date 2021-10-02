import io
import enum


class TS_WINDOWACTIVATION_CAPABILITYSET:
	def __init__(self):
		self.helpKeyFlag:bool = False
		self.helpKeyIndexFlag:bool = False
		self.helpExtendedKeyFlag:bool = False
		self.windowManagerKeyFlag:bool = False

	def to_bytes(self):
		t = int(self.helpKeyFlag).to_bytes(2, byteorder='little', signed = False)
		t += int(self.helpKeyIndexFlag).to_bytes(2, byteorder='little', signed = False)
		t += int(self.helpExtendedKeyFlag).to_bytes(2, byteorder='little', signed = False)
		t += int(self.windowManagerKeyFlag).to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_WINDOWACTIVATION_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_WINDOWACTIVATION_CAPABILITYSET()
		msg.helpKeyFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.helpKeyIndexFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.helpExtendedKeyFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.windowManagerKeyFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))	
		return msg

	def __repr__(self):
		t = '==== TS_WINDOWACTIVATION_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t