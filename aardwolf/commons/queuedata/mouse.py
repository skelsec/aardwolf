import enum
from aardwolf.commons.queuedata import RDPDATATYPE
from aardwolf.commons.queuedata.constants import MOUSEBUTTON


class RDP_MOUSE:
	"""
	Mouse movement or button press event.
	xPos: mouse position X coordinate
	yPos: mouse position Y coordinate
	button: mouse button pressed/released. If only hovering use MOUSEBUTTON_LEFT and no press
	is_pressed: indicates wether the button has been pressed or released
	"""
	def __init__(self):
		self.type = RDPDATATYPE.MOUSE
		self.xPos:int = None
		self.yPos:int = True
		self.button:MOUSEBUTTON = None
		self.is_pressed:bool = None

	def __repr__(self):
		t = '==== RDP_MOUSE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t