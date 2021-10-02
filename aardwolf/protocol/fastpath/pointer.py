import io
import enum
from typing import List

class TS_POINT16:
	def __init__(self):
		self.xPos:int = None
		self.yPos:int = None

	def to_bytes(self):
		t = self.xPos.to_bytes(2, byteorder='little', signed=False)
		t += self.yPos.to_bytes(2, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_POINT16.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_POINT16()
		msg.xPos = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.yPos = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_POINT16 ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_FP_CACHEDPOINTERATTRIBUTE:
	def __init__(self):
		self.cachedPointerUpdateData:int = None 

	def to_bytes(self):
		t = self.cachedPointerUpdateData.to_bytes(2, byteorder='little', signed=False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FP_CACHEDPOINTERATTRIBUTE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FP_CACHEDPOINTERATTRIBUTE()
		msg.cachedPointerUpdateData = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		return msg

	def __repr__(self):
		t = '==== TS_FP_CACHEDPOINTERATTRIBUTE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_FP_POINTERATTRIBUTE:
	def __init__(self):
		self.xorBpp:int = None 
		self.colorPtrAttr:TS_FP_COLORPOINTERATTRIBUTE = None 

	def to_bytes(self):
		t = self.xorBpp.to_bytes(2, byteorder='little', signed=False)
		t += self.colorPtrAttr.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FP_POINTERATTRIBUTE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FP_POINTERATTRIBUTE()
		msg.xorBpp = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.colorPtrAttr = TS_FP_COLORPOINTERATTRIBUTE.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_FP_POINTERATTRIBUTE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_FP_LARGEPOINTERATTRIBUTE:
	def __init__(self):
		self.xorBpp:int = None
		self.cacheIndex:int = None
		self.hotSpot:TS_POINT16 = None
		self.width:int = None
		self.height:int = None
		self.lengthAndMask:int = None
		self.lengthXorMask:int = None
		self.xorMaskData:bytes = None
		self.andMaskData:bytes = None
		self.pad: bytes = None

	def to_bytes(self):
		t = self.xorBpp.to_bytes(2, byteorder='little', signed=False)
		t += self.cacheIndex.to_bytes(2, byteorder='little', signed=False)
		t += self.hotSpot.to_bytes()
		t += self.width.to_bytes(2, byteorder='little', signed=False)
		t += self.height.to_bytes(2, byteorder='little', signed=False)
		t += len(self.andMaskData).to_bytes(4, byteorder='little', signed=False)
		t += len(self.xorMaskData).to_bytes(4, byteorder='little', signed=False)
		t += self.xorMaskData
		t += self.andMaskData
		if len(t) % 2 != 0:
			t += b'\x00'
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FP_LARGEPOINTERATTRIBUTE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FP_LARGEPOINTERATTRIBUTE()
		msg.xorBpp = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.cacheIndex = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.hotSpot = TS_POINT16.from_buffer(buff)
		msg.width = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.height = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.lengthAndMask = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		msg.lengthXorMask = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		msg.xorMaskData = buff.read(msg.lengthAndMask)
		msg.andMaskData = buff.read(msg.lengthXorMask)
		msg.pad = buff.read(1)
		return msg

	def __repr__(self):
		t = '==== TS_FP_LARGEPOINTERATTRIBUTE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_FP_COLORPOINTERATTRIBUTE:
	def __init__(self):
		self.cacheIndex:int = None
		self.hotSpot:TS_POINT16 = None
		self.width:int = None
		self.height:int = None
		self.lengthAndMask:int = None
		self.lengthXorMask:int = None
		self.xorMaskData:bytes = None
		self.andMaskData:bytes = None
		self.pad: bytes = None

	def to_bytes(self):
		t = self.cacheIndex.to_bytes(2, byteorder='little', signed=False)
		t += self.hotSpot.to_bytes()
		t += self.width.to_bytes(2, byteorder='little', signed=False)
		t += self.height.to_bytes(2, byteorder='little', signed=False)
		t += len(self.andMaskData).to_bytes(2, byteorder='little', signed=False)
		t += len(self.xorMaskData).to_bytes(2, byteorder='little', signed=False)
		t += self.xorMaskData
		t += self.andMaskData
		if len(t) % 2 != 0:
			t += b'\x00'
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_FP_COLORPOINTERATTRIBUTE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_FP_COLORPOINTERATTRIBUTE()
		msg.cacheIndex = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.hotSpot = TS_POINT16.from_buffer(buff)
		msg.width = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.height = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.lengthAndMask = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.lengthXorMask = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		msg.xorMaskData = buff.read(msg.lengthAndMask)
		msg.andMaskData = buff.read(msg.lengthXorMask)
		msg.pad = buff.read(1)
		return msg

	def __repr__(self):
		t = '==== TS_FP_COLORPOINTERATTRIBUTE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


class TS_POINTERPOSATTRIBUTE:
	def __init__(self):
		self.position:TS_POINT16 = None

	def to_bytes(self):
		t = self.position.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_POINTERPOSATTRIBUTE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_POINTERPOSATTRIBUTE()
		msg.position = TS_POINT16.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_POINTERPOSATTRIBUTE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

