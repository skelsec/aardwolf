import io
import enum

class KBDFLAGS(enum.IntFlag):
	EXTENDED = 0x0100 #Indicates that the keystroke message contains an extended scancode. For enhanced 101-key and 102-key keyboards, extended keys include the right ALT and right CTRL keys on the main section of the keyboard; the INS, DEL, HOME, END, PAGE UP, PAGE DOWN and ARROW keys in the clusters to the left of the numeric keypad; and the Divide ("/") and ENTER keys in the numeric keypad.
	EXTENDED1 = 0x0200 #Used to send keyboard events triggered by the PAUSE key.A PAUSE key press and release MUST be sent as the following sequence of keyboard events:
		#CTRL (0x1D) DOWN
		#NUMLOCK (0x45) DOWN
		#CTRL (0x1D) UP
		#NUMLOCK (0x45) UP
		#The CTRL DOWN and CTRL UP events MUST both include the KBDFLAGS_EXTENDED1 flag.
	DOWN = 0x4000 #Indicates that the key was down prior to this event.
	RELEASE = 0x8000 #The absence of this flag indicates a key-down event, while its presence indicates a key-release event.

class TS_KEYBOARD_EVENT:
	def __init__(self):
		self.keyboardFlags:KBDFLAGS = None
		self.keyCode:int = None #The scancode of the key which triggered the event.
		self.pad2Octets:bytes = b'\x00\x00'

	def to_bytes(self):
		t = self.keyboardFlags.to_bytes(2, byteorder='little', signed=False)
		t += self.keyCode.to_bytes(2, byteorder='little', signed=False)
		t += self.pad2Octets
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_KEYBOARD_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_KEYBOARD_EVENT()
		msg.keyboardFlags = KBDFLAGS(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		msg.keyCode = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.pad2Octets = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_KEYBOARD_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t