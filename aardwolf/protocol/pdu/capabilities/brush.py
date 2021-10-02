import io
import enum

class BRUSH_FLAG(enum.Enum):
	DEFAULT = 0x00000000 #Support for solid-color and monochrome pattern brushes with no caching. This is an RDP 4.0 implementation.
	COLOR_8x8 = 0x00000001 #Ability to handle color brushes (4-bit or 8-bit in RDP 5.0; 4-bit, 8-bit, 16-bit, or 24-bit in all other RDP versions, except for RDP 4.0) and caching. Brushes are limited to 8-by-8 pixels.
	COLOR_FULL = 0x00000002 #Ability to handle color brushes (4-bit or 8-bit in RDP 5.0; 4-bit, 8-bit, 16-bit, or 24-bit in all other RDP versions, except for RDP 4.0) and caching. Brushes can have arbitrary dimensions.

class TS_BRUSH_CAPABILITYSET:
	def __init__(self):
		self.brushSupportLevel:BRUSH_FLAG = BRUSH_FLAG.DEFAULT #FONTSUPPORT_FONTLIST

	def to_bytes(self):
		t = self.brushSupportLevel.value.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BRUSH_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BRUSH_CAPABILITYSET()
		msg.brushSupportLevel = BRUSH_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_BRUSH_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t