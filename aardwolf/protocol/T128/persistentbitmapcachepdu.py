import io
import enum
from typing import List
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY:
	def __init__(self):
		self.Key1:int = 0
		self.Key2:int = 0

	def to_bytes(self):
		t = self.Key1.to_bytes(4, byteorder='little', signed = False)
		t += self.Key2.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY()
		msg.Key1 = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.Key2 = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_BITMAPCACHE_PERSISTENT_LIST_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.numEntriesCache0:int = 0
		self.numEntriesCache1:int = 0
		self.numEntriesCache2:int = 0
		self.numEntriesCache3:int = 0
		self.numEntriesCache4:int = 0
		self.totalEntriesCache0:int = 0
		self.totalEntriesCache1:int = 0
		self.totalEntriesCache2:int = 0
		self.totalEntriesCache3:int = 0
		self.totalEntriesCache4:int = 0
		self.bBitMask:int = 0
		self.Pad2:int = 0
		self.Pad3:int = 0
		self.entries:List[TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY] = 0


	def to_bytes(self):
		#t  = self.shareDataHeader.to_bytes()
		t = self.numberEntries.to_bytes(2, byteorder='little', signed = False)
		t += self.totalNumEntries.to_bytes(2, byteorder='little', signed = False)
		t += self.mapFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.entrySize.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCACHE_PERSISTENT_LIST_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCACHE_PERSISTENT_LIST_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.numEntriesCache0 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.numEntriesCache1 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.numEntriesCache2 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.numEntriesCache3 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.numEntriesCache4 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalEntriesCache0 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalEntriesCache1 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalEntriesCache2 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalEntriesCache3 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.totalEntriesCache4 = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.bBitMask:int = 0
		msg.Pad2:int = 0
		msg.Pad3:int = 0
		msg.entries:List[TS_BITMAPCACHE_PERSISTENT_LIST_ENTRY] = 0



		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCACHE_PERSISTENT_LIST_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t