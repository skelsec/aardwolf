
import asyncio

class TCPStream:
	@staticmethod
	async def from_tcpsocket(tcpsocket):
		# tcpsocket must be running at this point
		in_queue = tcpsocket.in_queue
		out_queue = tcpsocket.out_queue
		closed_event = asyncio.Event()
		if hasattr(tcpsocket, 'disconnected'):
			closed_event = tcpsocket.disconnected

			
		writer = TCPStreamWriter(out_queue, closed_event)
		reader = TCPStreamReader(in_queue, closed_event)
		await writer.run()
		await reader.run()
		
		return reader, writer


class TCPStreamWriter:
	def __init__(self, out_queue, closed_event):
		self.out_queue = out_queue
		self.closed_event = closed_event

	def write(self, data):
		self.out_queue.put_nowait(data)

	def close(self):
		self.out_queue.put_nowait(b'')
		self.closed_event.set()

	async def drain(self):
		await asyncio.sleep(0)
		return

	async def run(self):
		return

class TCPStreamReader:
	def __init__(self, in_queue, closed_event):
		self.wsnet_reader_type = None
		self.in_queue = in_queue
		self.closed_event = closed_event
		self.buffer = b''
		self.data_in_evt = []
		self.err = None

		self.__lock = asyncio.Lock()

	async def run(self):
		return

	async def read(self, n = -1):
		try:
			if self.closed_event.is_set():
				return b''

			if self.__lock.locked() is True:
				raise Exception("Another operation is already in progress")
			
			if  len(self.buffer) > 0 and len(self.buffer) >= n:
				if n == -1:
					temp = self.buffer
					self.buffer = b''
				else:
					temp = self.buffer[:n]
					self.buffer = self.buffer[n:]
			
			else:
				async with self.__lock:
					if n == -1:
						res, self.err = await self.in_queue.get()
						self.buffer = b''

					while len(self.buffer) > 0 and len(self.buffer) >= n:
						res, self.err = await self.in_queue.get()
						if self.err is not None:
							if res is not None:
								self.buffer += res
							raise self.err
						self.buffer += res
					
					if n == -1:
						temp = self.buffer
						self.buffer = b''
						return temp
					else:
						temp = self.buffer[:n]
						self.buffer = self.buffer[n:]
						return temp
				return temp

		except Exception as e:
			#print(e)
			self.closed_event.set()
			raise

	async def readexactly(self, n):
		try:
			if n < 1:
				raise Exception('Readexactly must be a positive integer!')

			if self.__lock.locked() is True:
				raise Exception("Another operation is already in progress")
			async with self.__lock:
				while len(self.buffer) < n:
					res, self.err = await self.in_queue.get()
					if self.err is not None:
						if res is not None:
							self.buffer += res
						raise self.err
					
					self.buffer += res
				
				temp = self.buffer[:n]
				self.buffer = self.buffer[n:]
				return temp
		except Exception as e:
			#print(e)
			self.closed_event.set()
			raise

	async def readuntil(self, pattern):
		try:
			if self.closed_event.is_set():
				raise Exception('Pipe broken!')
			
			if self.__lock.locked() is True:
				raise Exception("Another operation is already in progress")
			
			async with self.__lock:
				ploc = self.buffer.find(pattern)
				while ploc == -1:
					res, self.err = await self.in_queue.get()
					if self.err is not None:
						if res is not None:
							self.buffer += res
						raise self.err
					
					self.buffer += res
					ploc = self.buffer.find(pattern)
				
				end = self.buffer.find(pattern)+len(pattern)
				temp = self.buffer[:end]
				self.buffer = self.buffer[end:]
				#print('readuntil ret %s' % temp)
				return temp

		except Exception as e:
			#print(e)
			self.closed_event.set()
			raise

	async def readline(self):
		return await self.readuntil(b'\n')