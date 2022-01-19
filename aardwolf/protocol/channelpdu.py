import io
import enum

class CHANNEL_FLAG(enum.IntFlag):
	CHANNEL_FLAG_FIRST = 0x00000001 #Indicates that the chunk is the first in a sequence.
	CHANNEL_FLAG_LAST = 0x00000002 #Indicates that the chunk is the last in a sequence.
	CHANNEL_FLAG_SHOW_PROTOCOL = 0x00000010 #The Channel PDU Header MUST be visible to the application endpoint (section 2.2.1.3.4.1).
	CHANNEL_FLAG_SUSPEND = 0x00000020 #All virtual channel traffic MUST be suspended. This flag is only valid in server-to-client virtual channel traffic. It MUST be ignored in client-to-server data.
	CHANNEL_FLAG_RESUME = 0x00000040 #All virtual channel traffic MUST be resumed. This flag is only valid in server-to-client virtual channel traffic. It MUST be ignored in client-to-server data.
	CHANNEL_FLAG_SHADOW_PERSISTENT = 0x00000080 #This flag is unused and its value MUST be ignored by the client and server.
	CHANNEL_PACKET_COMPRESSED = 0x00200000 #The virtual channel data is compressed. This flag is equivalent to MPPC bit C (for more information see [RFC2118] section 3.1).
	CHANNEL_PACKET_AT_FRONT = 0x00400000 #The decompressed packet MUST be placed at the beginning of the history buffer. This flag is equivalent to MPPC bit B (for more information see [RFC2118] section 3.1).
	CHANNEL_PACKET_FLUSHED = 0x00800000 #The decompressor MUST reinitialize the history buffer (by filling it with zeros) and reset the HistoryOffset to zero. After it has been reinitialized, the entire history buffer is immediately regarded as valid. This flag is equivalent to MPPC bit A (for more information see [RFC2118] section 3.1). If the CHANNEL_PACKET_COMPRESSED (0x00200000) flag is also present, then the CHANNEL_PACKET_FLUSHED flag MUST be processed first.
	CompressionTypeMask = 0x000F0000 #Indicates the compression package which was used to compress the data. See the discussion which follows this table for a list of compression packages.

class CHANNEL_PDU_HEADER:
	def __init__(self):
		self.length:int = None
		self.flags:CHANNEL_FLAG = None
		self.data:bytes = None

	def to_bytes(self):
		t = self.length.to_bytes(4, byteorder='little', signed = False)
		t += self.flags.to_bytes(4, byteorder='little', signed = False)
		t += self.data
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CHANNEL_PDU_HEADER.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CHANNEL_PDU_HEADER()
		msg.length = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.flags = CHANNEL_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.data = buff.read(msg.length)
		return msg

	@staticmethod
	def serialize_packet(flags:CHANNEL_FLAG, data, length = None):
		hdr = CHANNEL_PDU_HEADER()
		hdr.length = len(data)
		if length is not None:
			hdr.length = length
		hdr.data = data
		hdr.flags = flags
		return hdr

	def __repr__(self):
		t = '==== CHANNEL_PDU_HEADER ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t