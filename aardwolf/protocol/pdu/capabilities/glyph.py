import io
import enum

class GLYPH_SUPPORT(enum.Enum):
	NONE = 0x0000 #The client does not support glyph caching. All text output will be sent to the client as expensive Bitmap Updates (sections 2.2.9.1.1.3.1.2 and 2.2.9.1.2.1.2).
	PARTIAL = 0x0001 #Indicates support for Revision 1 Cache Glyph Secondary Drawing Orders ([MS-RDPEGDI] section 2.2.2.2.1.2.5).
	FULL = 0x0002 #Indicates support for Revision 1 Cache Glyph Secondary Drawing Orders ([MS-RDPEGDI] section 2.2.2.2.1.2.5).
	ENCODE = 0x0003 #Indicates support for Revision 2 Cache Glyph Secondary Drawing Orders ([MS-RDPEGDI] section 2.2.2.2.1.2.6).

class TS_GLYPHCACHE_CAPABILITYSET:
	def __init__(self):
		self.GlyphCache:bytes = b'\x00'*40 #https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/cae26830-263c-4c1e-97c2-b561faded3d9
		self.FragCache:bytes = b'\x00'*4
		self.GlyphSupportLevel:GLYPH_SUPPORT = GLYPH_SUPPORT.NONE
		self.pad2octets: bytes = b'\x00'*2

	def to_bytes(self):
		t = self.GlyphCache
		t += self.FragCache
		t += self.GlyphSupportLevel.value.to_bytes(2, byteorder='little', signed = False)
		t += self.pad2octets
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_GLYPHCACHE_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_GLYPHCACHE_CAPABILITYSET()
		msg.GlyphCache = buff.read(40)
		msg.FragCache = buff.read(4)
		msg.GlyphSupportLevel = GLYPH_SUPPORT(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.pad2octets = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_GLYPHCACHE_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t