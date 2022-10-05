
import io
import enum
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, COLOR_DEPTH, HIGH_COLOR_DEPTH, \
	SUPPORTED_COLOR_DEPTH, CONNECTION_TYPE, RNS_UD_CS, ORIENTATION
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/8a36630c-9c8e-4864-9382-2ec9d6f368ca
class TS_UD_CS_CORE:
	def __init__(self):
		self.type:TS_UD_TYPE = TS_UD_TYPE.CS_CORE
		self.length = None

		self.version: int = 0x00080005
		self.desktopWidth: int = None
		self.desktopHeight: int = None
		self.colorDepth: COLOR_DEPTH = None
		self.SASSequence: int = 0xAA03
		self.keyboardLayout: int = 1033
		self.clientBuild: int = None
		self.clientName: str = None
		self.keyboardType: int = 0x00000004
		self.keyboardSubType: int = 0
		self.keyboardFunctionKey: int = 12
		self.imeFileName: str = None
		self.postBeta2ColorDepth: COLOR_DEPTH = None
		self.clientProductId:int = None
		self.serialNumber:int = None
		self.highColorDepth: HIGH_COLOR_DEPTH = None
		self.supportedColorDepths: SUPPORTED_COLOR_DEPTH = None
		self.earlyCapabilityFlags:RNS_UD_CS = None
		self.clientDigProductId:bytes = None
		self.connectionType:CONNECTION_TYPE = None
		self.pad1octet:bytes = None
		self.serverSelectedProtocol:SUPP_PROTOCOLS = None
		self.desktopPhysicalWidth:int = None
		self.desktopPhysicalHeight:int = None
		self.desktopOrientation:ORIENTATION = None
		self.desktopScaleFactor:int = None
		self.deviceScaleFactor:int = None

		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		clientName = self.clientName.encode('utf-16-le').ljust(32, b'\x00')
		imeFileName = self.imeFileName.encode('utf-16-le').ljust(64, b'\x00')
		t = self.version.to_bytes(4, byteorder='little', signed = False)
		t += self.desktopWidth.to_bytes(2, byteorder='little', signed = False)
		t += self.desktopHeight.to_bytes(2, byteorder='little', signed = False)
		t += self.colorDepth.value.to_bytes(2, byteorder='little', signed = False)
		t += self.SASSequence.to_bytes(2, byteorder='little', signed = False)
		t += self.keyboardLayout.to_bytes(4, byteorder='little', signed = False)
		t += self.clientBuild.to_bytes(4, byteorder='little', signed = False)
		t += clientName
		t += self.keyboardType.to_bytes(4, byteorder='little', signed = False)
		t += self.keyboardSubType.to_bytes(4, byteorder='little', signed = False)
		t += self.keyboardFunctionKey.to_bytes(4, byteorder='little', signed = False)
		t += imeFileName
		#optional fileds...
		if self.postBeta2ColorDepth is None:
			return finish(t)
		t += self.postBeta2ColorDepth.value.to_bytes(2, byteorder='little', signed = False)
		if self.clientProductId is None:
			return finish(t)
		t += self.clientProductId.to_bytes(2, byteorder='little', signed = False)
		if self.serialNumber is None:
			return finish(t)
		t += self.serialNumber.to_bytes(4, byteorder='little', signed = False)
		if self.highColorDepth is None:
			return finish(t)
		t += self.highColorDepth.value.to_bytes(2, byteorder='little', signed = False)
		if self.supportedColorDepths is None:
			return finish(t)
		t += self.supportedColorDepths.to_bytes(2, byteorder='little', signed = False)
		if self.earlyCapabilityFlags is None:
			return finish(t)
		t += self.earlyCapabilityFlags.to_bytes(2, byteorder='little', signed = False)
		if self.clientDigProductId is None:
			return finish(t)
		t += self.clientDigProductId
		if self.connectionType is None:
			return finish(t)
		t += self.connectionType.value.to_bytes(1, byteorder='little', signed = False)
		if self.pad1octet is None:
			return finish(t)
		t += self.pad1octet
		if self.serverSelectedProtocol is None:
			return finish(t)
		t += self.serverSelectedProtocol.value.to_bytes(4, byteorder='little', signed = False)
		if self.desktopPhysicalWidth is None:
			return finish(t)		
		t += self.desktopPhysicalWidth.to_bytes(4, byteorder='little', signed = False)
		if self.desktopPhysicalHeight is None:
			return finish(t)
		t += self.desktopPhysicalHeight.to_bytes(4, byteorder='little', signed = False)
		if self.desktopOrientation is None:
			return finish(t)
		t += self.desktopOrientation.value.to_bytes(2, byteorder='little', signed = False)
		if self.desktopScaleFactor is None:
			return finish(t)
		t += self.desktopScaleFactor.to_bytes(4, byteorder='little', signed = False)
		if self.deviceScaleFactor is None:
			return finish(t)
		t += self.deviceScaleFactor.to_bytes(4, byteorder='little', signed = False)
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_CS_CORE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		def is_end(buff, start, size):
			return buff.tell() - start >= msg.length
		start = buff.tell()
		msg = TS_UD_CS_CORE()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		dlen = msg.length
		msg.version = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.desktopWidth = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.desktopHeight = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.colorDepth = COLOR_DEPTH(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.SASSequence = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.keyboardLayout = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.clientBuild = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.clientName = buff.read(32).decode('utf-16-le').replace('\x00', '')
		msg.keyboardType = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.keyboardSubType = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.keyboardFunctionKey = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.imeFileName = buff.read(64).decode('utf-16-le').replace('\x00', '')
		if is_end(buff,start, dlen):
			return msg
		msg.postBeta2ColorDepth = COLOR_DEPTH(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		if is_end(buff,start, dlen):
			return msg
		msg.clientProductId = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		if is_end(buff,start, dlen):
			return msg
		msg.serialNumber = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_end(buff,start, dlen):
			return msg
		msg.highColorDepth = HIGH_COLOR_DEPTH(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		if is_end(buff,start, dlen):
			return msg
		msg.supportedColorDepths = SUPPORTED_COLOR_DEPTH(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		if is_end(buff,start, dlen):
			return msg
		msg.earlyCapabilityFlags = RNS_UD_CS(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		if is_end(buff,start, dlen):
			return msg
		msg.clientDigProductId = buff.read(64)
		if RNS_UD_CS.VALID_CONNECTION_TYPE in msg.earlyCapabilityFlags:
			msg.connectionType = CONNECTION_TYPE(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		else:
			buff.read(1)
			msg.connectionType = CONNECTION_TYPE.UNK
		if is_end(buff,start, dlen):
			return msg
		msg.pad1octet = buff.read(1)
		if is_end(buff,start, dlen):
			return msg
		msg.serverSelectedProtocol = SUPP_PROTOCOLS(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		if is_end(buff,start, dlen):
			return msg
		msg.desktopPhysicalWidth = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_end(buff,start, dlen):
			return msg
		msg.desktopPhysicalHeight = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_end(buff,start, dlen):
			return msg
		msg.desktopOrientation = ORIENTATION(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		if is_end(buff,start, dlen):
			return msg
		msg.desktopScaleFactor = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		if is_end(buff,start, dlen):
			return msg
		msg.deviceScaleFactor = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_UD_CS_CORE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t