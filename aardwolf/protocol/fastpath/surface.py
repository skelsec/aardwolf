import io
import enum
from typing import List

class SURFCMD(enum.Enum):
	CMDTYPE_SET_SURFACE_BITS = 0x0001 #Indicates a Set Surface Bits Command (section 2.2.9.2.1).
	CMDTYPE_FRAME_MARKER = 0x0004 #Indicates a Frame Marker Command (section 2.2.9.2.3).
	CMDTYPE_STREAM_SURFACE_BITS = 0x0006 #Indicates a Stream Surface Bits Command (section 2.2.9.2.2).

class TS_COMPRESSED_BITMAP_HEADER_EX:
	def __init__(self):
		self.highUniqueId:int = None
		self.lowUniqueId:int = None
		self.tmMilliseconds:int = None
		self.tmSeconds:int = None

	def to_bytes(self):
		t = self.highUniqueId.to_bytes(4, byteorder='little', signed=False)
		t += self.lowUniqueId.to_bytes(4, byteorder='little', signed=False)
		t += self.tmMilliseconds.to_bytes(8, byteorder='little', signed=False)
		t += self.tmSeconds.to_bytes(8, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_COMPRESSED_BITMAP_HEADER_EX.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_COMPRESSED_BITMAP_HEADER_EX()
		msg.highUniqueId = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		msg.lowUniqueId = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		msg.tmMilliseconds = int.from_bytes(buff.read(8), byteorder='little', signed=False)
		msg.tmSeconds = int.from_bytes(buff.read(8), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_COMPRESSED_BITMAP_HEADER_EX ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class BITMAP_EX_FLAG(enum.IntFlag):
	EX_COMPRESSED_BITMAP_HEADER_PRESENT = 0x01 #Indicates that the optional exBitmapDataHeader field is present.

class TS_BITMAP_DATA_EX:
	def __init__(self):
		self.bpp:int = None
		self.flags:BITMAP_EX_FLAG = None
		self.reserved:int = None
		self.codecID:int = None
		self.width:int = None
		self.height:int = None
		self.bitmapDataLength:int = None
		self.exBitmapDataHeader:TS_COMPRESSED_BITMAP_HEADER_EX = None
		self.bitmapData:int = None

	def to_bytes(self):
		t = self.bpp.to_bytes(1, byteorder='little', signed=False)
		t += self.flags.to_bytes(1, byteorder='little', signed=False)
		t += self.reserved.to_bytes(1, byteorder='little', signed=False)
		t += self.codecID.to_bytes(1, byteorder='little', signed=False)
		t += self.width.to_bytes(2, byteorder='little', signed=False)
		t += self.height.to_bytes(2, byteorder='little', signed=False)
		t += len(self.bitmapData).to_bytes(4, byteorder='little', signed=False)
		if BITMAP_EX_FLAG.EX_COMPRESSED_BITMAP_HEADER_PRESENT in self.flags:
			t += self.exBitmapDataHeader.to_bytes()
		t += self.bitmapData
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAP_DATA_EX.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAP_DATA_EX()
		msg.bpp = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		msg.flags = BITMAP_EX_FLAG(int.from_bytes(buff.read(1), byteorder='little', signed=False))
		msg.reserved = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		msg.codecID = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		msg.width = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.height = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.bitmapDataLength = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		if BITMAP_EX_FLAG.EX_COMPRESSED_BITMAP_HEADER_PRESENT in msg.flags:
			msg.exBitmapDataHeader = TS_COMPRESSED_BITMAP_HEADER_EX.from_buffer(buff)
		msg.bitmapData = buff.read(msg.bitmapDataLength)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAP_DATA_EX ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t



class TS_SURFCMD_SET_SURF_BITS:
	def __init__(self):
		self.destLeft:int = None
		self.destTop:int = None
		self.destRight:int = None
		self.destBottom:int = None
		self.bitmapData:TS_BITMAP_DATA_EX = None

	def to_bytes(self):
		t = self.destLeft.to_bytes(2, byteorder='little', signed=False)
		t += self.destTop.to_bytes(2, byteorder='little', signed=False)
		t += self.destRight.to_bytes(2, byteorder='little', signed=False)
		t += self.destBottom.to_bytes(2, byteorder='little', signed=False)
		t += self.bitmapData.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SURFCMD_SET_SURF_BITS.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SURFCMD_SET_SURF_BITS()
		msg.destLeft = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destTop = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destRight = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destBottom = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.bitmapData = TS_BITMAP_DATA_EX.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_SURFCMD_SET_SURF_BITS ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class SURFACECMD_FRAMEACTION(enum.Enum):
	BEGIN = 0x0000 #Indicates the start of a new frame.
	END = 0x0001 #Indicates the end of the current frame.

class TS_FRAME_MARKER:
	def __init__(self):
		self.frameAction:SURFACECMD_FRAMEACTION = None
		self.frameId:int = None

	def to_bytes(self):
		t = self.frameAction.value.to_bytes(2, byteorder='little', signed=False)
		t += self.frameId.to_bytes(4, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FRAME_MARKER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FRAME_MARKER()
		msg.frameAction = SURFACECMD_FRAMEACTION(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		msg.frameId = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_FRAME_MARKER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_SURFCMD_STREAM_SURF_BITS:
	def __init__(self):
		self.destLeft:int = None
		self.destTop:int = None
		self.destRight:int = None
		self.destBottom:int = None
		self.bitmapData:TS_BITMAP_DATA_EX = None

	def to_bytes(self):
		t = self.destLeft.to_bytes(2, byteorder='little', signed=False)
		t += self.destTop.to_bytes(2, byteorder='little', signed=False)
		t += self.destRight.to_bytes(2, byteorder='little', signed=False)
		t += self.destBottom.to_bytes(2, byteorder='little', signed=False)
		t += self.bitmapData.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SURFCMD_STREAM_SURF_BITS.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SURFCMD_STREAM_SURF_BITS()
		msg.destLeft = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destTop = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destRight = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.destBottom = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.bitmapData = TS_BITMAP_DATA_EX.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_SURFCMD_STREAM_SURF_BITS ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_SURFCMD:
	def __init__(self):
		self.cmdType:SURFCMD = None
		self.cmdData = None

	def to_bytes(self):
		t = self.cmdType.value.to_bytes(2, byteorder='little', signed=False)
		t += self.cmdData.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SURFCMD.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SURFCMD()
		msg.cmdType = SURFCMD(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		if msg.cmdType == SURFCMD.CMDTYPE_SET_SURFACE_BITS:
			msg.cmdData = TS_SURFCMD_SET_SURF_BITS.from_buffer(buff)
		elif msg.cmdType == SURFCMD.CMDTYPE_FRAME_MARKER:
			msg.cmdData = TS_FRAME_MARKER.from_buffer(buff)
		elif msg.cmdType == SURFCMD.CMDTYPE_STREAM_SURFACE_BITS:
			msg.cmdData = TS_SURFCMD_STREAM_SURF_BITS.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_SURFCMD ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_FP_SURFCMDS:
	def __init__(self):
		self.surfaceCommands:List[TS_SURFCMD] = []

	def to_bytes(self):
		t = b''
		for cmd in self.surfaceCommands:
			t = cmd.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FP_SURFCMDS.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FP_SURFCMDS()
		
		return msg

	def __repr__(self):
		t = '==== TS_FP_SURFCMDS ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t