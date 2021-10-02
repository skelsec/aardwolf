
import io
import enum

from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT

class CLIPRDR_FORMAT_DATA_REQUEST:
	def __init__(self):
		self.requestedFormatId:CLIPBRD_FORMAT = None

	def to_bytes(self):
		if isinstance(self.requestedFormatId, CLIPBRD_FORMAT):
			t = self.requestedFormatId.value.to_bytes(4, byteorder='little', signed=False)
		else:
			t = self.requestedFormatId.to_bytes(4, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_FORMAT_DATA_REQUEST.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_FORMAT_DATA_REQUEST()
		t = buff.read(4)
		try:
			msg.requestedFormatId = CLIPBRD_FORMAT(int.from_bytes(t, byteorder='little', signed=False))
		except:
			msg.requestedFormatId = int.from_bytes(t, byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FORMAT_DATA_REQUEST ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t