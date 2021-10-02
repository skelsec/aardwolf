import io
import enum

class SOUND_FLAG(enum.Enum):
	NONE = 0x0000
	BEEPS = 0x0001 #Playing a beep sound is supported.

class TS_SOUND_CAPABILITYSET:
	def __init__(self):
		self.soundFlags:SOUND_FLAG = SOUND_FLAG.NONE
		self.pad2octets:bytes = b'\x00'*2

	def to_bytes(self):
		t = self.soundFlags.value.to_bytes(2, byteorder='little', signed = False)
		t += self.pad2octets
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SOUND_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SOUND_CAPABILITYSET()
		msg.soundFlags = SOUND_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.pad2octets = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_SOUND_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t