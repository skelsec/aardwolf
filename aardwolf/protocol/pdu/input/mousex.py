import io
import enum

class PTRXFLAGS(enum.IntFlag):
	DOWN = 0x8000 #Indicates that a click event has occurred at the position specified by the xPos and yPos fields. The button flags indicate which button has been clicked and at least one of these flags MUST be set.
	BUTTON1 = 0x0001 #Extended mouse button 1 (also referred to as button 4) was clicked or released. If the PTRXFLAGS_DOWN flag is set, the button was clicked; otherwise, it was released.
	BUTTON2 = 0x0002 #Extended mouse button 2 (also referred to as button 5) was clicked or released. If the PTRXFLAGS_DOWN flag is set, the button was clicked; otherwise, it was released.

class TS_POINTERX_EVENT:
	def __init__(self):
		self.pointerFlags:PTRXFLAGS = None #only release flag is allowed here
		self.xPos:int = None #maybe string? #The Unicode character input code.
		self.yPos:int = None

	def to_bytes(self):
		t = self.pointerFlags.to_bytes(2, byteorder='little', signed=False)
		t += self.xPos.to_bytes(2, byteorder='little', signed=False)
		t += self.yPos.to_bytes(2, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_POINTERX_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_POINTERX_EVENT()
		msg.pointerFlags = PTRXFLAGS(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		msg.xPos = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.yPos = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_POINTERX_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t