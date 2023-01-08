
from aardwolf.extensions.RDPEDYC.vchannels import VirtualChannelBase


class VchannelECHO(VirtualChannelBase):
	def __init__(self):
		VirtualChannelBase.__init__(self, 'ECHO')
	
	async def channel_init(self):
		#print('ECHO channel started!')
		return True, None

	async def channel_data_in(self, data):
		#print('ECHO channel data in: %s' % data)
		await self.channel_data_out(data)
	