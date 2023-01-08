
from aardwolf.extensions.RDPEDYC.vchannels import VirtualChannelBase
import asyncio


class VchannelTEST(VirtualChannelBase):
	def __init__(self):
		VirtualChannelBase.__init__(self, 'DATATEST1')
	
	async def channel_init(self):
		print('DATATEST1 channel started!')
		return True, None

	async def channel_data_in(self, data):
		print('DATATEST1 channel data in: %s' % data)
		#await self.channel_data_out(data)

		await asyncio.sleep(5)
		await self.channel_data_out(b'AB'*5000)