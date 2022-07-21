import io
import enum
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class TS_FONT_LIST_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.numberFonts:int = 0
		self.totalNumFonts:int = 0
		self.listFlags:int = 0x0003
		self.entrySize:int = 50

	def to_bytes(self):
		#t  = self.shareDataHeader.to_bytes()
		t = self.numberFonts.to_bytes(2, byteorder='little', signed = False)
		t += self.totalNumFonts.to_bytes(2, byteorder='little', signed = False)
		t += self.listFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.entrySize.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FONT_LIST_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FONT_LIST_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.numberFonts = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalNumFonts = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.listFlags = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.entrySize = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_FONT_LIST_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t