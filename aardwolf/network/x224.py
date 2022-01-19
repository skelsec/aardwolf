import asyncio
import os

import logging
import typing
from aardwolf.network.tpkt import TPKTNetwork
from aardwolf.protocol.x224.constants import TPDU_TYPE, NEG_FLAGS, SUPP_PROTOCOLS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm
from aardwolf.protocol.x224.data import Data
from aardwolf.protocol.x224 import X224Packet
from aardwolf.protocol.x224.constants import NEG_FLAGS, SUPP_PROTOCOLS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest, RDP_NEG_REQ
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm


class X224Network:
	"""
	IMPORTANT! The transpo
	"""
	def __init__(self, transport:TPKTNetwork):
		self.transport:TPKTNetwork = transport

		self.out_queue = asyncio.Queue()
		self.in_queue = asyncio.Queue()
		
		self.disconnected = asyncio.Event()

		self.incoming_task = None
		self.outgoing_task = None
		
	async def disconnect(self):
		if self.outgoing_task is not None:
			self.outgoing_task.cancel()
		if self.incoming_task is not None:
			self.incoming_task.cancel()
		self.disconnected.set()
	
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

			#print(X224Packet.from_bytes(conreq.to_bytes()))

			await self.transport.out_queue.put(conreq.to_bytes())
			is_fastpath, reply, err = await self.in_queue.get()
			if err is not None:
				raise err
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

	async def handle_incoming(self):
		"""
		Reads data bytes from the socket and dispatches it to the incoming queue
		"""
		try:
			lasterror = None
			msgsize = None
			buffer = b''
			while not self.disconnected.is_set():	
				try:
					is_fastpath, data, err = await self.transport.in_queue.get()
					if err is not None:
						raise err
					if data is None:
						return

					packet = data
					if is_fastpath is False:
						#print('X224Net <- %s' % data.hex())
						packet = X224Packet.from_bytes(data)
						#print('X224Net (packet) <- %s' % packet)
					await self.in_queue.put((is_fastpath, packet, None))
				except asyncio.CancelledError as e:
					lasterror = e
					break
				except Exception as e:
					logging.exception('[X224Net] handle_incoming %s' % str(e))
					lasterror = e
					break
			
			
		except asyncio.CancelledError:
			return
		
		except Exception as e:
			lasterror = e

		finally:
			if self.in_queue is not None:
				await self.in_queue.put( (None, None, lasterror) )
			await self.disconnect()
		
	async def handle_outgoing(self):
		"""
		Reads data bytes from the outgoing queue and dispatches it to the socket
		"""
		try:
			while not self.disconnected.is_set():
				data = await self.out_queue.get()
				if data is None:
					return
				msg = Data()
				msg.data = data
				#print('X224Net -> %s' % msg.to_bytes().hex())
				await self.transport.out_queue.put(msg.to_bytes())
		except asyncio.CancelledError:
			return
		except Exception as e:
			logging.debug('[X224Net] handle_outgoing %s' % str(e))
		finally:
			await self.disconnect()
	
	async def run(self):
		try:
			self.incoming_task = asyncio.create_task(self.handle_incoming())
			self.outgoing_task = asyncio.create_task(self.handle_outgoing())
			return True, None
		except Exception as e:
			return False, e

			
			