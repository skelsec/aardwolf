import enum
from aardwolf.commons.queuedata import RDPDATATYPE

class RDP_MOUSE:
	def __init__(self):
		self.type = RDPDATATYPE.MOUSE
		self.xPos:int = None
		self.yPos:int = True
		self.button:int = None
		self.pressed:bool = None

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