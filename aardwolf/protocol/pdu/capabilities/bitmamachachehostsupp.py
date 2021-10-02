import io
import enum

class TS_BITMAPCACHE_HOSTSUPPORT_CAPABILITYSET:
	def __init__(self):
		self.cacheVersion:int = 1
		self.pad:bytes = b'\x00' * 3

	def to_bytes(self):
		t = self.cacheVersion.to_bytes(1, byteorder='little', signed = False)
		t += self.pad
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_BITMAPCACHE_HOSTSUPPORT_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_BITMAPCACHE_HOSTSUPPORT_CAPABILITYSET()
		msg.cacheVersion = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.pad = buff.read(3)
		return msg

	def __repr__(self):
		t = '==== TS_BITMAPCACHE_HOSTSUPPORT_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t