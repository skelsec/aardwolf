import io
import enum
from typing import List

class TS_PALETTE_ENTRY:
	def __init__(self):
		self.red:int = None
		self.green:int = None
		self.blue:int = None

	def to_bytes(self):
		t = self.red.to_bytes(1, byteorder='little', signed=False)
		t += self.green.to_bytes(1, byteorder='little', signed=False)
		t += self.blue.to_bytes(1, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_PALETTE_ENTRY.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_PALETTE_ENTRY()
		msg.red = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		msg.green = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		msg.blue = int.from_bytes(buff.read(1), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_PALETTE_ENTRY ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_UPDATE_PALETTE_DATA:
	def __init__(self):
		self.updateType:int = 0x0002
		self.pad2Octets:bytes = b'\x00\x00'
		self.numberColors:int = None
		self.paletteEntries:List[TS_PALETTE_ENTRY] = []

	def to_bytes(self):
		t = self.updateType.to_bytes(2, byteorder='little', signed=False)
		t += self.pad2Octets
		t += len(self.paletteEntries).to_bytes(2, byteorder='little', signed=False)
		for pal in self.paletteEntries:
			t += pal.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UPDATE_PALETTE_DATA.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UPDATE_PALETTE_DATA()
		msg.updateType = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.pad2Octets = buff.read(2)
		msg.numberColors = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		for _ in range(msg.numberColors):
			msg.paletteEntries.append(TS_PALETTE_ENTRY.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== TS_UPDATE_PALETTE_DATA ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

