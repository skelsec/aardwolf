import io
import enum

class TS_BITMAPCACHE_CAPABILITYSET:
	def __init__(self):
		self.pad:bytes = b'\x00' * 24
		self.Cache0Entries:int = 0
		self.Cache0MaximumCellSize:int = 0
		self.Cache1Entries:int = 0
		self.Cache1MaximumCellSize:int = 0
		self.Cache2Entries:int = 0
		self.Cache2MaximumCellSize:int = 0

	def to_bytes(self):
		t  = self.pad
		t += self.Cache0Entries.to_bytes(2, byteorder='little', signed = False)
		t += self.Cache0MaximumCellSize.to_bytes(2, byteorder='little', signed = False)
		t += self.Cache1Entries.to_bytes(2, byteorder='little', signed = False)
		t += self.Cache1MaximumCellSize.to_bytes(2, byteorder='little', signed = False)
		t += self.Cache2Entries.to_bytes(2, byteorder='little', signed = False)
		t += self.Cache2MaximumCellSize.to_bytes(32, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCACHE_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCACHE_CAPABILITYSET()
		msg.pad = buff.read(24)
		msg.Cache0Entries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.Cache0MaximumCellSize = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.Cache1Entries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.Cache2Entries = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.Cache2MaximumCellSize = int.from_bytes(buff.read(2), byteorder='little', signed = False)		
		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCACHE_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t