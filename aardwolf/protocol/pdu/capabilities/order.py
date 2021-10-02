import io
import enum

class ORDERFLGS_SUPP(enum.IntFlag):
	TS_NEG_DSTBLT_INDEX = 0x01 #DstBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.1).
	TS_NEG_PATBLT_INDEX = 0x02 #PatBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.3) and OpaqueRect Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.5).
	TS_NEG_SCRBLT_INDEX = 0x04 #ScrBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.7).<26>
	TS_NEG_MEMBLT_INDEX = 0x08 #MemBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.9).<27>
	TS_NEG_MEM3BLT_INDEX = 0x10 #Mem3Blt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.10).
	UnusedIndex1 = 0x20 #The contents of the byte at this index MUST be ignored.
	UnusedIndex2 = 0x40 #The contents of the byte at this index MUST be ignored.
	TS_NEG_DRAWNINEGRID_INDEX = 0x80 #DrawNineGrid Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.21).
	TS_NEG_LINETO_INDEX = 0x100 #LineTo Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.11).
	TS_NEG_MULTI_DRAWNINEGRID_INDEX = 0x200 #MultiDrawNineGrid Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.22).
	UnusedIndex3 = 0x400 #The contents of the byte at this index MUST be ignored.
	TS_NEG_SAVEBITMAP_INDEX = 0x800 #SaveBitmap Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.12).
	UnusedIndex4 = 0x1000 #The contents of the byte at this index MUST be ignored.
	UnusedIndex5 = 0x2000 #The contents of the byte at this index MUST be ignored.
	UnusedIndex6 = 0x4000 #The contents of the byte at this index MUST be ignored.
	TS_NEG_MULTIDSTBLT_INDEX = 0x8000 #MultiDstBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.2).
	TS_NEG_MULTIPATBLT_INDEX = 0x10000 #MultiPatBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.4).
	TS_NEG_MULTISCRBLT_INDEX = 0x20000 #MultiScrBlt Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.8).
	TS_NEG_MULTIOPAQUERECT_INDEX = 0x40000 #MultiOpaqueRect Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.6).
	TS_NEG_FAST_INDEX_INDEX = 0x80000 #FastIndex Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.14).
	TS_NEG_POLYGON_SC_INDEX = 0x100000 #PolygonSC Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.16) and PolygonCB Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.17).
	TS_NEG_POLYGON_CB_INDEX = 0x200000 #PolygonCB Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.17) and PolygonSC Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.16).
	TS_NEG_POLYLINE_INDEX = 0x400000 #Polyline Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.18).
	UnusedIndex7 = 0x800000 #The contents of the byte at this index MUST be ignored.
	TS_NEG_FAST_GLYPH_INDEX = 0x1000000 #FastGlyph Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.15).
	TS_NEG_ELLIPSE_SC_INDEX = 0x2000000 #EllipseSC Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.19) and EllipseCB Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.20).
	TS_NEG_ELLIPSE_CB_INDEX = 0x4000000 #EllipseCB Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.20) and EllipseSC Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.19).
	TS_NEG_INDEX_INDEX = 0x8000000 #GlyphIndex Primary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.1.2.13).
	UnusedIndex8 = 0x10000000 #The contents of the byte at this index MUST be ignored.
	UnusedIndex9 = 0x20000000 #The contents of the byte at this index MUST be ignored.
	UnusedIndex10 = 0x40000000 #The contents of the byte at this index MUST be ignored.
	UnusedIndex11 = 0x80000000 #The contents of the byte at this index MUST be ignored.
	
class ORDERFLAGS_EX(enum.IntFlag):
	CACHE_BITMAP_REV3_SUPPORT = 0x0002 #The Cache Bitmap (Revision 3) Secondary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.2.8) is supported.
	ALTSEC_FRAME_MARKER_SUPPORT = 0x0004 #The Frame Marker Alternate Secondary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.3.7) is supported.

