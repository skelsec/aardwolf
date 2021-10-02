import enum
import io


class TS_SYSTEMTIME:
	def __init__(self):
		self.wYear:int = 0
		self.wMonth:int = None
		self.wDayOfWeek:int = None
		self.wDay:int = None
		self.wHour:int = None
		self.wMinute:int = None
		self.wSecond:int = 0
		self.wMilliseconds:int = 0

	def to_bytes(self):
		t = self.wYear.to_bytes(2, byteorder='little', signed = False)
		t += self.wMonth.to_bytes(2, byteorder='little', signed = False)
		t += self.wDayOfWeek.to_bytes(2, byteorder='little', signed = False)
		t += self.wDay.to_bytes(2, byteorder='little', signed = False)
		t += self.wHour.to_bytes(2, byteorder='little', signed = False)
		t += self.wMinute.to_bytes(2, byteorder='little', signed = False)
		t += self.wSecond.to_bytes(2, byteorder='little', signed = False)
		t += self.wMilliseconds.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SYSTEMTIME.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SYSTEMTIME()
		msg.wYear = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wMonth = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wDayOfWeek = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wDay = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wHour = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wMinute = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wSecond = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wMilliseconds = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_SYSTEMTIME ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_TIME_ZONE_INFORMATION:
	def __init__(self):
		self.Bias:int = None
		self.StandardName:bytes = None
		self.StandardDate:TS_SYSTEMTIME = None
		self.StandardBias:int = None
		self.DaylightName:bytes = None
		self.DaylightDate:TS_SYSTEMTIME = None
		self.DaylightBias:int = 0

	def to_bytes(self):
		t = self.Bias.to_bytes(4, byteorder='little', signed = False)
		t += self.StandardName
		t += self.StandardDate.to_bytes()
		t += self.StandardBias.to_bytes(4, byteorder='little', signed = False)
		t += self.DaylightName
		t += self.DaylightDate.to_bytes()
		t += self.DaylightBias.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_TIME_ZONE_INFORMATION.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_TIME_ZONE_INFORMATION()
		msg.Bias = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.StandardName = buff.read(64)
		msg.StandardDate = TS_SYSTEMTIME.from_buffer(buff)
		msg.StandardBias = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.DaylightName = buff.read(64)
		msg.DaylightDate = TS_SYSTEMTIME.from_buffer(buff)
		msg.DaylightBias = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_TIME_ZONE_INFORMATION ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class PERF(enum.IntFlag):
	DISABLE_WALLPAPER = 0x00000001 #Disable desktop wallpaper.
	DISABLE_FULLWINDOWDRAG = 0x00000002 #Disable full-window drag (only the window outline is displayed when the window is moved).
	DISABLE_MENUANIMATIONS = 0x00000004 #Disable menu animations.
	DISABLE_THEMING = 0x00000008 #Disable user interface themes.
	RESERVED1 = 0x00000010 #An unused flag that is reserved for future use. This flag SHOULD be ignored by the server.
	DISABLE_CURSOR_SHADOW = 0x00000020 #Disable mouse cursor shadows.
	DISABLE_CURSORSETTINGS = 0x00000040 #Disable cursor blinking.
	ENABLE_FONT_SMOOTHING = 0x00000080 #Enable font smoothing.<18>
	ENABLE_DESKTOP_COMPOSITION = 0x00000100 #Enable Desktop Composition ([MS-RDPEDC] sections 1, 2 and 3; and [MS-RDPCR2] sections 1, 2 and 3). The usage of Desktop Composition in a remote session requires that the color depth be 32 bits per pixel (bpp). (See the description of the highColorDepth, supportedColorDepths and earlyCapabilityFlags (specifically the RNS_UD_CS_WANT_32BPP_SESSION (0x0002) flag) fields in section 2.2.1.3.2 for background on setting the remote session color depth to 32 bpp.)<19>
	RESERVED2 = 0x80000000 #An unused flag that is reserved for future use. This flag SHOULD be ignored by the server.

