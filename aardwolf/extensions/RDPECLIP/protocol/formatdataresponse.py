
import io
import enum
from typing import List

from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT

class MAPPING_MODE(enum.Enum):
	TEXT = 0x00000001 #Each logical unit is mapped to one device pixel. Positive x is to the right; positive y is down.
	LOMETRIC = 0x00000002 #Each logical unit is mapped to 0.1 millimeter. Positive x is to the right; positive y is up.
	HIMETRIC = 0x00000003 #Each logical unit is mapped to 0.01 millimeter. Positive x is to the right; positive y is up.
	LOENGLISH = 0x00000004 #Each logical unit is mapped to 0.01 inch. Positive x is to the right; positive y is up.
	HIENGLISH = 0x00000005 #Each logical unit is mapped to 0.001 inch. Positive x is to the right; positive y is up.
	TWIPS = 0x00000006 #Each logical unit is mapped to 1/20 of a printer's point (1/1440 of an inch), also called a twip. Positive x is to the right; positive y is up.
	ISOTROPIC = 0x00000007 #Logical units are mapped to arbitrary units with equally scaled axes; one unit along the x-axis is equal to one unit along the y-axis.
	ANISOTROPIC = 0x00000008


class CLIPRDR_MFPICT:
	def __init__(self):
		self.mappingMode:MAPPING_MODE = None
		self.xExt:int = None
		self.yExt:int = None
		self.metaFileData:bytes = None

	def to_bytes(self):
		t = self.mappingMode.value.to_bytes(4, byteorder='little', signed=False)
		t += self.xExt.to_bytes(4, byteorder='little', signed=False)
		t += self.yExt.to_bytes(4, byteorder='little', signed=False)
		t += self.metaFileData
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_MFPICT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_MFPICT()
		msg.mappingMode = MAPPING_MODE(int.from_bytes(buff.read(4), byteorder='little', signed=False))
		msg.xExt = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		msg.yExt = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		msg.metaFileData = buff.read()
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_MFPICT ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class PALETTEENTRY:
	def __init__(self):
		self.red:int = None
		self.green:int = None
		self.blue:int = None
		self.extra:bytes = b'\x00'

	def to_bytes(self):
		t = self.red.to_bytes(1, byteorder='little', signed=False)
		t += self.green.to_bytes(1, byteorder='little', signed=False)
		t += self.blue.to_bytes(1, byteorder='little', signed=False)
		t += self.extra
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return PALETTEENTRY.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = PALETTEENTRY()
		msg.red = buff.read(1)[0]
		msg.green = buff.read(1)[0]
		msg.blue = buff.read(1)[0]
		msg.extra = buff.read(1)
		return msg

	def __repr__(self):
		t = '==== PALETTEENTRY ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


class CLIPRDR_PALETTE:
	def __init__(self):
		self.paletteEntriesData:List[PALETTEENTRY] = []

	def to_bytes(self):
		t = b''
		for pe in self.paletteEntriesData:
			t += pe.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_PALETTE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_PALETTE()
		while buff.read(1) != b'':
			buff.seek(-1,1)
			PALETTEENTRY.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_PALETTE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class FD_FLAGS(enum.IntFlag):
	ATTRIBUTES = 0x00000004 #The fileAttributes field contains valid data.
	FILESIZE = 0x00000040 #The fileSizeHigh and fileSizeLow fields contain valid data.
	WRITESTIME = 0x00000020 #The lastWriteTime field contains valid data.
	SHOWPROGRESSUI = 0x00004000 #A progress indicator SHOULD be shown when copying the file.

class FILE_ATTRIBUTE(enum.IntFlag):
	READONLY = 0x00000001 #A file that is read-only. Applications can read the file, but cannot write to it or delete it.
	HIDDEN = 0x00000002 #The file or directory is hidden. It is not included in an ordinary directory listing.
	SYSTEM = 0x00000004 #A file or directory that the operating system uses a part of, or uses exclusively.
	DIRECTORY = 0x00000010 #Identifies a directory.
	ARCHIVE = 0x00000020 #A file or directory that is an archive file or directory. Applications typically use this attribute to mark files for backup or removal.
	NORMAL = 0x00000080 #A file that does not have other attributes set. This attribute is valid only when used alone.

