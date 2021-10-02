import io
import enum

class TS_SYNC(enum.IntFlag):
	SCROLL_LOCK = 0x00000001 #Indicates that the Scroll Lock indicator light SHOULD be on.
	NUM_LOCK = 0x00000002 #Indicates that the Num Lock indicator light SHOULD be on.
	CAPS_LOCK = 0x00000004 #Indicates that the Caps Lock indicator light SHOULD be on.
	KANA_LOCK = 0x00000008 #Indicates that the Kana Lock indicator light SHOULD be on.

class TS_SYNC_EVENT:
	def __init__(self):
		self.pad2Octets:bytes = None
		self.toggleFlags:TS_SYNC = None 

	def to_bytes(self):
		t = self.pad2Octets
		t += self.toggleFlags.to_bytes(2, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SYNC_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SYNC_EVENT()
		msg.pad2Octets = buff.read(2)
		msg.toggleFlags = TS_SYNC(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		return msg

	def __repr__(self):
		t = '==== TS_SYNC_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t