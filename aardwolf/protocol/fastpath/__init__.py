
import enum
import io
from typing import List
from aardwolf.protocol.fastpath.palette import TS_UPDATE_PALETTE_DATA
from aardwolf.protocol.fastpath.bitmap import TS_UPDATE_BITMAP_DATA
from aardwolf.protocol.fastpath.pointer import TS_FP_LARGEPOINTERATTRIBUTE, TS_FP_CACHEDPOINTERATTRIBUTE, TS_FP_POINTERATTRIBUTE, TS_POINTERPOSATTRIBUTE, TS_FP_COLORPOINTERATTRIBUTE
from aardwolf.protocol.fastpath.surface import TS_SURFCMD
#from aardwolf.protocol.fastpath.order import TS_FP_UPDATE_ORDERS

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/68b5ee54-d0d5-4d65-8d81-e1c4025f7597
# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/a1c4caa8-00ed-45bb-a06e-5177473766d3

class FASTPATH_ACTION(enum.Enum):
	FASTPATH = 0x0 #Indicates that the PDU is a fast-path output PDU.
	X224 = 0x3 #Indicates the presence of a TPKT Header ([T123] section 8) initial version byte which indicates that the PDU is a slow-path output PDU (in this case the full value of the initial byte MUST be 0x03).

class FASTPATH_SEC(enum.IntFlag):
	NONE = 0x0
	SECURE_CHECKSUM = 0x1 #Indicates that the MAC signature for the PDU was generated using the "salted MAC generation" technique (section 5.3.6.1.1). If this bit is not set, then the standard technique was used (sections 2.2.8.1.1.2.2 and 2.2.8.1.1.2.3).
	ENCRYPTED = 0x2 #Indicates that the PDU contains an 8-byte MAC signature after the optional length2 field (that is, the dataSignature field is present), and the contents of the PDU are encrypted using the negotiated encryption package (sections 5.3.2 and 5.3.6).

