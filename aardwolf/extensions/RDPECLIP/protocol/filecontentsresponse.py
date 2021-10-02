import io
import enum

class CLIPRDR_FILECONTENTS_RESPONSE:
	def __init__(self,is_size):
		self.is_size = is_size
		self.streamId:int = None
		self.requestedFileContentsData = None #this is either a 64bit integer (if filesize was requested) OR a blob of bytes with file contents


	def to_bytes(self):
		t = self.streamId.to_bytes(4, byteorder='little', signed = False)
		t += self.requestedFileContentsData
		return t

	@staticmethod
	def from_bytes(bbuff: bytes, is_size):
		return CLIPRDR_FILECONTENTS_RESPONSE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO, is_size):
		msg = CLIPRDR_FILECONTENTS_RESPONSE(is_size)
		msg.streamId = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_size is True:
			msg.requestedFileContentsData = int.from_bytes(buff.read(8), byteorder='little', signed = False)
		else:
			msg.requestedFileContentsData = buff.read()
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FILECONTENTS_RESPONSE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t
