
import io
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD, dynvc_header_to_bytes, dynvc_header_from_buff

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/69377767-56a6-4ab8-996b-7758676e9261
class DYNVC_DATA_FIRST:
	def __init__(self):
		self.cbid:int = 4
		self.len:int   = 4
		self.cmd:DYNVC_CMD = DYNVC_CMD.DATA_FIRST
		self.ChannelId:int   = 0
		self.Length:int = None
		self.Data:bytes = None

	@staticmethod
	def from_bytes(data: bytes):
		return DYNVC_DATA_FIRST.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		hdr_start = buff.tell()
		msg = DYNVC_DATA_FIRST()
		msg.cbid, msg.len, msg.cmd = dynvc_header_from_buff(buff, cbid_mod=True, sp_mod = True)
		msg.ChannelId = int.from_bytes(buff.read(msg.cbid), byteorder='little', signed=False)
		msg.Length = int.from_bytes(buff.read(msg.len), byteorder='little', signed=False)
		hdr_end = buff.tell()
		hdrsize = hdr_end - hdr_start
		if hdrsize+msg.Length < 1600:
			msg.Data = buff.read(msg.Length)
		else:
			msg.Data = buff.read(1600 - hdrsize)

		return msg

	def to_bytes(self):
		t = b''
		t += dynvc_header_to_bytes(self.cbid, self.len, self.cmd, cbid_mod=True, sp_mod = True)
		t += self.ChannelId.to_bytes(self.cbid, byteorder='little', signed=False)
		t += self.Length.to_bytes(self.len, byteorder='little', signed=False)
		t += self.Data
		return t

	@staticmethod
	def chunk_data(data, channel_id):
		chunksize = 1600-9
		if len(data) < chunksize:
			msg = DYNVC_DATA()
			msg.cbid = 4
			msg.ChannelId = channel_id
			msg.Data = data
			yield msg.to_bytes()
		else:
			msg = DYNVC_DATA_FIRST()
			msg.cbid = 4
			msg.len  = 4
			msg.cmd  = DYNVC_CMD.DATA_FIRST
			msg.ChannelId = channel_id
			msg.Data = data[:chunksize]
			msg.Length = len(data)
			yield msg.to_bytes()

			i = chunksize
			while i < len(data):
				chunk = data[i:i+chunksize]
				msg = DYNVC_DATA()
				msg.cbid = 4
				msg.ChannelId = channel_id
				msg.Data = chunk
				yield msg.to_bytes()
				i += chunksize
			
	def __str__(self):
		t = ''
		for k in self.__dict__:
			if k == 'Data' and len(self.Data) > 100:
				res = 'Data: %s...(%s)\r\n' % (self.Data[50], len(self.Data))
			else:
				res = '%s: %s\r\n' % (k, self.__dict__[k])
			t += res
		return t

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/15b59886-db44-47f1-8da3-47c8fcd82803
class DYNVC_DATA:
	def __init__(self):
		self.cbid:int = None
		self.sp:int   = 0
		self.cmd:DYNVC_CMD = DYNVC_CMD.DATA
		self.ChannelId:int   = 0
		self.Data:bytes = None

	@staticmethod
	def from_bytes(data: bytes):
		return DYNVC_DATA.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		hdr_start = buff.tell()
		msg = DYNVC_DATA()
		msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff, cbid_mod=True, sp_mod = True)
		msg.ChannelId = int.from_bytes(buff.read(msg.cbid), byteorder='little', signed=False)
		hdr_end = buff.tell()
		hdrsize = hdr_end - hdr_start
		msg.Data = buff.read(1600 - hdrsize)
		return msg

	def to_bytes(self):
		t = b''
		t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd, cbid_mod=True, sp_mod = True)
		t += self.ChannelId.to_bytes(self.cbid, byteorder='little', signed=False)
		t += self.Data
		return t


	def __str__(self):
		t = ''
		for k in self.__dict__:
			if k == 'Data' and len(self.Data) > 100:
				res = 'Data: %s...(%s)\r\n' % (self.Data[50], len(self.Data))
			else:
				res = '%s: %s\r\n' % (k, self.__dict__[k])
			t += res
		return t