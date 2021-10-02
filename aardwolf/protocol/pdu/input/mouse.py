import io
import enum

class PTRFLAGS(enum.IntFlag):
	HWHEEL = 0x0400 #The event is a horizontal mouse wheel rotation. The only valid flags in a horizontal wheel rotation event are PTRFLAGS_WHEEL_NEGATIVE and the WheelRotationMask; all other pointer flags are ignored. This flag MUST NOT be sent to a server that does not indicate support for horizontal mouse wheel events in the Input Capability Set (section 2.2.7.1.6).
	WHEEL = 0x0200 #The event is a vertical mouse wheel rotation. The only valid flags in a vertical wheel rotation event are PTRFLAGS_WHEEL_NEGATIVE and the WheelRotationMask; all other pointer flags are ignored.
	WHEEL_NEGATIVE = 0x0100 #The wheel rotation value (contained in the WheelRotationMask bit field) is negative and MUST be sign-extended before injection at the server.
	WheelRotationMask = 0x01FF #The bit field describing the number of rotation units the mouse wheel was rotated. The value is negative if the PTRFLAGS_WHEEL_NEGATIVE flag is set.
	MOVE = 0x0800 #    Indicates that the mouse position MUST be updated to the location specified by the xPos and yPos fields.
	DOWN = 0x8000 #    Indicates that a click event has occurred at the position specified by the xPos and yPos fields. The button flags indicate which button has been clicked and at least one of these flags MUST be set.
	BUTTON1 = 0x1000 #    Mouse button 1 (left button) was clicked or released. If the PTRFLAGS_DOWN flag is set, then the button was clicked, otherwise it was released.
	BUTTON2 = 0x2000 #    Mouse button 2 (right button) was clicked or released. If the PTRFLAGS_DOWN flag is set, then the button was clicked, otherwise it was released.
	BUTTON3 = 0x4000 #    Mouse button 3 (middle button or wheel) was clicked or released. If the PTRFLAGS_DOWN flag is set, then the button was clicked, otherwise it was released.

class TS_POINTER_EVENT:
	def __init__(self):
		self.pointerFlags:PTRFLAGS = None #only release flag is allowed here
		self.xPos:int = None #maybe string? #The Unicode character input code.
		self.yPos:int = None

	def to_bytes(self):
		t = self.pointerFlags.to_bytes(2, byteorder='little', signed=False)
		t += self.xPos.to_bytes(2, byteorder='little', signed=False)
		t += self.yPos.to_bytes(2, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_POINTER_EVENT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_POINTER_EVENT()
		msg.pointerFlags = PTRFLAGS(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		msg.xPos = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.yPos = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_POINTER_EVENT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

