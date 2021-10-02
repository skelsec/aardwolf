
from aardwolf.protocol.x224.constants import TPDU_TYPE, NEG_FLAGS, SUPP_PROTOCOLS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm
from aardwolf.protocol.x224.data import Data

class X224Packet:
	@staticmethod
	def from_bytes(data: bytes):
		dtype = TPDU_TYPE(data[1] >> 4)
		return ptype2obj[dtype].from_bytes(data)

ptype2obj = {
	TPDU_TYPE.DATA : Data,
	TPDU_TYPE.CONNECTION_REQUEST : ConnectionRequest,
	TPDU_TYPE.CONNECTION_CONFIRM : ConnectionConfirm,
}
