import asyncio

import logging
import traceback
from aardwolf.protocol.tpkt import TPKT

class TPKTNetwork:
	def __init__(self, transport):
		self.transport = transport

		self.out_queue = asyncio.Queue()
		self.in_queue = asyncio.Queue()
		
		self.disconnected = asyncio.Event()

		self.incoming_task = None
		self.outgoing_task = None

		self.__buffer = b''
		self.__soft_switch = False
		
	async def disconnect(self):
		if self.outgoing_task is not None:
			self.outgoing_task.cancel()
		if self.incoming_task is not None:
			self.incoming_task.cancel()
		if self.transport is not None:
			self.transport.out_queue.put_nowait(b'')
			await self.transport.disconnect()
		self.disconnected.set()

	async def handle_incoming(self):
		"""
		Reads data bytes from the socket and dispatches it to the incoming queue
		"""
		try:
			lasterror = None
			msgsize = None
			is_fastpath = False
			while not self.disconnected.is_set():	
				try:
					if msgsize is None:
						if len(self.__buffer) >= 4:
							if self.__buffer[0] == 3:
								msgsize = int.from_bytes(self.__buffer[2:4], byteorder='big', signed=False)
							else:
								is_fastpath = True
								msgsize = self.__buffer[1]
								if msgsize >> 7 == 1:
									msgsize = int.from_bytes(self.__buffer[1:3], byteorder='big', signed=False)
									msgsize = msgsize & 0x7fff


					if msgsize is not None:
						if len(self.__buffer)>=msgsize:
							if is_fastpath is False:
								msg = TPKT.from_bytes(self.__buffer[:msgsize])
								await self.in_queue.put( (is_fastpath, msg.tpdu, None) )
								self.__buffer = self.__buffer[msgsize:]
								msgsize = None
							else:
								await self.in_queue.put( (is_fastpath, self.__buffer[:msgsize], None) )
								self.__buffer = self.__buffer[msgsize:]
								msgsize = None
								is_fastpath = False
						
							if len(self.__buffer) > 0:
								continue

					data, err = await self.transport.in_queue.get()
					if err is not None:
						raise err
					if data is None:
						return

					self.__buffer += data				
				except asyncio.CancelledError as e:
					lasterror = e
					break
				except Exception as e:
					logging.exception('[TPKTNetwork] handle_incoming %s' % str(e))
					lasterror = e
					break
			
			
		except asyncio.CancelledError:
			return
		
		except Exception as e:
			lasterror = e

		finally:
			if self.__soft_switch is False:
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
				msg = TPKT()
				msg.tpdu = data
				#print('TPKT -> %s' % msg.to_bytes())
				await self.transport.out_queue.put(msg.to_bytes())
		except asyncio.CancelledError:
			return
		except Exception as e:
			logging.exception('[TPKTNetwork] handle_outgoing %s' % str(e))
		finally:
			if self.__soft_switch is False:
				await self.disconnect()
	
	async def suspend_read(self):
		try:
			self.__soft_switch = True
			self.incoming_task.cancel()
			self.outgoing_task.cancel()
			return True, None
		except Exception as e:
			return None, e

	async def conitnue_read(self):
		try:
			self.__soft_switch = False
			self.incoming_task = asyncio.create_task(self.handle_incoming())
			self.outgoing_task = asyncio.create_task(self.handle_outgoing())
			return True, None
		except Exception as e:
			return None, e


	async def switch_transport(self, newtransportobj):
		#most cases this means that we are switching to SSL from TCP
		try:
			self.__soft_switch = True #indicating that no errors will be sent to lower/upper layers
			self.incoming_task.cancel()
			self.outgoing_task.cancel()
			self.transport, err = await newtransportobj.from_transport(self.transport)
			if err is not None:
				raise err
			self.__soft_switch = False
			self.incoming_task = asyncio.create_task(self.handle_incoming())
			self.outgoing_task = asyncio.create_task(self.handle_outgoing())
			
			return True, None
		except Exception as e:
			#traceback.print_exc()
			return None, e

	async def run(self):
		try:
			self.incoming_task = asyncio.create_task(self.handle_incoming())
			self.outgoing_task = asyncio.create_task(self.handle_outgoing())
			return True, None
		except Exception as e:
			return False, e

			
			