class CLIPRDR_FILEDESCRIPTOR:
	def __init__(self):
		self.flags:FD_FLAGS = None
		self.reserved1:bytes = b'\x00'*32
		self.fileAttributes:FILE_ATTRIBUTE = None
		self.reserved2:bytes = None
		self.lastWriteTime:int = None
		self.fileSizeHigh:int = None
		self.fileSizeLow:int = None
		self.fileName:str = None #520 bytes, 260 chars null term

		self.fileSize:int =None

	def to_bytes(self):
		if self.fileSize is not None:
			self.fileSizeHigh = self.fileSize >> 32
			self.fileSizeLow = self.fileSize & 0xFFFFFFFF

		t = self.flags.to_bytes(4, byteorder='little', signed=False)
		t += self.reserved1
		t += self.fileAttributes.to_bytes(4, byteorder='little', signed=False)
		t += self.reserved2
		t += self.lastWriteTime.to_bytes(8, byteorder='little', signed=False)
		t += self.fileSizeHigh.to_bytes(4, byteorder='little', signed=False)
		t += self.fileSizeLow.to_bytes(4, byteorder='little', signed=False)
		t += self.fileName.encode('utf-16-le').ljust(b'\x00',520)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_FILEDESCRIPTOR.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_FILEDESCRIPTOR()
		msg.flags = FD_FLAGS(int.from_bytes(buff.read(4), byteorder='little', signed=False))
		msg.reserved1 = buff.read(32)
		msg.fileAttributes = FILE_ATTRIBUTE(int.from_bytes(buff.read(4), byteorder='little', signed=False))
		msg.reserved2 = buff.read(16)
		msg.lastWriteTime = FILE_ATTRIBUTE(int.from_bytes(buff.read(8), byteorder='little', signed=False))
		msg.fileSizeHigh = FILE_ATTRIBUTE(int.from_bytes(buff.read(4), byteorder='little', signed=False))
		msg.fileSizeLow = FILE_ATTRIBUTE(int.from_bytes(buff.read(4), byteorder='little', signed=False))
		msg.fileName = buff.read(520).decode('utf-16-le').replace('\x00','')
		msg.fileSize = msg.fileSizeHigh << 32 | msg.fileSizeLow
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FILEDESCRIPTOR ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


class CLIPRDR_FILELIST:
	def __init__(self):
		self.cItems:MAPPING_MODE = None
		self.fileDescriptorArray:List[CLIPRDR_FILEDESCRIPTOR] = []

	def to_bytes(self):
		t = len(self.fileDescriptorArray).to_bytes(4, byteorder='little', signed=False)
		for fd in self.fileDescriptorArray:
			t += fd.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_FILELIST.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_FILELIST()
		msg.cItems = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		for _ in range(msg.cItems):
			msg.fileDescriptorArray.append(CLIPRDR_FILEDESCRIPTOR.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FILELIST ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class CLIPRDR_FORMAT_DATA_RESPONSE:
	def __init__(self):
		self.dataobj = None

	def to_bytes(self, otype:CLIPBRD_FORMAT):
		if otype == CLIPBRD_FORMAT.CF_UNICODETEXT:
			t = self.dataobj.encode('utf-16-le') + b'\x00'*3
		elif otype == CLIPBRD_FORMAT.CF_TEXT:
			t = self.dataobj.encode('ascii') + b'\x00'
		else:
			t = self.dataobj.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes, otype:CLIPBRD_FORMAT):
		return CLIPRDR_FORMAT_DATA_RESPONSE.from_buffer(io.BytesIO(bbuff), otype = otype)

	@staticmethod
	def from_buffer(buff: io.BytesIO, otype:CLIPBRD_FORMAT):
		msg = CLIPRDR_FORMAT_DATA_RESPONSE()
		if otype == CLIPBRD_FORMAT.CF_HDROP: #TODO: not sure
			msg.dataobj = CLIPRDR_FILELIST.from_buffer(buff)
		elif otype == CLIPBRD_FORMAT.CF_PALETTE:
			msg.dataobj =  CLIPRDR_PALETTE.from_buffer(buff)
		elif otype == CLIPBRD_FORMAT.CF_METAFILEPICT:
			msg.dataobj =  CLIPRDR_MFPICT.from_buffer(buff)
		elif otype == CLIPBRD_FORMAT.CF_UNICODETEXT:
			msg.dataobj = buff.read().decode('utf-16-le').replace('\x00','')
		elif otype == CLIPBRD_FORMAT.CF_TEXT:
			msg.dataobj = buff.read().decode().replace('\x00','')
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FORMAT_DATA_RESPONSE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t