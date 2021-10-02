from aardwolf.network.x224 import X224Network
import asyncio
import traceback
import os

from aardwolf.protocol.tpkt import TPKT
from aardwolf.protocol.x224.constants import NEG_FLAGS, SUPP_PROTOCOLS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest, RDP_NEG_REQ
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm

from aardwolf.transport.tcp import TCPSocket
from aardwolf.network.tpkt import TPKTNetwork
from aardwolf.network.tpkt import TPKTNetwork

class AARDPTarget:
	def __init__(self):
		self.ip = None
		self.port = None
		self.timeout = 10
	
	def get_ip(self):
		return self.ip

	def get_port(self):
		return self.port

async def amain():
	try:
		target = AARDPTarget()
		target.ip = '10.10.10.103'
		target.port = 3389
		tcptransport = TCPSocket(target)
		_, err = await tcptransport.connect()
		if err is not None:
			raise err

		tpktnet = TPKTNetwork(tcptransport)
		_, err = await tpktnet.run()
		if err is not None:
			raise err

		x224net = X224Network(tpktnet)
		_, err = await x224net.run()
		if err is not None:
			raise err
		
		#await x224net.out_queue.put(b'ALMA')

		_, err = await x224net.client_negotiate()
		if err is not None:
			raise err

		print('Done!')
	except Exception as e:
		traceback.print_exc()

if __name__ == '__main__':
	asyncio.run(amain())
