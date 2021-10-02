import io
import enum

class OSMAJORTYPE(enum.Enum):
	UNSPECIFIED = 0x0000 #Unspecified platform
	WINDOWS = 0x0001 #Windows platform 
	OS2 = 0x0002 #OS/2 platform
	MACINTOSH = 0x0003 #Macintosh platform
	UNIX = 0x0004 #UNIX platform
	IOS= 0x0005 #iOS platform
	OSX = 0x0006 #OS X platform
	ANDROID = 0x0007 #Android platform
	CHROME_OS = 0x0008 #Chrome OS platform

class OSMINORTYPE(enum.Enum):
	UNSPECIFIED = 0x0000 #Unspecified version
	WINDOWS_31X = 0x0001 #Windows 3.1x
	WINDOWS_95 = 0x0002 #Windows 95
	WINDOWS_NT = 0x0003 #Windows NT
	OS2_V21 = 0x0004 #OS/2 2.1
	POWER_PC = 0x0005 #PowerPC
	MACINTOSH = 0x0006 #Macintosh
	NATIVE_XSERVER = 0x0007 #Native X Server
	PSEUDO_XSERVER = 0x0008 #Pseudo X Server
	WINDOWS_RT = 0x0009 #Windows RT

class EXTRAFLAG(enum.IntFlag):
	FASTPATH_OUTPUT_SUPPORTED = 0x0001 #Advertiser supports fast-path output.<24>
	NO_BITMAP_COMPRESSION_HDR = 0x0400 #Advertiser supports excluding the 8-byte Compressed Data Header (section 2.2.9.1.1.3.1.2.3) from the Bitmap Data (section 2.2.9.1.1.3.1.2.2) structure or the Cache Bitmap (Revision 2) Secondary Drawing Order ([MS-RDPEGDI] section 2.2.2.2.1.2.3).
	LONG_CREDENTIALS_SUPPORTED = 0x0004 #Advertiser supports long-length credentials for the user name, password, or domain name in the Save Session Info PDU (section 2.2.10.1).<25>
	AUTORECONNECT_SUPPORTED = 0x0008 #Advertiser supports auto-reconnection (section 5.5).
	ENC_SALTED_CHECKSUM = 0x0010 #Advertiser supports salted MAC generation (section 5.3.6.1.1).



class TS_GENERAL_CAPABILITYSET:
	def __init__(self):
		self.osMajorType:OSMAJORTYPE = None
		self.osMinorType:OSMINORTYPE = None
		self.protocolVersion:int = 0x0200
		self.pad2octetsA:bytes = b'\x00'*2
		self.compressionTypes:int = 0
		self.extraFlags:EXTRAFLAG = None
		self.updateCapabilityFlag:int = 0
		self.remoteUnshareFlag:int = 0
		self.compressionLevel:int = 0
		self.refreshRectSupport:bool = False
		self.suppressOutputSupport:bool = False

	def to_bytes(self):
		t = self.osMajorType.value.to_bytes(2, byteorder='little', signed = False)
		t += self.osMinorType.value.to_bytes(2, byteorder='little', signed = False)
		t += self.protocolVersion.to_bytes(2, byteorder='little', signed = False)
		t += self.pad2octetsA
		t += self.compressionTypes.to_bytes(2, byteorder='little', signed = False)
		t += self.extraFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.updateCapabilityFlag.to_bytes(2, byteorder='little', signed = False)
		t += self.remoteUnshareFlag.to_bytes(2, byteorder='little', signed = False)
		t += self.compressionLevel.to_bytes(2, byteorder='little', signed = False)
		t += int(self.refreshRectSupport).to_bytes(1, byteorder='little', signed = False)
		t += int(self.suppressOutputSupport).to_bytes(1, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_GENERAL_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_GENERAL_CAPABILITYSET()
		msg.osMajorType = OSMAJORTYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.osMinorType = OSMINORTYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.protocolVersion = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pad2octetsA = buff.read(2)
		msg.compressionTypes = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.extraFlags = EXTRAFLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.updateCapabilityFlag = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.remoteUnshareFlag = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.compressionLevel = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.refreshRectSupport = bool(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.suppressOutputSupport = bool(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_GENERAL_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t