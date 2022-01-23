import io
import enum
from aardwolf.protocol.pdu.input.keyboard import KBDFLAGS

class TS_UNICODE_KEYBOARD_EVENT:
	def __init__(self):
		self.keyboardFlags:KBDFLAGS = None #only release flag is allowed here
		self.unicodeCode:int = None #maybe string? #The Unicode character input code.
		self.pad2Octets:bytes = b'\x00\x00'

	def to_bytes(self):
		t = self.keyboardFlags.to_bytes(2, byteorder='little', signed=False)
		t += self.unicodeCode[0].encode('utf-16-le')
		t += self.pad2Octets
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UNICODE_KEYBOARD_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UNICODE_KEYBOARD_EVENT()
		msg.keyboardFlags = KBDFLAGS(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		msg.unicodeCode = buff.read(2).decode('utf-16-le')
		msg.pad2Octets = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_UNICODE_KEYBOARD_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t