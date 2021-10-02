import io
import enum
from typing import Any, List

class CAPSTYPE(enum.Enum):
	GENERAL = 0x0001 #General Capability Set

class CB_CAPS_VERSION(enum.Enum):
	VERSION_1 = 0x00000001 #Version 1
	VERSION_2 = 0x00000002 #Version 2

class CB_GENERAL_FALGS(enum.IntFlag):
	USE_LONG_FORMAT_NAMES = 0x00000002 #The Long Format Name variant of the Format List PDU is supported for exchanging updated format names. If this flag is not set, the Short Format Name variant MUST be used. If this flag is set by both protocol endpoints, then the Long Format Name variant MUST be used.
	STREAM_FILECLIP_ENABLED = 0x00000004 #File copy and paste using stream-based operations are supported using the File Contents Request PDU and File Contents Response PDU.
	FILECLIP_NO_FILE_PATHS = 0x00000008 #Indicates that any description of files to copy and paste MUST NOT include the source path of the files.
	CAN_LOCK_CLIPDATA = 0x00000010 #Locking and unlocking of File Stream data on the clipboard is supported using the Lock Clipboard Data PDU and Unlock Clipboard Data PDU.
	HUGE_FILE_SUPPORT_ENABLED = 0x00000020 #Indicates support for transferring files that are larger than 4,294,967,295 bytes in size. If this flag is not set, then only files of size less than or equal to 4,294,967,295 bytes can be exchanged using the File Contents Request PDU and File Contents Response PDU.

class CLIPRDR_GENERAL_CAPABILITY:
	def __init__(self):
		self.capabilitySetType:CAPSTYPE = CAPSTYPE.GENERAL
		self.lengthCapability:int = 12
		self.version:CB_CAPS_VERSION = CB_CAPS_VERSION.VERSION_2
		self.generalFlags:CB_GENERAL_FALGS = 0

	def to_bytes(self):
		t = self.capabilitySetType.value.to_bytes(2, byteorder='little', signed = False)
		t += self.lengthCapability.to_bytes(2, byteorder='little', signed = False)
		t += self.version.value.to_bytes(4, byteorder='little', signed = False)
		t += self.generalFlags.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_GENERAL_CAPABILITY.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_GENERAL_CAPABILITY()
		msg.capabilitySetType = CAPSTYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.lengthCapability = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.version = CB_CAPS_VERSION(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.generalFlags = CB_GENERAL_FALGS(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_GENERAL_CAPABILITY ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


class CLIPRDR_CAPS:
	def __init__(self):
		self.cCapabilitiesSets:int = None
		self.pad1:bytes = b'\x00\x00'
		self.capabilitySets:List[Any] = []


	def to_bytes(self):
		t = len(self.capabilitySets).to_bytes(2, byteorder='little', signed = False)
		t += self.pad1
		for cap in self.capabilitySets:
			t += cap.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_CAPS.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_CAPS()
		msg.cCapabilitiesSets = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.pad1 = buff.read(2)
		for _ in range(msg.cCapabilitiesSets):
			obj = capstype2cap[CAPSTYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))]
			buff.seek(-2,1)
			msg.capabilitySets.append(obj.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_CAPS ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

capstype2cap = {
	CAPSTYPE.GENERAL : CLIPRDR_GENERAL_CAPABILITY
}