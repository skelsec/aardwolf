
import io
from aardwolf.protocol.x224.constants import TPDU_TYPE

# https://www.itu.int/rec/T-REC-X.224-199511-I/en (13.7)
class Data:
	def __init__(self):
		# fixed
		self.length = None #here it's always 2
		self.DT:TPDU_TYPE = TPDU_TYPE.DATA
		self.ROA:bool = False #indicates we want ACK for this packet
		self.TPDU_NR = b'\x80'
		self.data = None #remaining data which is not indicated by the length field (most of the data)
		
	def to_bytes(self):
		t = (self.DT.value << 4 | (int(self.ROA) & 0b0001)).to_bytes(1, byteorder='big', signed = False)
		t += self.TPDU_NR
		t = b'\x02' + t + self.data
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return Data.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		# be careful, this consumes the enitre buffer!
		msg = Data()
		msg.length = int.from_bytes(buff.read(1), byteorder='big', signed = False)
		t = buff.read(msg.length)
		msg.DT = TPDU_TYPE(t[0] >> 4)
		msg.ROA = bool(t[0] & 0b0001)
		msg.TPDU_NR = t[1]
		msg.data = buff.read()
		return msg

	def __repr__(self):
		t = '==== Data ====\r\n'
		t += 'length :%s\r\n' % self.length
		t += 'DT :%s\r\n' % self.DT
		t += 'ROA :%s\r\n' % self.ROA
		t += 'data :%s\r\n' % self.data
		return t