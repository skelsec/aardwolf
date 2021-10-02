import io
import enum


class DRAWFLAG(enum.IntFlag):
	ALLOW_DYNAMIC_COLOR_FIDELITY = 0x02 #Indicates support for lossy compression of 32 bpp bitmaps by reducing color-fidelity on a per-pixel basis ([MS-RDPEGDI] section 3.1.9.1.4).
	ALLOW_COLOR_SUBSAMPLING = 0x04 #Indicates support for chroma subsampling when compressing 32 bpp bitmaps ([MS-RDPEGDI] section 3.1.9.1.3).
	ALLOW_SKIP_ALPHA = 0x08 #Indicates that the client supports the removal of the alpha-channel when compressing 32 bpp bitmaps. In this case the alpha is assumed to be 0xFF, meaning the bitmap is opaque.
	UNUSED_FLAG = 0x10 #An unused flag that MUST be ignored by the client if it is present in the server-to-client Bitmap Capability Set.



class TS_BITMAP_CAPABILITYSET:
	def __init__(self):
		self.preferredBitsPerPixel:int = None
		self.receive1BitPerPixel:bool = True
		self.receive4BitsPerPixel:bool = True
		self.receive8BitsPerPixel:bool = True
		self.desktopWidth:int = None
		self.desktopHeight:int = None
		self.pad2octets:int = 0
		self.desktopResizeFlag:bool = False
		self.bitmapCompressionFlag:bool = True
		self.highColorFlags:int = 0
		self.drawingFlags:DRAWFLAG = DRAWFLAG.UNUSED_FLAG
		self.multipleRectangleSupport:bool = True
		self.pad2octetsB:int = 0

	def to_bytes(self):
		t = self.preferredBitsPerPixel.to_bytes(2, byteorder='little', signed = False)
		t += int(self.receive1BitPerPixel).to_bytes(2, byteorder='little', signed = False)
		t += int(self.receive4BitsPerPixel).to_bytes(2, byteorder='little', signed = False)
		t += int(self.receive8BitsPerPixel).to_bytes(2, byteorder='little', signed = False)
		t += self.desktopWidth.to_bytes(2, byteorder='little', signed = False)
		t += self.desktopHeight.to_bytes(2, byteorder='little', signed = False)
		t += self.pad2octets.to_bytes(2, byteorder='little', signed = False)
		t += int(self.desktopResizeFlag).to_bytes(2, byteorder='little', signed = False)
		t += int(self.bitmapCompressionFlag).to_bytes(2, byteorder='little', signed = False)
		t += self.highColorFlags.to_bytes(1, byteorder='little', signed = False)
		t += self.drawingFlags.to_bytes(1, byteorder='little', signed = False)
		t += int(self.multipleRectangleSupport).to_bytes(2, byteorder='little', signed = False)
		t += int(self.pad2octetsB).to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAP_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAP_CAPABILITYSET()
		msg.preferredBitsPerPixel = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.receive1BitPerPixel = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.receive4BitsPerPixel = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.receive8BitsPerPixel = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.desktopWidth = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.desktopHeight = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pad2octets = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.desktopResizeFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.bitmapCompressionFlag = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.highColorFlags = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.drawingFlags = DRAWFLAG(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.multipleRectangleSupport = bool(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.pad2octetsB = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAP_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t