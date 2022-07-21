import io
import enum
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class CTRLACTION(enum.Enum):
	REQUEST_CONTROL = 0x0001 #Request control
	GRANTED_CONTROL = 0x0002 #Granted control
	DETACH = 0x0003 #Detach
	COOPERATE = 0x0004 #Cooperate

class TS_CONTROL_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.action:CTRLACTION = None
		self.grantId:int = 0
		self.controlId:int = 0

	def to_bytes(self):
		#t  = self.shareDataHeader.to_bytes()
		t = self.action.value.to_bytes(2, byteorder='little', signed = False)
		t += self.grantId.to_bytes(2, byteorder='little', signed = False)
		t += self.controlId.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_CONTROL_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_CONTROL_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.action = CTRLACTION(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.grantId = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.controlId = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_CONTROL_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t