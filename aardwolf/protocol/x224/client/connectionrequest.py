import io
import enum

from aardwolf.protocol.x224.constants import TPDU_TYPE, NEG_FLAGS, SUPP_PROTOCOLS

class RDP_NEG_CORRELATION_INFO:
	def __init__(self):
		self.type:int = 6 #TYPE_RDP_CORRELATION_INFO
		self.flags:int = 0 #no flags defined
		self.length:int = 36
		self.correlationId:bytes = None
		self.reserved:bytes = None
		
	def to_bytes(self):
		t  = self.type.to_bytes(1, byteorder='little', signed = False)
		t += self.flags.value.to_bytes(1, byteorder='little', signed = False)
		t += self.length.to_bytes(2, byteorder='little', signed = False)
		t += self.correlationId
		t += self.reserved
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return RDP_NEG_CORRELATION_INFO.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = RDP_NEG_CORRELATION_INFO()
		msg.type = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.flags = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.correlationId = buff.read(16)
		msg.reserved = buff.read(16)
		return msg

	def __repr__(self):
		t = '==== RDP_NEG_CORRELATION_INFO ====\r\n'
		t += 'type :%s\r\n' % self.type
		t += 'flags :%s\r\n' % self.flags
		t += 'length :%s\r\n' % self.length
		t += 'correlationId :%s\r\n' % self.correlationId
		t += 'reserved :%s\r\n' % self.reserved
		return t

class RDP_NEG_REQ:
	def __init__(self):
		self.type = 1
		self.flags:NEG_FLAGS = None
		self.length:int = 8
		self.requestedProtocols:SUPP_PROTOCOLS = None
		
	def to_bytes(self):
		t  = self.type.to_bytes(1, byteorder='little', signed = False)
		t += self.flags.to_bytes(1, byteorder='little', signed = False)
		t += self.length.to_bytes(2, byteorder='little', signed = False)
		t += self.requestedProtocols.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return RDP_NEG_REQ.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = RDP_NEG_REQ()
		msg.type = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.flags = NEG_FLAGS(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.requestedProtocols = SUPP_PROTOCOLS(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== RDP_NEG_REQ ====\r\n'
		t += 'type :%s\r\n' % self.type
		t += 'flags :%s\r\n' % self.flags
		t += 'length :%s\r\n' % self.length
		t += 'requestedProtocols :%s\r\n' % self.requestedProtocols
		return t

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/18a27ef9-6f9a-4501-b000-94b1fe3c2c10
class ConnectionRequest:
	def __init__(self):
		# fixed
		self.length = None
		self.CR = TPDU_TYPE.CONNECTION_REQUEST
		self.CDT = 0
		self.DST_REF = 0
		self.SRC_REF = None
		self.CLASS_OPT = 0
		self.cookie = None #optional!
		# variable
		self.rdpNegReq = None #optional!
		self.rdpCorrelationInfo = None #optional!
		
	def to_bytes(self):
		t = (self.CR.value << 4 | self.CDT).to_bytes(1, byteorder='big', signed = False)
		t += self.DST_REF.to_bytes(2, byteorder='big', signed = False)
		t += self.SRC_REF.to_bytes(2, byteorder='big', signed = False)
		t += self.CLASS_OPT.to_bytes(1, byteorder='big', signed = False)
		if self.cookie is not None:
			t += self.cookie
		if self.rdpNegReq is not None:
			t += self.rdpNegReq.to_bytes()
		
		t = len(t).to_bytes(1, byteorder='big', signed = False) + t
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return ConnectionRequest.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		fixlen = int.from_bytes(buff.read(1), byteorder='big', signed = False)
		tbuff = io.BytesIO(buff.read(fixlen-1))
		msg = ConnectionRequest()
		msg.length = fixlen
		t = int.from_bytes(tbuff.read(1), byteorder='big', signed = False)
		msg.CR = TPDU_TYPE(t >> 4)
		msg.CDT = t & 0xF
		msg.DST_REF = int.from_bytes(tbuff.read(2), byteorder='big', signed = False)
		msg.SRC_REF = int.from_bytes(tbuff.read(2), byteorder='big', signed = False)
		msg.CLASS_OPT = int.from_bytes(tbuff.read(1), byteorder='big', signed = False)
		rest = tbuff.read()
		m = rest.find(b'\r\n')
		if m != -1:
			msg.cookie = rest[:m+2]
			rest = rest[m+2:]
		if len(rest) > 0:
			msg.rdpNegReq = RDP_NEG_REQ.from_bytes(rest[:8])
			if NEG_FLAGS.CORRELATION_INFO_PRESENT in msg.rdpNegReq.flags:
				msg.rdpCorrelationInfo = RDP_NEG_CORRELATION_INFO.from_bytes(rest[8:])

		return msg

	def __repr__(self):
		t = '==== ConnectionRequest ====\r\n'
		t += 'length :%s\r\n' % self.length
		t += 'CR :%s\r\n' % self.CR
		t += 'CDT :%s\r\n' % self.CDT
		t += 'DST_REF :%s\r\n' % self.DST_REF
		t += 'DST_REF :%s\r\n' % self.DST_REF
		t += 'CLASS_OPT :%s\r\n' % self.CLASS_OPT
		t += 'cookie :%s\r\n' % self.cookie
		t += 'rdpNegReq: %s' % self.rdpNegReq
		t += 'rdpCorrelationInfo: %s' % self.rdpCorrelationInfo
		return t
