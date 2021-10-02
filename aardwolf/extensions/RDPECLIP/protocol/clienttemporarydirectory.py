
import io
import enum

class CLIPRDR_TEMP_DIRECTORY:
	def __init__(self):
		self.wszTempDir:str = None #always 520 bytes

	def to_bytes(self):
		t = self.wszTempDir.encode('utf-16-le').ljust(520,b'\x00')
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_TEMP_DIRECTORY.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_TEMP_DIRECTORY()
		msg.wszTempDir = buff.read(520).decode('utf-16-le').replace('\x00','')
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_TEMP_DIRECTORY ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t