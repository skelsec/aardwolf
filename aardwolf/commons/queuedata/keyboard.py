import enum
from aardwolf.commons.queuedata import RDPDATATYPE

class RDP_KEYBOARD_SCANCODE:
	def __init__(self):
		self.type = RDPDATATYPE.KEYSCAN
		self.keyCode:int = None
		self.is_pressed:bool = True
		self.is_extended:bool = False

class RDP_KEYBOARD_UNICODE:
	def __init__(self):
		self.type = RDPDATATYPE.KEYUNICODE
		self.char:str = None
		self.is_pressed:bool = None