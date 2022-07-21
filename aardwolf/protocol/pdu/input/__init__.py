import io
import enum

from aardwolf import logger
from aardwolf.protocol.pdu.input.keyboard import TS_KEYBOARD_EVENT
from aardwolf.protocol.pdu.input.unicode import TS_UNICODE_KEYBOARD_EVENT
from aardwolf.protocol.pdu.input.mouse import TS_POINTER_EVENT
from aardwolf.protocol.pdu.input.mousex import TS_POINTERX_EVENT
from aardwolf.protocol.pdu.input.sync import TS_SYNC_EVENT
from aardwolf.protocol.pdu.input.unused import TS_UNUSED_EVENT


class INPUT_EVENT(enum.Enum):
	SYNC = 0x0000 #Indicates a Synchronize Event (section 2.2.8.1.1.3.1.1.5).
	UNUSED = 0x0002 #Indicates an Unused Event (section 2.2.8.1.1.3.1.1.6).
	SCANCODE = 0x0004 #Indicates a Keyboard Event (section 2.2.8.1.1.3.1.1.1).
	UNICODE = 0x0005 #Indicates a Unicode Keyboard Event (section 2.2.8.1.1.3.1.1.2).
	MOUSE = 0x8001 #Indicates a Mouse Event (section 2.2.8.1.1.3.1.1.3).
	MOUSEX = 0x8002 #Indicates an Extended Mouse Event (section 2.2.8.1.1.3.1.1.4).

class TS_INPUT_EVENT:
	def __init__(self):
		self.eventTime: bytes = b'\x00'*4 #would have created a datetime obj but it is in fact ignroed by the server
		self.messageType:INPUT_EVENT = None
		self.slowPathInputData:bytes = None #always 6 bytes long

		# high level
		self.input = None
	
	@staticmethod
	def from_input(cap):
		t = TS_INPUT_EVENT()
		t.messageType = obj2otype[type(cap)]
		t.input = cap
		return t

	def to_bytes(self):
		t = self.eventTime
		t += self.messageType.value.to_bytes(2, byteorder='little', signed = False)
		t += self.input.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_INPUT_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_INPUT_EVENT()
		msg.eventTime = buff.read(4)
		msg.messageType = INPUT_EVENT(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.slowPathInputData = buff.read(6)
		
		ot = otype2obj[msg.messageType]
		if ot is not None:
			msg.input = ot.from_bytes(msg.slowPathInputData)
		else:
			logger.debug('Not implemented parser! %s' % msg.capabilitySetType)
		return msg

	def __repr__(self):
		t = '==== TS_INPUT_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

otype2obj = {
	INPUT_EVENT.SYNC : TS_SYNC_EVENT,
	INPUT_EVENT.UNUSED : TS_UNUSED_EVENT,
	INPUT_EVENT.SCANCODE : TS_KEYBOARD_EVENT,
	INPUT_EVENT.UNICODE : TS_UNICODE_KEYBOARD_EVENT,
	INPUT_EVENT.MOUSE : TS_POINTER_EVENT,
	INPUT_EVENT.MOUSEX : TS_POINTERX_EVENT,

}

obj2otype = {v: k for k, v in otype2obj.items()}