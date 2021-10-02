import io
import enum

class VCCAPS(enum.IntFlag):
	NO_COMPR = 0x00000000 #Virtual channel compression is not supported.
	COMPR_SC = 0x00000001 #Indicates to the server that virtual channel compression is supported by the client for server-to-client traffic. The highest compression level supported by the client is advertised in the Client Info PDU (section 2.2.1.11).
	COMPR_CS_8K = 0x00000002 #Indicates to the client that virtual channel compression is supported by the server for client-to-server traffic (the compression level is limited to RDP 4.0 bulk compression).

class TS_VIRTUALCHANNEL_CAPABILITYSET:
	def __init__(self):
		self.flags:VCCAPS = VCCAPS.NO_COMPR
		self.VCChunkSize:int = None

	def to_bytes(self):
		t = self.flags.to_bytes(4, byteorder='little', signed = False)
		if self.VCChunkSize is not None:
			t += self.VCChunkSize.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_VIRTUALCHANNEL_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_VIRTUALCHANNEL_CAPABILITYSET()
		msg.flags = VCCAPS(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		if buff.read(1) == b'':
			return msg
		buff.seek(-1,1)
		#optional
		msg.VCChunkSize = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		return msg

	def __repr__(self):
		t = '==== TS_VIRTUALCHANNEL_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t