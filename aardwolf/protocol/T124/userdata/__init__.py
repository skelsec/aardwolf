
import io
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE
from aardwolf.protocol.T124.userdata.clientcoredata import TS_UD_CS_CORE
from aardwolf.protocol.T124.userdata.clientsecuritydata import TS_UD_CS_SEC
from aardwolf.protocol.T124.userdata.clientnetworkdata import TS_UD_CS_NET
from aardwolf.protocol.T124.userdata.clientclusterdata import TS_UD_CS_CLUSTER
from aardwolf.protocol.T124.userdata.monitordefinition import TS_UD_CS_MONITOR
from aardwolf.protocol.T124.userdata.clientmessagechanneldata import TS_UD_CS_MCS_MSGCHANNEL
from aardwolf.protocol.T124.userdata.clientmultitransportchanneldata import TS_UD_CS_MULTITRANSPORT
from aardwolf.protocol.T124.userdata.clientmonitorextendeddata import TS_UD_CS_MONITOR_EX

from aardwolf.protocol.T124.userdata.servercoredata import TS_UD_SC_CORE
from aardwolf.protocol.T124.userdata.serversecuritydata import TS_UD_SC_SEC1
from aardwolf.protocol.T124.userdata.servernetworkdata import TS_UD_SC_NET
from aardwolf.protocol.T124.userdata.servermessagechannel import TS_UD_SC_MCS_MSGCHANNEL
from aardwolf.protocol.T124.userdata.servermultitransportchanneldata import TS_UD_SC_MULTITRANSPORT


class TS_UD:
	def __init__(self):
		self.userdata = {}

	@staticmethod
	def from_bytes(data):
		return TS_UD.from_buffer(io.BytesIO(data))
	
	@staticmethod
	def from_buffer(buff):
		res = TS_UD()
		start = buff.tell()
		buff.seek(0,2)
		end = buff.tell()
		buff.seek(start)
		while buff.tell() < end:
			print(buff.tell())
			ts = buff.tell()
			otype = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed=False))
			olen = int.from_bytes(buff.read(2), byteorder='little', signed=False)
			buff.seek(ts)
			res.userdata[otype] = type2obj[otype].from_buffer(buff)
		return res
	
	def to_bytes(self):
		t = b''
		for k in self.userdata:
			t += self.userdata[k].to_bytes()
		return t

class TS_UD_PACKET:
	@staticmethod
	def from_bytes(data):
		olen = int.from_bytes(data[2:4], byteorder='little', signed=False)
		otype = TS_UD_TYPE(int.from_bytes(data[:2], byteorder='little', signed=False))
		return type2obj[otype].from_bytes(data[:olen])
	
	@staticmethod
	def from_buffer(buff):
		start = buff.tell()
		olen = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		otype = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		buff.seek(start)
		return type2obj[otype].from_buffer(buff)


type2obj = {
	TS_UD_TYPE.CS_CORE : TS_UD_CS_CORE,
	TS_UD_TYPE.CS_SECURITY : TS_UD_CS_SEC,
	TS_UD_TYPE.CS_NET : TS_UD_CS_NET,
	TS_UD_TYPE.CS_CLUSTER : TS_UD_CS_CLUSTER,
	TS_UD_TYPE.CS_MONITOR : TS_UD_CS_MONITOR,
	TS_UD_TYPE.CS_MCS_MSGCHANNEL : TS_UD_CS_MCS_MSGCHANNEL,
	TS_UD_TYPE.CS_MONITOR_EX : TS_UD_CS_MONITOR_EX,
	TS_UD_TYPE.CS_MULTITRANSPORT : TS_UD_CS_MULTITRANSPORT,
}

class TS_SC:
	def __init__(self):
		self.serverdata = {}

	@staticmethod
	def from_bytes(data):
		return TS_SC.from_buffer(io.BytesIO(data))
	
	@staticmethod
	def from_buffer(buff):
		res = TS_SC()
		start = buff.tell()
		buff.seek(0,2)
		end = buff.tell()
		buff.seek(start)
		while buff.tell() < end:
			ts = buff.tell()
			otype = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed=False))
			olen = int.from_bytes(buff.read(2), byteorder='little', signed=False)
			buff.seek(ts)
			res.serverdata[otype] = srvtype2obj[otype].from_buffer(buff)
		return res
	
	def to_bytes(self):
		t = b''
		for k in self.serverdata:
			t += self.serverdata[k].to_bytes()
		return t

class TS_SC_PACKET:
	@staticmethod
	def from_bytes(data):
		olen = int.from_bytes(data[2:4], byteorder='little', signed=False)
		otype = TS_UD_TYPE(int.from_bytes(data[:2], byteorder='little', signed=False))
		return srvtype2obj[otype].from_bytes(data[:olen])
	
	@staticmethod
	def from_buffer(buff):
		start = buff.tell()
		olen = int.from_bytes(buff.read(2), byteorder='little', signed=False)
		otype = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed=False))
		buff.seek(start)
		return type2obj[otype].from_buffer(buff)


srvtype2obj = {
	TS_UD_TYPE.SC_CORE : TS_UD_SC_CORE,
	TS_UD_TYPE.SC_SECURITY : TS_UD_SC_SEC1,
	TS_UD_TYPE.SC_NET : TS_UD_SC_NET,
	TS_UD_TYPE.SC_MCS_MSGCHANNEL : TS_UD_SC_MCS_MSGCHANNEL,
	TS_UD_TYPE.SC_MULTITRANSPORT : TS_UD_SC_MULTITRANSPORT,
}