class TS_FP_FIPS_INFO:
	def __init__(self):
		self.length:int = 16
		self.version:int = 1
		self.padlen:int = None 

	def to_bytes(self):
		t = self.length.to_bytes(2, byteorder='little', signed=False)
		t += self.version.to_bytes(1, byteorder='little', signed=False)
		t += self.padlen.to_bytes(1, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FP_FIPS_INFO.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FP_FIPS_INFO()
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.version = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		msg.padlen = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_FP_FIPS_INFO ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class FASTPATH_UPDATETYPE(enum.IntFlag):
	ORDERS = 0x0 #Indicates a Fast-Path Orders Update ([MS-RDPEGDI] section 2.2.2.2).
	BITMAP = 0x1 #Indicates a Fast-Path Bitmap Update (section 2.2.9.1.2.1.2).
	PALETTE = 0x2 #Indicates a Fast-Path Palette Update (section 2.2.9.1.2.1.1).
	SYNCHRONIZE = 0x3 #Indicates a Fast-Path Synchronize Update (section 2.2.9.1.2.1.3).
	SURFCMDS = 0x4 #Indicates a Fast-Path Surface Commands Update (section 2.2.9.1.2.1.10).
	PTR_NULL = 0x5 #Indicates a Fast-Path System Pointer Hidden Update (section 2.2.9.1.2.1.5).
	PTR_DEFAULT = 0x6 #Indicates a Fast-Path System Pointer Default Update (section 2.2.9.1.2.1.6).
	PTR_POSITION = 0x8 #Indicates a Fast-Path Pointer Position Update (section 2.2.9.1.2.1.4).
	COLOR = 0x9 #Indicates a Fast-Path Color Pointer Update (section 2.2.9.1.2.1.7).
	CACHED = 0xA #Indicates a Fast-Path Cached Pointer Update (section 2.2.9.1.2.1.9).
	POINTER = 0xB #Indicates a Fast-Path New Pointer Update (section 2.2.9.1.2.1.8).
	LARGE_POINTER = 0xC #Indicates a Fast-Path Large Pointer Update (section 2.2.9.1.2.1.11).

class FASTPATH_FRAGMENT(enum.Enum):
	SINGLE = 0x0 #The fast-path data in the updateData field is not part of a sequence of fragments.
	LAST = 0x1 #The fast-path data in the updateData field contains the last fragment in a sequence of fragments.
	FIRST = 0x2 #The fast-path data in the updateData field contains the first fragment in a sequence of fragments.
	NEXT = 0x3 #The fast-path data in the updateData field contains the second or subsequent fragment in a sequence of fragments.

class FASTPATH_OUTPUT_COMPRESSION(enum.IntFlag):
	NONE = 0x0
	USED = 0x2 #Indicates that the compressionFlags field is present. 

class TS_FP_UPDATE:
	def __init__(self):
		# HDR start
		self.updateCode: FASTPATH_UPDATETYPE = None
		self.fragmentation: FASTPATH_FRAGMENT = None
		self.compression: FASTPATH_OUTPUT_COMPRESSION = FASTPATH_OUTPUT_COMPRESSION.NONE
		# HDR end
		self.compressionFlags:int = 0
		self.size:int = None
		self.updateData:bytes = None

		# high level
		self.update = None

	def to_bytes(self):
		if self.updateData is not None:
			data = self.updateData
		elif self.update is not None:
			data = self.update.to_bytes()
		else:
			data = b''
		update_header = (
			self.updateCode.value
			| (self.fragmentation.value << 4)
			| (self.compression.value << 6)
		)
		t = update_header.to_bytes(1, byteorder='little', signed = False)
		if self.compression == FASTPATH_OUTPUT_COMPRESSION.USED:
			t += self.compressionFlags.to_bytes(1, byteorder='little', signed = False)
		t += len(data).to_bytes(2, byteorder='little', signed = False)
		t += data
		return t

	@staticmethod
	def from_bytes(bbuff: bytes, parse_update = True):
		buff = io.BytesIO(bbuff)
		msg = TS_FP_UPDATE.from_buffer(buff, parse_update=parse_update)
		if buff.read(1) != b'':
			raise ValueError('Trailing data after fast-path update')
		return msg

	@staticmethod
	def from_buffer(buff: io.BytesIO, parse_update = True):
		msg = TS_FP_UPDATE()
		update_header_raw = buff.read(1)
		if len(update_header_raw) != 1:
			raise ValueError('Truncated fast-path update header')
		updateHeader = update_header_raw[0]
		msg.updateCode = FASTPATH_UPDATETYPE(updateHeader & 0xF)
		msg.fragmentation = FASTPATH_FRAGMENT((updateHeader >> 4) & 3)
		compression_value = (updateHeader >> 6) & 3
		if compression_value not in (
			FASTPATH_OUTPUT_COMPRESSION.NONE.value,
			FASTPATH_OUTPUT_COMPRESSION.USED.value,
		):
			raise ValueError('Invalid fast-path output compression value')
		msg.compression = FASTPATH_OUTPUT_COMPRESSION(compression_value)
		if msg.compression == FASTPATH_OUTPUT_COMPRESSION.USED:
			compression_flags_raw = buff.read(1)
			if len(compression_flags_raw) != 1:
				raise ValueError('Truncated fast-path compression flags')
			msg.compressionFlags = compression_flags_raw[0]
		size_raw = buff.read(2)
		if len(size_raw) != 2:
			raise ValueError('Truncated fast-path update size')
		msg.size = int.from_bytes(size_raw, byteorder='little', signed = False)
		msg.updateData = buff.read(msg.size)
		if len(msg.updateData) != msg.size:
			raise ValueError('Truncated fast-path update data')
		if parse_update:
			if msg.fragmentation != FASTPATH_FRAGMENT.SINGLE:
				raise ValueError('Cannot decode a fragmented fast-path update before reassembly')
			msg.parse_update_data()
		return msg

	@staticmethod
	def list_from_bytes(bbuff: bytes):
		buff = io.BytesIO(bbuff)
		updates = []
		while buff.tell() < len(bbuff):
			updates.append(TS_FP_UPDATE.from_buffer(buff, parse_update=False))
		return updates

	def parse_update_data(self):
		if self.fragmentation != FASTPATH_FRAGMENT.SINGLE:
			raise ValueError('Cannot decode a fragmented fast-path update before reassembly')
		if self.compression == FASTPATH_OUTPUT_COMPRESSION.USED:
			raise NotImplementedError('Fast-path bulk compression is not implemented')
		ot = otype2obj.get(self.updateCode)
		if ot is not None:
			self.update = ot.from_bytes(self.updateData)
		return self.update

	def __repr__(self):
		t = '==== TS_FP_UPDATE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

otype2obj = {
	FASTPATH_UPDATETYPE.ORDERS : None, # TODO
	FASTPATH_UPDATETYPE.BITMAP : TS_UPDATE_BITMAP_DATA,
	FASTPATH_UPDATETYPE.PALETTE : TS_UPDATE_PALETTE_DATA,
	FASTPATH_UPDATETYPE.SYNCHRONIZE : None, # this is normal
	FASTPATH_UPDATETYPE.SURFCMDS : TS_SURFCMD,
	FASTPATH_UPDATETYPE.PTR_NULL : None, # this is normal
	FASTPATH_UPDATETYPE.PTR_DEFAULT : None, # this is normal
	FASTPATH_UPDATETYPE.PTR_POSITION : TS_POINTERPOSATTRIBUTE,
	FASTPATH_UPDATETYPE.COLOR : TS_FP_COLORPOINTERATTRIBUTE,
	FASTPATH_UPDATETYPE.CACHED : TS_FP_CACHEDPOINTERATTRIBUTE,
	FASTPATH_UPDATETYPE.POINTER : TS_FP_POINTERATTRIBUTE,
	FASTPATH_UPDATETYPE.LARGE_POINTER : TS_FP_LARGEPOINTERATTRIBUTE,
}

obj2otype = {v: k for k, v in otype2obj.items()}

class TS_FP_UPDATE_PDU:
	def __init__(self):
		self.action:FASTPATH_ACTION = 0
		self.reserved:int = 0
		self.flags:FASTPATH_SEC = None
		self.length1:int = None
		self.length2:int = None
		self.fipsInformation:TS_FP_FIPS_INFO = None #OPTIONAL!
		self.dataSignature:bytes = None
		self.fpOutputData:bytes = b''
		self.fpOutputUpdates:List[TS_FP_UPDATE] = []

	def to_bytes(self):
		raise NotImplementedError()

	@staticmethod
	def from_bytes(bbuff: bytes, with_fips = False):
		buff = io.BytesIO(bbuff)
		msg = TS_FP_UPDATE_PDU.from_buffer(buff, with_fips)
		if buff.read(1) != b'':
			raise ValueError('Trailing data after fast-path output PDU')
		return msg

	@staticmethod
	def from_buffer(buff: io.BytesIO, with_fips = False):
		msg = TS_FP_UPDATE_PDU()
		packet_start = buff.tell()
		header_raw = buff.read(1)
		if len(header_raw) != 1:
			raise ValueError('Truncated fast-path output PDU header')
		t = header_raw[0]
		msg.action = FASTPATH_ACTION(t & 3)
		msg.reserved = (t >> 2) & 15
		msg.flags = FASTPATH_SEC(t >> 6)

		length1_raw = buff.read(1)
		if len(length1_raw) != 1:
			raise ValueError('Truncated fast-path output PDU length')
		msg.length1 = length1_raw[0]
		length = msg.length1
		if msg.length1 >> 7 == 1:
			length2_raw = buff.read(1)
			if len(length2_raw) != 1:
				raise ValueError('Truncated fast-path output PDU length')
			msg.length2 = length2_raw[0]
			length = ((msg.length1 & 0x7f) << 8) | msg.length2
		if length < buff.tell() - packet_start:
			raise ValueError('Invalid fast-path output PDU length')

		if with_fips is True:
			msg.fipsInformation = TS_FP_FIPS_INFO.from_buffer(buff)
		if FASTPATH_SEC.ENCRYPTED in msg.flags or FASTPATH_SEC.SECURE_CHECKSUM in msg.flags:
			msg.dataSignature = buff.read(8)
			if len(msg.dataSignature) != 8:
				raise ValueError('Truncated fast-path output PDU signature')
		
		payload_length = length - (buff.tell() - packet_start)
		if payload_length < 0:
			raise ValueError('Invalid fast-path output PDU length')
		msg.fpOutputData = buff.read(payload_length)
		if len(msg.fpOutputData) != payload_length:
			raise ValueError('Truncated fast-path output PDU data')
		if FASTPATH_SEC.ENCRYPTED not in msg.flags:
			msg.fpOutputUpdates = TS_FP_UPDATE.list_from_bytes(msg.fpOutputData)

		return msg

	def __repr__(self):
		t = '==== TS_SHAREDATAHEADER ====\r\n'
		for k in self.__dict__:
			if k == 'fpOutputUpdates':
				value = self.__dict__[k][:100]
			elif isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k].name
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t