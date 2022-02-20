import enum
from aardwolf.commons.queuedata import RDPDATATYPE

class RDP_BEEP:
	"""
	This object will be dispatched on the external queue 
	when the server sends a Beep or Bell notification
	"""
	def __init__(self):
		self.type = RDPDATATYPE.BEEP
	def __repr__(self):
		t = '==== RDP_BEEP ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t