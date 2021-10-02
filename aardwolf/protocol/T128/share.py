import enum
import io

class PDUTYPE(enum.Enum):
	DEMANDACTIVEPDU = 0x1 #Demand Active PDU (section 2.2.1.13.1).
	CONFIRMACTIVEPDU = 0x3 # Confirm Active PDU (section 2.2.1.13.2).
	DEACTIVATEALLPDU = 0x6 # Deactivate All PDU (section 2.2.3.1)
	DATAPDU = 0x7 # Data PDU (actual type is revealed by the pduType2 field in the Share Data Header (section 2.2.8.1.1.1.2) structure).
	SERVER_REDIR_PKT = 0xA # Enhanced Security Server Redirection PDU (section 2.2.13.3.1).

class STREAM_TYPE(enum.Enum):
	UNDEFINED = 0x00 #Undefined stream priority. This value might be used in the Server Synchronize PDU (section 2.2.1.19) due to a server-side RDP bug. It MUST NOT be used in conjunction with any other PDUs.
	LOW = 0x01 #Low-priority stream.
	MED = 0x02 #Medium-priority stream.
	HI = 0x04 #High-priority stream.

class PDUTYPE2(enum.Enum):
	UPDATE = 0x02 #Graphics Update PDU (section 2.2.9.1.1.3)
	CONTROL = 0x14 #Control PDU (section 2.2.1.15.1)
	POINTER = 0x1B #Pointer Update PDU (section 2.2.9.1.1.4)
	INPUT = 0x1C #Input Event PDU (section 2.2.8.1.1.3)
	SYNCHRONIZE = 0x1F #Synchronize PDU (section 2.2.1.14.1)
	REFRESH_RECT = 0x21 #Refresh Rect PDU (section 2.2.11.2.1)
	PLAY_SOUND = 0x22 #Play Sound PDU (section 2.2.9.1.1.5.1)
	SUPPRESS_OUTPUT = 0x23 #Suppress Output PDU (section 2.2.11.3.1)
	SHUTDOWN_REQUEST = 0x24 #Shutdown Request PDU (section 2.2.2.1.1)
	SHUTDOWN_DENIED = 0x25 #Shutdown Request Denied PDU (section 2.2.2.2.1)
	SAVE_SESSION_INFO = 0x26 #Save Session Info PDU (section 2.2.10.1.1)
	FONTLIST = 0x27 #Font List PDU (section 2.2.1.18.1)
	FONTMAP = 0x28 #Font Map PDU (section 2.2.1.22.1)
	SET_KEYBOARD_INDICATORS = 0x29 #Set Keyboard Indicators PDU (section 2.2.8.2.1.1)
	BITMAPCACHE_PERSISTENT_LIST = 0x2B #Persistent Key List PDU (section 2.2.1.17.1)
	BITMAPCACHE_ERROR_PDU = 0x2C #Bitmap Cache Error PDU ([MS-RDPEGDI] section 2.2.2.3.1)
	SET_KEYBOARD_IME_STATUS = 0x2D #Set Keyboard IME Status PDU (section 2.2.8.2.2.1)
	OFFSCRCACHE_ERROR_PDU = 0x2E #Offscreen Bitmap Cache Error PDU ([MS-RDPEGDI] section 2.2.2.3.2)
	SET_ERROR_INFO_PDU = 0x2F #Set Error Info PDU (section 2.2.5.1.1)
	DRAWNINEGRID_ERROR_PDU = 0x30 #DrawNineGrid Cache Error PDU ([MS-RDPEGDI] section 2.2.2.3.3)
	DRAWGDIPLUS_ERROR_PDU = 0x31 #GDI+ Error PDU ([MS-RDPEGDI] section 2.2.2.3.4)
	ARC_STATUS_PDU = 0x32 #Auto-Reconnect Status PDU (section 2.2.4.1.1)
	STATUS_INFO_PDU = 0x36 #Status Info PDU (section 2.2.5.2)
	MONITOR_LAYOUT_PDU = 0x37 #Monitor Layout PDU (section 2.2.12.1)

class CompType(enum.IntFlag):
	CompressionTypeMask = 0x0F #Indicates the package which was used for compression. See the table which follows for a list of compression packages.
	PACKET_COMPRESSED = 0x20 #The payload data is compressed. This flag is equivalent to MPPC bit C (for more information see [RFC2118] section 3.1).
	PACKET_AT_FRONT = 0x40 #The decompressed packet MUST be placed at the beginning of the history buffer. This flag is equivalent to MPPC bit B (for more information see [RFC2118] section 3.1).
	PACKET_FLUSHED = 0x80 #The decompressor MUST reinitialize the history buffer (by filling it with zeros) and reset the HistoryOffset to zero. After it has been reinitialized, the entire history buffer is immediately regarded as valid. This flag is equivalent to MPPC bit A (for more information see [RFC2118] section 3.1). If the PACKET_COMPRESSED (0x20) flag is also present, then the PACKET_FLUSHED flag MUST be processed first.
	PACKET_COMPR_TYPE_8K = 0x0 #RDP 4.0 bulk compression (section 3.1.8.4.1).
	PACKET_COMPR_TYPE_64K = 0x1 #RDP 5.0 bulk compression (section 3.1.8.4.2).
	PACKET_COMPR_TYPE_RDP6 = 0x2 #RDP 6.0 bulk compression ([MS-RDPEGDI] section 3.1.8.1).
	PACKET_COMPR_TYPE_RDP61 = 0x3 #RDP 6.1 bulk compression ([MS-RDPEGDI] section 3.1.8.2).

class TS_SHARECONTROLHEADER:
	def __init__(self):
		self.totalLength:int = None
		self.pduType:PDUTYPE = None
		self.pduVersion:int = 1
		self.pduSource:int = None #channel ID

	def to_bytes(self):
		t = self.totalLength.to_bytes(2, byteorder='little', signed = False)
		t += (self.pduType.value  | self.pduVersion << 4).to_bytes(2, byteorder='little', signed = False)
		t += self.pduSource.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SHARECONTROLHEADER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SHARECONTROLHEADER()
		msg.totalLength = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		t = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.pduType = PDUTYPE(t & 0xF)
		msg.pduVersion = t >> 4
		buff.read(1)
		msg.pduSource = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_SHARECONTROLHEADER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_SHAREDATAHEADER:
	def __init__(self):
		self.shareControlHeader:TS_SHARECONTROLHEADER = None
		self.shareID:int = None
		self.pad1:int = 0
		self.streamID:STREAM_TYPE = None
		self.uncompressedLength:int = None
		self.pduType2:PDUTYPE2 = None 
		self.compressedType:CompType = None
		self.compressedLength:int = None

	def to_bytes(self):
		t = self.shareControlHeader.to_bytes()
		t += self.shareID.to_bytes(4, byteorder='little', signed = False)
		t += self.pad1.to_bytes(1, byteorder='little', signed = False)
		t += self.streamID.value.to_bytes(1, byteorder='little', signed = False)
		t += self.uncompressedLength.to_bytes(2, byteorder='little', signed = False)
		t += self.pduType2.value.to_bytes(1, byteorder='little', signed = False)
		t += self.compressedType.to_bytes(1, byteorder='little', signed = False)
		t += self.compressedLength.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SHAREDATAHEADER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SHAREDATAHEADER()
		msg.shareControlHeader = TS_SHARECONTROLHEADER.from_buffer(buff)
		msg.shareID = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.pad1 = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.streamID = STREAM_TYPE(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.uncompressedLength = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pduType2 = PDUTYPE2(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.compressedType = CompType(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.compressedLength = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_SHAREDATAHEADER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t