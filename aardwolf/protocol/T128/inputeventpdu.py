import io
import enum
from typing import List
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER
from aardwolf.protocol.pdu.input import TS_INPUT_EVENT


class TS_INPUT_PDU_DATA:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.numEvents:int = 0
		self.pad2Octets:int = 0
		self.slowPathInputEvents:List[TS_INPUT_EVENT] = []

	def to_bytes(self):
		#t  = self.shareDataHeader.to_bytes()
		data = b''
		for inputevt in self.slowPathInputEvents:
			data += inputevt.to_bytes()
		t = len(self.slowPathInputEvents).to_bytes(2, byteorder='little', signed = False)
		t += self.pad2Octets.to_bytes(2, byteorder='little', signed = False)
		t += data
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_INPUT_PDU_DATA.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_INPUT_PDU_DATA()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.numEvents = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pad2Octets = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		for _ in range(msg.numEvents):
			msg.slowPathInputEvents.append(TS_INPUT_EVENT.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== TS_INPUT_PDU_DATA ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t