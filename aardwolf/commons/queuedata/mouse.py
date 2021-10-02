import enum
from aardwolf.commons.queuedata import RDPDATATYPE

class RDP_MOUSE:
	def __init__(self):
		self.type = RDPDATATYPE.MOUSE
		self.xPos:int = None
		self.yPos:int = True
		self.button:int = None
		self.pressed:bool = None
