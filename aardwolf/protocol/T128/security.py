import enum
import io

class SEC_HDR_FLAG(enum.IntFlag):
	EXCHANGE_PKT = 0x0001 #Indicates that the packet is a Security Exchange PDU (section 2.2.1.10). This packet type is sent from client to server only. The client only sends this packet if it will be encrypting further communication and Standard RDP Security mechanisms (section 5.3) are in effect.
	TRANSPORT_REQ = 0x0002 #Indicates that the packet is an Initiate Multitransport Request PDU (section 2.2.15.1). This flag MUST NOT be present if the PDU containing the security header is being sent from client to server. This flag MUST NOT be present if the PDU containing the security header is not being sent on the MCS message channel. The ID of the message channel is specified in the Server Message Channel Data (section 2.2.1.4.5).
	TRANSPORT_RSP = 0x0004 #Indicates that the packet is an Initiate Multitransport Response PDU (section 2.2.15.2). This flag MUST NOT be present if the PDU containing the security header is being sent from server to client. This flag MUST NOT be present if the PDU containing the security header is not being sent on the MCS message channel. The ID of the message channel is specified in the Server Message Channel Data (section 2.2.1.4.5).
	ENCRYPT = 0x0008 #Indicates that the packet is encrypted.
	RESET_SEQNO = 0x0010 #This flag is not processed by any RDP clients or servers and MUST be ignored.
	IGNORE_SEQNO = 0x0020 #This flag is not processed by any RDP clients or servers and MUST be ignored.
	INFO_PKT = 0x0040 #Indicates that the packet is a Client Info PDU (section 2.2.1.11). This packet type is sent from client to server only. If Standard RDP Security mechanisms are in effect, then this packet MUST also be encrypted.
	LICENSE_PKT = 0x0080 #Indicates that the packet is a Licensing PDU (section 2.2.1.12).
	LICENSE_ENCRYPT_CS = 0x0200 #Indicates to the client that the server is capable of processing encrypted licensing packets. It is sent by the server together with any licensing PDUs (section 2.2.1.12).
	LICENSE_ENCRYPT_SC = 0x0200 #Indicates to the server that the client is capable of processing encrypted licensing packets. It is sent by the client together with the SEC_EXCHANGE_PKT flag when sending a Security Exchange PDU (section 2.2.1.10).
	REDIRECTION_PKT = 0x0400 # Indicates that the packet is a Standard Security Server Redirection PDU (section 2.2.13.2.1) and that the PDU is encrypted.
	SECURE_CHECKSUM = 0x0800 #Indicates that the MAC for the PDU was generated using the "salted MAC generation" technique (section 5.3.6.1.1). If this flag is not present, then the standard technique was used (sections 2.2.8.1.1.2.2 and 2.2.8.1.1.2.3).
	AUTODETECT_REQ = 0x1000 #Indicates that the packet is an Auto-Detect Request PDU (section 2.2.14.3). This flag MUST NOT be present if the PDU containing the security header is being sent from client to server This flag MUST NOT be present if the PDU containing the security header is not being sent on the MCS message channel. The ID of the message channel is specified in the Server Message Channel Data (section 2.2.1.4.5).
	AUTODETECT_RSP = 0x2000 # Indicates that the packet is an Auto-Detect Response PDU (section 2.2.14.4). This flag MUST NOT be present if the PDU containing the security header is being sent from server to client This flag MUST NOT be present if the PDU containing the security header is not being sent on the MCS message channel. The ID of the message channel is specified in the Server Message Channel Data (2.2.1.4.5).
	HEARTBEAT = 0x4000 #Indicates that the packet is a Heartbeat PDU (section 2.2.16.1). This flag MUST NOT be present if the PDU containing the security header is not being sent on the MCS message channel. The ID of the message channel is specified in the Server Message Channel Data (2.2.1.4.5).
	FLAGSHI_VALID = 0x8000 #Indicates that the flagsHi field contains valid data. If this flag is not set, then the contents of the flagsHi field MUST be ignored.

class TS_SECURITY_HEADER:
	def __init__(self):
		self.flags:SEC_HDR_FLAG = 0
		self.flagsHi:int = 0

	def to_bytes(self):
		t = self.flags.to_bytes(2, byteorder='little', signed = False)
		t += self.flagsHi.to_bytes(2, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SECURITY_HEADER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SECURITY_HEADER()
		msg.flags = SEC_HDR_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.flagsHi = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_SECURITY_HEADER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_SECURITY_HEADER1:
	def __init__(self):
		self.flags:SEC_HDR_FLAG = None
		self.flagsHi:int = 0
		self.dataSignature:bytes = None

	def to_bytes(self):
		t = self.flags.to_bytes(2, byteorder='little', signed = False)
		t += self.flagsHi.to_bytes(2, byteorder='little', signed = False)
		t += self.dataSignature
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SECURITY_HEADER1.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SECURITY_HEADER1()
		msg.flags = SEC_HDR_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.flagsHi = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.dataSignature = buff.read(8)
		return msg

	def __repr__(self):
		t = '==== TS_SECURITY_HEADER1 ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

class TS_SECURITY_HEADER2:
	def __init__(self):
		self.flags:SEC_HDR_FLAG = None
		self.flagsHi:int = 0
		self.length:int = 16
		self.version: int = 1
		self.padlen:int = 0
		self.dataSignature:bytes = None

	def to_bytes(self):
		t = self.flags.to_bytes(2, byteorder='little', signed = False)
		t += self.flagsHi.to_bytes(2, byteorder='little', signed = False)
		t += self.length.to_bytes(2, byteorder='little', signed = False)
		t += self.version.to_bytes(1, byteorder='little', signed = False)
		t += self.padlen.to_bytes(1, byteorder='little', signed = False)
		t += self.dataSignature
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SECURITY_HEADER2.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SECURITY_HEADER2()
		msg.flags = SEC_HDR_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.flagsHi = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.version = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.padlen = int.from_bytes(buff.read(1), byteorder='little', signed = False)
		msg.dataSignature = buff.read(8)
		return msg

	def __repr__(self):
		t = '==== TS_SECURITY_HEADER2 ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t