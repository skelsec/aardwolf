

import io

# https://datatracker.ietf.org/doc/html/rfc2126#section-4.3
class TPKT:
	def __init__(self):
		self.version = 3
		self.reserved = 0
		self.length = None
		self.tpdu = None
		
	def to_bytes(self):
		t  = self.version.to_bytes(1, byteorder='big', signed = False)
		t += self.reserved.to_bytes(1, byteorder='big', signed = False)
		t += (len(self.tpdu)+4).to_bytes(2, byteorder='big', signed = False)
		t += self.tpdu
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TPKT.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TPKT()
		msg.version = int.from_bytes(buff.read(1), byteorder='big', signed=False)
		msg.reserved = int.from_bytes(buff.read(1), byteorder='big', signed=False)
		msg.length = int.from_bytes(buff.read(2), byteorder='big', signed=False)
		msg.tpdu = buff.read(msg.length-4)
		return msg

	def __repr__(self):
		t = '==== TPKT ====\r\n'
		t += 'version %s\r\n' % self.version
		t += 'reserved %s\r\n' % self.reserved
		t += 'length %s\r\n' % self.length
		t += 'tpdu %s\r\n' % self.tpdu
		return t