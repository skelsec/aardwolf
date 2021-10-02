
import io
import enum

class CLIPRDR_UNLOCK_CLIPDATA:
	def __init__(self):
		self.clipDataId:int = None

	def to_bytes(self):
		t = self.clipDataId.to_bytes(4, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_UNLOCK_CLIPDATA.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_UNLOCK_CLIPDATA()
		msg.clipDataId = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_UNLOCK_CLIPDATA ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t