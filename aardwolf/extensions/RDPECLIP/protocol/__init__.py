import io
import enum

from aardwolf.extensions.RDPECLIP.protocol.clipboardcapabilities import CLIPRDR_CAPS
from aardwolf.extensions.RDPECLIP.protocol.clienttemporarydirectory import CLIPRDR_TEMP_DIRECTORY
from aardwolf.extensions.RDPECLIP.protocol.lockclipboarddata import CLIPRDR_LOCK_CLIPDATA
from aardwolf.extensions.RDPECLIP.protocol.unlockclipboarddata import CLIPRDR_UNLOCK_CLIPDATA
from aardwolf.extensions.RDPECLIP.protocol.formatdatarequest import CLIPRDR_FORMAT_DATA_REQUEST
from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPRDR_FORMAT_LIST
from aardwolf.extensions.RDPECLIP.protocol.formatdataresponse import CLIPRDR_FORMAT_DATA_RESPONSE
from aardwolf.extensions.RDPECLIP.protocol.filecontentsrequest import CLIPRDR_FILECONTENTS_REQUEST
from aardwolf.extensions.RDPECLIP.protocol.filecontentsresponse import CLIPRDR_FILECONTENTS_RESPONSE


class CB_FLAG(enum.IntFlag):
	CB_RESPONSE_OK = 0x0001 #Used by the Format List Response PDU, Format Data Response PDU, and File Contents Response PDU to indicate that the associated request Format List PDU, Format Data Request PDU, and File Contents Request PDU were processed successfully.
	CB_RESPONSE_FAIL = 0x0002 #Used by the Format List Response PDU, Format Data Response PDU, and File Contents Response PDU to indicate that the associated Format List PDU, Format Data Request PDU, and File Contents Request PDU were not processed successfully.
	CB_ASCII_NAMES = 0x0004 #Used by the Short Format Name variant of the Format List Response PDU to indicate that the format names are in ASCII 8.

class CB_TYPE(enum.Enum):
	CB_MONITOR_READY = 0x0001 #Monitor Ready PDU
	CB_FORMAT_LIST = 0x0002 #Format List PDU
	CB_FORMAT_LIST_RESPONSE = 0x0003 #Format List Response PDU
	CB_FORMAT_DATA_REQUEST = 0x0004 #Format Data Request PDU
	CB_FORMAT_DATA_RESPONSE = 0x0005 #Format Data Response PDU
	CB_TEMP_DIRECTORY = 0x0006 #Temporary Directory PDU
	CB_CLIP_CAPS = 0x0007 #Clipboard Capabilities PDU
	CB_FILECONTENTS_REQUEST = 0x0008 #File Contents Request PDU
	CB_FILECONTENTS_RESPONSE = 0x0009 #File Contents Response PDU
	CB_LOCK_CLIPDATA = 0x000A #Lock Clipboard Data PDU
	CB_UNLOCK_CLIPDATA = 0x000B #Unlock Clipboard Data PDU

class CLIPRDR_HEADER:
	def __init__(self):
		self.msgType:CB_TYPE = None
		self.msgFlags:CB_FLAG = None
		self.dataLen:int = None

	def to_bytes(self):
		t = self.msgType.value.to_bytes(2, byteorder='little', signed = False)
		t += self.msgFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.dataLen.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_HEADER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_HEADER()
		msg.msgType = CB_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.msgFlags = CB_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.dataLen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	@staticmethod
	def parse_packet_bytes(bbuff: bytes):
		return CLIPRDR_HEADER.parse_packet_buffer(io.BytesIO(bbuff))
	
	@staticmethod
	def parse_packet_buffer(buff: bytes):
		hdr = CLIPRDR_HEADER.from_buffer(buff)
		data = buff.read(hdr.dataLen)
		if type2obj[hdr.msgType] is None:
			return hdr, None
		return hdr, type2obj[hdr.msgType].from_bytes(data)
	
	@staticmethod
	def serialize_packet(msgType:CB_TYPE, msgFlags:CB_FLAG, obj):
		data = obj
		if obj is not None:
			if isinstance(obj, bytes):
				data = obj
			else:
				data = obj.to_bytes()
		hdr = CLIPRDR_HEADER()
		hdr.msgType = msgType
		hdr.msgFlags = msgFlags
		if obj is not None:
			hdr.dataLen = len(data)
			return hdr.to_bytes() + data
		else:
			hdr.dataLen = 0
			return hdr.to_bytes()
		
		


	def __repr__(self):
		t = '==== CLIPRDR_HEADER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

# not all object here are parsable automatically without outside information given to the respective parser!
type2obj = {
	CB_TYPE.CB_MONITOR_READY : None, #normal
	CB_TYPE.CB_FORMAT_LIST : CLIPRDR_FORMAT_LIST,
	CB_TYPE.CB_FORMAT_LIST_RESPONSE : None, #normal
	CB_TYPE.CB_FORMAT_DATA_REQUEST : CLIPRDR_FORMAT_DATA_REQUEST,
	CB_TYPE.CB_FORMAT_DATA_RESPONSE : CLIPRDR_FORMAT_DATA_RESPONSE, 
	CB_TYPE.CB_TEMP_DIRECTORY : CLIPRDR_TEMP_DIRECTORY,
	CB_TYPE.CB_CLIP_CAPS : CLIPRDR_CAPS,
	CB_TYPE.CB_FILECONTENTS_REQUEST : CLIPRDR_FILECONTENTS_REQUEST,
	CB_TYPE.CB_FILECONTENTS_RESPONSE : CLIPRDR_FILECONTENTS_RESPONSE,
	CB_TYPE.CB_LOCK_CLIPDATA : CLIPRDR_LOCK_CLIPDATA,
	CB_TYPE.CB_UNLOCK_CLIPDATA : CLIPRDR_UNLOCK_CLIPDATA,
}
