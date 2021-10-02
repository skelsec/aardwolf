import io
import enum

class FILECONTENTS_FLAG(enum.Enum):
	FILECONTENTS_SIZE = 0x00000001 #A request for the size of the file identified by the lindex field. The size MUST be returned as a 64-bit, unsigned integer. The cbRequested field MUST be set to 0x00000008 and both the nPositionLow and nPositionHigh fields MUST be set to 0x00000000.
	FILECONTENTS_RANGE = 0x00000002 #A request for the data present in the file identified by the lindex field. The data to be retrieved is extracted starting from the offset given by the nPositionLow and nPositionHigh fields. The maximum number of bytes to extract is specified by the cbRequested field.

class CLIPRDR_FILECONTENTS_REQUEST:
	def __init__(self):
		self.streamId:int = None
		self.lindex:int = None
		self.dwFlags:FILECONTENTS_FLAG = None
		self.nPositionLow:int = None
		self.nPositionHigh:int = None
		self.cbRequested:int = None
		self.clipDataId:int = None

		self.nPosition:int = None


	def to_bytes(self):
		if self.nPosition is not None:
			self.nPositionHigh = self.nPosition >> 32
			self.nPositionLow = self.nPosition & 0xFFFFFFFF

		t = self.streamId.to_bytes(4, byteorder='little', signed = False)
		t += self.lindex.to_bytes(4, byteorder='little', signed = False)
		t += self.dwFlags.value.to_bytes(4, byteorder='little', signed = False)
		t += self.nPositionLow.to_bytes(4, byteorder='little', signed = False)
		t += self.nPositionHigh.to_bytes(4, byteorder='little', signed = False)
		t += self.cbRequested.to_bytes(4, byteorder='little', signed = False)
		if self.clipDataId is not None:
			t += self.clipDataId.to_bytes(4, byteorder='little', signed = False)

		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_FILECONTENTS_REQUEST.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_FILECONTENTS_REQUEST()
		msg.streamId = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.lindex = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.dwFlags = FILECONTENTS_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.nPositionLow = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.nPositionHigh = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.cbRequested = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if buff.read(1) != b'':
			buff.seek(-1,1)
			msg.clipDataId = int.from_bytes(buff.read(4), byteorder='little', signed = False)

		msg.nPosition = msg.nPositionHigh << 32 | msg.nPositionLow
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FILECONTENTS_REQUEST ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t
