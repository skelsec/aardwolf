import io
import enum
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class TS_SHUTDOWN_REQ_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None

	def to_bytes(self):
		return b''

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SHUTDOWN_REQ_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SHUTDOWN_REQ_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_SHUTDOWN_REQ_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t