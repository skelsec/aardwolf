import io
from aardwolf.protocol.x224.constants import TPDU_TYPE, RESP_FLAGS, SUPP_PROTOCOLS, FAIL_CODE


class RDP_NEG_FAILURE:
	def __init__(self):
		self.type:int = 3 #RDP_NEG_FAILURE
		self.flags:int = 0
		self.length:int = 8
		self.failureCode:FAIL_CODE = None
		
	def to_bytes(self):
		t  = self.type.to_bytes(1, byteorder='little', signed = False)
		t += self.flags.to_bytes(1, byteorder='little', signed = False)
		t += self.length.to_bytes(2, byteorder='little', signed = False)
		t += self.failureCode.value.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return RDP_NEG_FAILURE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = RDP_NEG_FAILURE()
		msg.type = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.flags = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.failureCode = FAIL_CODE(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== RDP_NEG_FAILURE ====\r\n'
		t += 'type :%s\r\n' % self.type
		t += 'flags :%s\r\n' % self.flags
		t += 'length :%s\r\n' % self.length
		t += 'failureCode :%s\r\n' % self.failureCode.name
		return t

class RDP_NEG_RSP:
	def __init__(self):
		self.type:int = 2 #TYPE_RDP_NEG_RSP
		self.flags:RESP_FLAGS = 0
		self.length:int = 8
		self.selectedProtocol:SUPP_PROTOCOLS = None
		
	def to_bytes(self):
		t  = self.type.to_bytes(1, byteorder='little', signed = False)
		t += self.flags.to_bytes(1, byteorder='little', signed = False)
		t += self.length.to_bytes(2, byteorder='little', signed = False)
		t += self.selectedProtocol.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return RDP_NEG_RSP.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = RDP_NEG_RSP()
		msg.type = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.flags = RESP_FLAGS(int.from_bytes(buff.read(1), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.selectedProtocol = SUPP_PROTOCOLS(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== RDP_NEG_RSP ====\r\n'
		t += 'type :%s\r\n' % self.type
		t += 'flags :%s\r\n' % self.flags
		t += 'length :%s\r\n' % self.length
		t += 'selectedProtocol :%s\r\n' % self.selectedProtocol
		return t

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/18a27ef9-6f9a-4501-b000-94b1fe3c2c10
class ConnectionConfirm:
	def __init__(self):
		# fixed
		self.length = None
		self.CR = TPDU_TYPE.CONNECTION_CONFIRM
		self.CDT = 0
		self.DST_REF = 0
		self.SRC_REF = None
		self.CLASS_OPT = 0
		self.cookie = None #optional!
		# variable
		self.rdpNegData = None #optional!
		
	def to_bytes(self):
		t = (self.CR.value << 4 | self.CDT).to_bytes(1, byteorder='big', signed = False)
		t += self.DST_REF.to_bytes(2, byteorder='big', signed = False)
		t += self.SRC_REF.to_bytes(2, byteorder='big', signed = False)
		t += self.CLASS_OPT.to_bytes(1, byteorder='big', signed = False)
		if self.rdpNegData is not None:
			t += self.rdpNegData.to_bytes()
		
		t = len(t).to_bytes(1, byteorder='big', signed = False) + t
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return ConnectionConfirm.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		fixlen = int.from_bytes(buff.read(1), byteorder='big', signed = False)
		tbuff = io.BytesIO(buff.read(fixlen-1))
		msg = ConnectionConfirm()
		msg.length = fixlen
		t = int.from_bytes(tbuff.read(1), byteorder='big', signed = False)
		msg.CR = TPDU_TYPE(t >> 4)
		msg.CDT = t & 0xF
		msg.DST_REF = int.from_bytes(tbuff.read(2), byteorder='big', signed = False)
		msg.SRC_REF = int.from_bytes(tbuff.read(2), byteorder='big', signed = False)
		msg.CLASS_OPT = int.from_bytes(tbuff.read(1), byteorder='big', signed = False)
		rest = tbuff.read()
		if len(rest) > 0:
			if rest[0] == 3:
				msg.rdpNegData = RDP_NEG_FAILURE.from_bytes(rest[:8])
			elif rest[0] == 2:
				msg.rdpNegData = RDP_NEG_RSP.from_bytes(rest[:8])

		return msg

	def __repr__(self):
		t = '==== ConnectionRequest ====\r\n'
		t += 'length :%s\r\n' % self.length
		t += 'CR :%s\r\n' % self.CR
		t += 'CDT :%s\r\n' % self.CDT
		t += 'DST_REF :%s\r\n' % self.DST_REF
		t += 'DST_REF :%s\r\n' % self.DST_REF
		t += 'CLASS_OPT :%s\r\n' % self.CLASS_OPT
		t += 'rdpNegData: %s' % self.rdpNegData
		return t
