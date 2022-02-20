import asyncio

import logging
import traceback
import socket
#from aardwolf import logger
#from aardwolf.commons.exceptions import *

class TCPSocket:
	"""
	Generic asynchronous TCP socket class, nothing RDP related.
	Creates the connection and channels incoming/outgoing bytes via asynchonous queues.
	"""
	def __init__(self, target):
		self.settings = target
		self.reader = None
		self.writer = None
		
		self.out_queue = asyncio.Queue()
		self.in_queue = asyncio.Queue()
		
		self.disconnected = asyncio.Event()

		self.incoming_task = None
		self.outgoing_task = None
		self.disconnect_monitor_task = None


	async def disconnect_monitor(self):
		await self.disconnected.wait()
		if self.incoming_task is not None:
			self.incoming_task.cancel()
		await self.disconnect()
		

		
	async def disconnect(self):
		"""
		Disconnects from the socket.
		Stops the reader and writer streams.
		"""
		if self.disconnected.is_set():
			return
		if self.outgoing_task is not None:
			self.outgoing_task.cancel()
		if self.incoming_task is not None:
			self.incoming_task.cancel()

		if self.writer is not None:
			try:
				self.writer.close()
			except:
				pass
		self.writer = None
		self.reader = None
		self.disconnected.set()

	async def handle_incoming(self):
		"""
		Reads data bytes from the socket and dispatches it to the incoming queue
		"""
		try:
			lasterror = None
			while not self.disconnected.is_set():
				try:
					await asyncio.sleep(0)
					data = await self.reader.read(1073741824)
					#print('TCP <- %s' % data.hex())
					await self.in_queue.put( (data, None) )
					if data == b'':
						return
				
				except asyncio.CancelledError as e:
					lasterror = e
					break
				except Exception as e:
					#logging.exception('[TCPSocket] handle_incoming %s' % str(e))
					lasterror = e
					break
			
			
		except asyncio.CancelledError:
			return
		
		except Exception as e:
			lasterror = e

		finally:
			#print('??????????')
			if self.in_queue is not None:
				await self.in_queue.put( (None, lasterror) )
			await self.disconnect()
		
	async def handle_outgoing(self):
		"""
		Reads data bytes from the outgoing queue and dispatches it to the socket
		"""
		try:
			while not self.disconnected.is_set():
				data = await self.out_queue.get()
				if data == b'':
					return
				#print('TCP -> %s' % data.hex())
				self.writer.write(data)
				await self.writer.drain()
		except asyncio.CancelledError:
			#the RDP connection is terminating
			return
			
		except Exception as e:
			logging.exception('[TCPSocket] handle_outgoing %s' % str(e))
		finally:
			await self.disconnect()
			
	async def connect(self):
		"""
		Main function to be called, connects to the target specified in settings, and starts reading/writing.
		"""
		
		try:
			con = asyncio.open_connection(self.settings.get_ip(), self.settings.get_port())
			
			try:
				self.reader, self.writer = await asyncio.wait_for(con, int(self.settings.timeout))
			except asyncio.TimeoutError:
				logging.debug('[TCPSocket] Connection timeout')
				raise Exception('[TCPSocket] Connection timeout')
				
			except ConnectionRefusedError:
				logging.debug('[TCPSocket] Connection refused')
				raise Exception('[TCPSocket] Connection refused')
				
			except asyncio.CancelledError:
				#the RDP connection is terminating
				raise asyncio.CancelledError
				
			except Exception as e:
				logging.debug('[TCPSocket] connect generic exception')
				raise e
			
			self.incoming_task = asyncio.create_task(self.handle_incoming())
			self.outgoing_task = asyncio.create_task(self.handle_outgoing())
			self.disconnect_monitor_task = asyncio.create_task(self.disconnect_monitor())


			return True, None
		except Exception as e:
			try:
				self.writer.close()
			except:
				pass
			return False, e

			
			