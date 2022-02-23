import enum
import asyncio
import ipaddress

from aardwolf import logger

from asysocks.client import SOCKSClient
from asysocks.common.comms import SocksQueueComms


class SocksProxyConnection:
	"""
	Generic asynchronous TCP socket class, nothing SMB related.
	Creates the connection and channels incoming/outgoing bytes via asynchonous queues.
	"""
	def __init__(self, target):
		self.target = target
		
		self.client = None
		self.proxy_task = None
		self.handle_in_task = None

		self.out_queue = None#asyncio.Queue()
		self.in_queue = None#asyncio.Queue()
		self.disconnected = None #asyncio.Event()

		self.proxy_in_queue = None#asyncio.Queue()
		self.is_plain_msg = True
		
	async def disconnect(self):
		"""
		Disconnects from the socket.
		Stops the reader and writer streams.
		"""
		if self.client is not None:
			await self.client.terminate()
		if self.proxy_task is not None:
			self.proxy_task.cancel()
		if self.handle_in_q is not None:
			self.handle_in_task.cancel()

	async def terminate(self):
		await self.disconnect()
			
	async def handle_in_q(self):
		try:
			while True:				
				temp, err = await self.proxy_in_queue.get()
				#print(temp)
				if err is not None:
					raise err

				if temp == b'' or temp is None:
					logger.debug('Server finished!')
					return

				await self.in_queue.put((temp, None))
				continue
		
		except asyncio.CancelledError:
			return
		except Exception as e:
			logger.exception('handle_in_q')
			await self.in_queue.put((None, e))

		finally:
			self.proxy_task.cancel()


		
	async def connect(self):
		"""
		
		"""
		try:
			self.out_queue = asyncio.Queue()
			self.in_queue = asyncio.Queue()
			self.disconnected = asyncio.Event()
			self.proxy_in_queue = asyncio.Queue()
			comms = SocksQueueComms(self.out_queue, self.proxy_in_queue)

			self.target.proxy.target[-1].endpoint_ip = self.target.get_hostname_or_ip() if self.target.serverip is None else self.target.serverip
			self.target.proxy.target[-1].endpoint_port = int(self.target.port)
			self.target.proxy.target[-1].endpoint_timeout = None #TODO: maybe implement endpoint timeout?
			self.target.proxy.target[-1].timeout = self.target.timeout
			self.client = SOCKSClient(comms, self.target.proxy.target)
			self.proxy_task = asyncio.create_task(self.client.run())
			self.handle_in_task = asyncio.create_task(self.handle_in_q())
			return True, None
		except Exception as e:
			return False, e

