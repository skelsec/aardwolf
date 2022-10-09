import typing


from asysocks.unicomm.common.connection import UniConnection

from aardwolf.protocol.x224.constants import TPDU_TYPE, NEG_FLAGS, SUPP_PROTOCOLS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm
from aardwolf.protocol.x224.data import Data
from aardwolf.protocol.x224 import X224Packet
from aardwolf.protocol.x224.constants import NEG_FLAGS, SUPP_PROTOCOLS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest, RDP_NEG_REQ
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm


class X224Network:
	def __init__(self, connection:UniConnection):
		self.connection = connection
	
	async def client_negotiate(self, flags:NEG_FLAGS = 0, supported_protocols:SUPP_PROTOCOLS = SUPP_PROTOCOLS.SSL|SUPP_PROTOCOLS.HYBRID_EX, to_raise = True):
		reply = None
		try:
			negreq = RDP_NEG_REQ()
			negreq.flags = flags
			negreq.requestedProtocols = supported_protocols
			
			conreq = ConnectionRequest()
			conreq.SRC_REF = 0
			conreq.cookie = b'Cookie: mstshash=devel\r\n'
			conreq.rdpNegReq = negreq

			await self.connection.write(conreq.to_bytes())
			reply = await self.read()
			if reply.CR != TPDU_TYPE.CONNECTION_CONFIRM:
				raise Exception('Server sent back unknown TPDU type! %s' % reply.CR)
			reply = typing.cast(ConnectionConfirm, reply)
			if reply.rdpNegData is None:
				return reply, None
			
			if reply.rdpNegData.type == 3 and to_raise is True:
				#server denied our request!
				raise Exception('Server refused our connection request! Reason: %s' % reply.rdpNegData.failureCode.name)

			return reply, None
		except Exception as e:
			return reply, e

	async def read(self):
		is_fastpath, tpktdata = await self.connection.read_one()
		if is_fastpath is True:
			raise Exception('Fastpath packet should never be here!')
		return X224Packet.from_bytes(tpktdata)

	async def write(self, data):
		msg = Data()
		msg.data = data
		await self.connection.write(msg.to_bytes())

			
			