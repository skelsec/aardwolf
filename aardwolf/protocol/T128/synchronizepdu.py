import io
import enum
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class TS_SYNCHRONIZE_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.messageType:int = 1
		self.targetUser:int = None #MCS channel ID

	def to_bytes(self):
		t = self.messageType.to_bytes(2, byteorder='little', signed = False)
		t += self.targetUser.to_bytes(2, byteorder='little', signed = False)
		#self.shareDataHeader.shareControlHeader.totalLength = 6 + len(t)
		#t = self.shareControlHeader.to_bytes() + t
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SYNCHRONIZE_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SYNCHRONIZE_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.messageType = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.targetUser = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_SYNCHRONIZE_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t