import asyncio

from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD
from aardwolf.extensions.RDPEDYC.protocol.data import DYNVC_DATA_FIRST, DYNVC_DATA

class VirtualChannelBase:
	def __init__(self, name:str, buffered = True):
		self.channel_name:str = name
		self.channel_id:int = None
		self.channel_closed_evt:asyncio.Event = asyncio.Event()
		self.__channel_data_buffered = buffered
		self.__virtual_channel_manager = None
		self.__fragment_buffer:bytes = b''
		self.__current_data_length = -1
		self.__send_lock = asyncio.Lock()

	async def channel_init_internal(self, channelid:int, manager):
		self.channel_id = channelid
		self.__virtual_channel_manager = manager
		return await self.channel_init()

	async def channel_rawdata_in(self, msg:DYNVC_DATA_FIRST or DYNVC_DATA):
		"""
		This method is called by the Channel Manager whenever (uncompressed) data is coming in.
		The data might be fragmented, so this function serves to reconstruct the entire data that is
		send by the server. 

		"""
		if self.__channel_data_buffered is False:
			await self.channel_data_in(msg.Data)
			return
		
		self.__fragment_buffer += msg.Data
		if msg.cmd == DYNVC_CMD.DATA_FIRST:
			self.__current_data_length = msg.Length

		if len(self.__fragment_buffer) == self.__current_data_length or self.__current_data_length == -1:
			await self.channel_data_in(self.__fragment_buffer)
			self.__fragment_buffer = b''
			self.__current_data_length = -1
		#print('__current_data_length: %s' % self.__current_data_length)
		#print('len(self.__fragment_buffer): %s' % len(self.__fragment_buffer))

	async def channel_data_out(self, data:bytes):
		async with self.__send_lock:
			for datamsg in DYNVC_DATA_FIRST.chunk_data(data, self.channel_id):
				#print('Sending reply data: %s' % datamsg)
				await self.__virtual_channel_manager.fragment_and_send(datamsg)
	
	async def channel_closed(self):
		"""
		The remote end closed the channel
		"""
		self.channel_closed_evt.set()

	async def close_channel(self):
		"""
		Triggers the channel to be closed
		"""
		await self.__virtual_channel_manager.close_channel(self.channel_id)

	#### OVERRIDE THESE
	async def channel_init(self):
		"""
		This function is called when the channel is about to start.
		YOU MUST return a Tuple[Bool, Exception] after finishing init.
		If you return exception in the tuple, the channel will be discarded.
		"""
		return True, None

	async def channel_data_in(self, data:bytes):
		"""
		This function will be called when data arrives on this channel.
		If you used unbuffered channel, the data here will arrive in 1600 byte chunks
		"""
		pass

	

	
