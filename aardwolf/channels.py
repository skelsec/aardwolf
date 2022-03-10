
import asyncio
import traceback
import typing

from aardwolf.protocol.T124.userdata.constants import ChannelOption

class Channel:
	def __init__(self, name:str, options:ChannelOption = ChannelOption.INITIALIZED|ChannelOption.ENCRYPT_RDP):
		self.name = name
		self.options = options
		self.channel_id = None
		self.raw_in_queue = asyncio.Queue()
		self.raw_out_queue = None
		self.in_queue = asyncio.Queue()
		self.data_in_queue = asyncio.Queue()
		self.out_queue = asyncio.Queue()
		self.connection = None
		self.initiator = None

	def get_name(self):
		return self.name
	
	async def disconnect(self):
		try:
			if self.monitor_out_task is not None:
				self.monitor_out_task.cancel()
			if self.monitor_in_task is not None:
				self.monitor_in_task.cancel()
			_, err = await self.stop()
			if err is not None:
				raise err
		except:
			pass

	async def run(self, connection):
		try:
			# this should take a queues which belong to the lower-layer
			self.raw_out_queue = connection._x224net.out_queue
			self.connection = connection
			self.initiator = self.connection._initiator
			self.monitor_out_task = asyncio.create_task(self.monitor_out())
			self.monitor_in_task = asyncio.create_task(self.monitor_in())
			_, err = await self.start()
			if err is not None:
				raise err
			return True, None
		except Exception as e:
			traceback.print_exc()
			return None, e


	async def start(self):
		# Override this when implementing new channel type
		try:
			return True, None
		except Exception as e:
			return None, e
	
	async def stop(self):
		# Override this when implementing new channel type
		try:
			return True, None
		except Exception as e:
			return None, e

	async def monitor_in(self):
		try:
			while True:
				data, err = await self.raw_in_queue.get()						
				if err is not None:
					await self.out_queue.put((data, err))
					raise err
				#print('Channel data in! "%s(%s)" <- %s' % (self.name, self.channel_id, data))

				await self.out_queue.put((data, err))

		except asyncio.CancelledError:
			return None, None
		except Exception as e:
			traceback.print_exc()
			return None, e
	
	async def monitor_out(self):
		try:
			while True:
				data = await self.in_queue.get()
				#print('Sending data on channel "%s(%s)" -> %s' % (self.name, self.channel_id, data))
				await self.raw_out_queue.put(data)

		except asyncio.CancelledError:
			return None, None

		except Exception as e:
			traceback.print_exc()
			return None, e
	
	