class ORDERFLAG(enum.IntFlag):
	NEGOTIATEORDERSUPPORT = 0x0002 #Indicates support for specifying supported drawing orders in the orderSupport field. This flag MUST be set.
	ZEROBOUNDSDELTASSUPPORT = 0x0008 #Indicates support for the TS_ZERO_BOUNDS_DELTAS (0x20) flag ([MS-RDPEGDI] section 2.2.2.2.1.1.2). The client MUST set this flag.
	COLORINDEXSUPPORT = 0x0020 #Indicates support for sending color indices (not RGB values) in orders.
	SOLIDPATTERNBRUSHONLY = 0x0040 #Indicates that this party can receive only solid and pattern brushes.
	ORDERFLAGS_EXTRA_FLAGS = 0x0080 #Indicates that the orderSupportExFlags field contains valid data.

class TS_ORDER_CAPABILITYSET:
	def __init__(self):
		self.terminalDescriptor:bytes = b'\x00' * 16
		self.pad4octetsA:bytes = b'\x00' * 4
		self.desktopSaveXGranularity:int = 1
		self.desktopSaveYGranularity:int = 20
		self.pad2octetsA:bytes = b'\x00' * 2
		self.maximumOrderLevel:int = 1
		self.numberFonts:int = 0
		self.orderFlags:ORDERFLAG = None
		self.orderSupport:ORDERFLGS_SUPP = 0
		self.textFlags:bytes = b'\x00' * 2
		self.orderSupportExFlags:ORDERFLAGS_EX = 0
		self.pad4octetsB:bytes = b'\x00' * 4
		self.desktopSaveSize:int = 230400 #[MS-RDPEGDI] section 2.2.2.2.1.1.2.12
		self.pad2octetsC:bytes = b'\x00' * 2
		self.pad2octetsD:bytes = b'\x00' * 2
		self.textANSICodePage:bytes = b'\x00' * 2 #ignored
		self.pad2octetsE:bytes = b'\x00' * 2


	def to_bytes(self):
		t  = self.terminalDescriptor
		t += self.pad4octetsA
		t += self.desktopSaveXGranularity.to_bytes(2, byteorder='little', signed = False)
		t += self.desktopSaveYGranularity.to_bytes(2, byteorder='little', signed = False)
		t += self.pad2octetsA
		t += self.maximumOrderLevel.to_bytes(2, byteorder='little', signed = False)
		t += self.numberFonts.to_bytes(2, byteorder='little', signed = False)
		t += self.orderFlags.to_bytes(2, byteorder='little', signed = False)
		for bit in bin(self.orderSupport)[2:].ljust(32,'0')[::-1]:
			if bit == '1':
				t += b'\x01'
			else:
				t += b'\x00'
		t += self.textFlags
		t += self.orderSupportExFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.pad4octetsB
		t += self.desktopSaveSize.to_bytes(4, byteorder='little', signed = False)
		t += self.pad2octetsC
		t += self.pad2octetsD
		t += self.textANSICodePage
		t += self.pad2octetsE
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_ORDER_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_ORDER_CAPABILITYSET()
		msg.terminalDescriptor = buff.read(16)
		msg.pad4octetsA = buff.read(4)
		msg.desktopSaveXGranularity = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.desktopSaveYGranularity = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pad2octetsA = buff.read(2)
		msg.maximumOrderLevel = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.numberFonts = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.orderFlags = ORDERFLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		#waaaarghhh
		temp = ''
		for _ in range(32):
			temp += str(int(bool(buff.read(1)[0])))
		msg.orderSupport = ORDERFLGS_SUPP(int(temp[::-1],2))
		msg.textFlags = buff.read(2)
		msg.orderSupportExFlags = ORDERFLAGS_EX(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.pad4octetsB = buff.read(4)
		msg.desktopSaveSize = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.pad2octetsC = buff.read(2)
		msg.pad2octetsD = buff.read(2)
		msg.textANSICodePage = buff.read(2)
		msg.pad2octetsE = buff.read(2)
		return msg

	def __repr__(self):
		t = '==== TS_ORDER_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t