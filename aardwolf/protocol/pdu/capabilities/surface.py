import io
import enum

class SURFCMDS(enum.IntFlag):
	SETSURFACEBITS = 0x00000002 #The Set Surface Bits Command (section 2.2.9.2.1) is supported.
	FRAMEMARKER = 0x00000010 #The Frame Marker Command (section 2.2.9.2.3) is supported.
	STREAMSURFACEBITS = 0x00000040 #The Stream Surface Bits Command (section 2.2.9.2.2) is supported.

class TS_SURFCMDS_CAPABILITYSET:
	def __init__(self):
		self.cmdFlags:SURFCMDS = None
		self.reserved:bytes = b'\x00'*4

	def to_bytes(self):
		t = self.cmdFlags.to_bytes(4, byteorder='little', signed = False)
		t += self.reserved
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SURFCMDS_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SURFCMDS_CAPABILITYSET()
		msg.cmdFlags = SURFCMDS(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.reserved = buff.read(4)
		return msg

	def __repr__(self):
		t = '==== TS_SURFCMDS_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t