class CLI_AF(enum.Enum):
	AF_INET  = 0x0002 #The clientAddress field contains an IPv4 address.
	AF_INET6 = 0x0017 #The clientAddress field contains an IPv6 address.

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/732394f5-e2b5-4ac5-8a0a-35345386b0d1
class TS_EXTENDED_INFO_PACKET:
	def __init__(self):
		self.clientAddressFamily:CLI_AF = None
		self.cbClientAddress:int = None
		self.clientAddress:str = None
		self.cbClientDir:int = None
		self.clientDir:str = None
		self.clientTimeZone:TS_TIME_ZONE_INFORMATION = None
		self.clientSessionId:int = 0
		self.performanceFlags:PERF = None
		self.cbAutoReconnectCookie:int = None
		self.autoReconnectCookie:bytes = None
		self.reserved1:bytes = b'\x00\x00'
		self.reserved2:bytes = b'\x00\x00'
		self.cbDynamicDSTTimeZoneKeyName:int = None
		self.dynamicDSTTimeZoneKeyName:str = None
		self.dynamicDaylightTimeDisabled:bool = None

	def to_bytes(self):
		t = self.clientAddressFamily.value.to_bytes(2, byteorder='little', signed = False)
		t += len((self.clientAddress+'\x00').encode('utf-16-le')).to_bytes(2, byteorder='little', signed = False)
		t += (self.clientAddress+'\x00').encode('utf-16-le')
		t += len((self.clientDir+'\x00').encode('utf-16-le')).to_bytes(2, byteorder='little', signed = False)
		t += (self.clientDir+'\x00').encode('utf-16-le')
		if self.clientTimeZone is None:
			return t
		t += self.clientTimeZone.to_bytes()
		if self.clientSessionId is None:
			return t
		t += self.clientSessionId.to_bytes(4, byteorder='little', signed = False)
		if self.performanceFlags is None:
			return t
		t += self.performanceFlags.to_bytes(4, byteorder='little', signed = False)
		if self.autoReconnectCookie is None:
			return t
		t += len(self.autoReconnectCookie).to_bytes(2, byteorder='little', signed = False)
		if self.autoReconnectCookie is None:
			return t
		t += self.autoReconnectCookie
		if self.reserved1 is None:
			return t
		t += self.reserved1
		if self.reserved2 is None:
			return t
		t += self.reserved2
		if self.dynamicDSTTimeZoneKeyName is None:
			return t
		t += len(self.dynamicDSTTimeZoneKeyName).to_bytes(2, byteorder='little', signed = False)
		if self.dynamicDSTTimeZoneKeyName is None:
			return t
		t += self.dynamicDSTTimeZoneKeyName.encode()
		if self.dynamicDaylightTimeDisabled is None:
			return t
		t += int(self.dynamicDaylightTimeDisabled).to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_EXTENDED_INFO_PACKET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_EXTENDED_INFO_PACKET()		
		msg.clientAddressFamily = CLI_AF(int.from_bytes(buff.read(2), byteorder='little', signed= False))
		msg.cbClientAddress = int.from_bytes(buff.read(2), byteorder='little', signed= False)
		msg.clientAddress = buff.read(msg.cbClientAddress).decode('utf-16-le').replace('\x00', '')
		msg.cbClientDir = int.from_bytes(buff.read(2), byteorder='little', signed= False)
		msg.clientDir = buff.read(msg.cbClientDir).decode('utf-16-le').replace('\x00', '')
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.clientTimeZone = TS_TIME_ZONE_INFORMATION.from_buffer(buff)
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.clientSessionId = int.from_bytes(buff.read(4), byteorder='little', signed= False)
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.performanceFlags = PERF(int.from_bytes(buff.read(4), byteorder='little', signed= False))
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.cbAutoReconnectCookie = int.from_bytes(buff.read(2), byteorder='little', signed= False)
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.autoReconnectCookie = buff.read(28) #always 28 docu
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.reserved1 = buff.read(2)
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.reserved2 = buff.read(2)
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.cbDynamicDSTTimeZoneKeyName = int.from_bytes(buff.read(2), byteorder='little', signed= False)
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.dynamicDSTTimeZoneKeyName = buff.read(msg.cbDynamicDSTTimeZoneKeyName).decode()
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		msg.dynamicDaylightTimeDisabled = bool(int.from_bytes(buff.read(2), byteorder='little', signed= False))
		return msg

	def __repr__(self):
		t = '==== TS_EXTENDED_INFO_PACKET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t