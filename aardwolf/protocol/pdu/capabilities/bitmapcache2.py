import io
import enum

class CacheFlag2(enum.IntFlag):
	PERSISTENT_KEYS_EXPECTED_FLAG = 0x0001 #Indicates that the client will send a Persistent Key List PDU during the Connection Finalization phase of the RDP Connection Sequence (see section 1.3.1.1 for an overview of the RDP Connection Sequence phases).
	ALLOW_CACHE_WAITING_LIST_FLAG = 0x0002 #Indicates that the client supports a cache waiting list. If a waiting list is supported, new bitmaps are cached on the second hit rather than the first (that is, a bitmap is sent twice before it is cached).

class TS_BITMAPCACHE_CELL_CACHE_INFO:
	def __init__(self):
		self.NumEntries:int = None
		self.persistent:bool = None

	def to_bytes(self):
		temp = self.NumEntries << 1
		temp += int(self.persistent)
		t  = temp.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCACHE_CELL_CACHE_INFO.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCACHE_CELL_CACHE_INFO()
		t = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.NumEntries = t >> 1
		msg.persistent = bool(t & 1)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCACHE_CELL_CACHE_INFO ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_BITMAPCACHE_CAPABILITYSET_REV2:
	def __init__(self):
		self.CacheFlags:CacheFlag2 = None
		self.Pad2:bytes = b'\x00' * 1
		self.NumCellCaches:int = None
		self.BitmapCache0CellInfo:TS_BITMAPCACHE_CELL_CACHE_INFO = None
		self.BitmapCache1CellInfo:TS_BITMAPCACHE_CELL_CACHE_INFO = None
		self.BitmapCache2CellInfo:TS_BITMAPCACHE_CELL_CACHE_INFO = None
		self.BitmapCache3CellInfo:TS_BITMAPCACHE_CELL_CACHE_INFO = None
		self.BitmapCache4CellInfo:TS_BITMAPCACHE_CELL_CACHE_INFO = None
		self.Pad3:bytes = b'\x00' * 12

	def to_bytes(self):
		t  = self.CacheFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.Pad2
		t += self.NumCellCaches.to_bytes(1, byteorder='little', signed = False)
		t += self.BitmapCache0CellInfo.to_bytes()
		t += self.BitmapCache1CellInfo.to_bytes()
		t += self.BitmapCache2CellInfo.to_bytes()
		t += self.BitmapCache3CellInfo.to_bytes()
		t += self.BitmapCache4CellInfo.to_bytes()
		t += self.Pad3
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCACHE_CAPABILITYSET_REV2.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCACHE_CAPABILITYSET_REV2()
		msg.CacheFlags = CacheFlag2(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.Pad2 = buff.read(1)
		msg.NumCellCaches = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.BitmapCache0CellInfo = TS_BITMAPCACHE_CELL_CACHE_INFO.from_buffer(buff)
		msg.BitmapCache1CellInfo = TS_BITMAPCACHE_CELL_CACHE_INFO.from_buffer(buff)
		msg.BitmapCache2CellInfo = TS_BITMAPCACHE_CELL_CACHE_INFO.from_buffer(buff)
		msg.BitmapCache3CellInfo = TS_BITMAPCACHE_CELL_CACHE_INFO.from_buffer(buff)
		msg.BitmapCache4CellInfo = TS_BITMAPCACHE_CELL_CACHE_INFO.from_buffer(buff)
		
		msg.Pad3 = buff.read(12)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCACHE_CAPABILITYSET_REV2 ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t