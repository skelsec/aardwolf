import io
import enum
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class TS_FONT_MAP_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.numberEntries:int = 0
		self.totalNumEntries:int = 0
		self.mapFlags:int = 0x0002
		self.entrySize:int = 4

	def to_bytes(self):
		#t  = self.shareDataHeader.to_bytes()
		t = self.numberEntries.to_bytes(2, byteorder='little', signed = False)
		t += self.totalNumEntries.to_bytes(2, byteorder='little', signed = False)
		t += self.mapFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.entrySize.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FONT_MAP_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FONT_MAP_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.numberEntries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalNumEntries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.mapFlags = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.entrySize = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_FONT_MAP_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t