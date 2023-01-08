import asyncio
import traceback
from typing import cast, Dict, List

from aardwolf import logger
from aardwolf.channels import Channel
from aardwolf.protocol.T124.userdata.constants import ChannelOption
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_MESSAGE, DYNVC_CMD
from aardwolf.extensions.RDPEDYC.protocol.caps import DYNVC_CAPS_REQ
from aardwolf.extensions.RDPEDYC.protocol.create import DYNVC_CREATE_REQ, DYNVC_CREATE_RSP
from aardwolf.extensions.RDPEDYC.protocol.close import DYNVC_CLOSE

from aardwolf.protocol.channelpdu import CHANNEL_PDU_HEADER, CHANNEL_FLAG
from aardwolf.protocol.T128.security import TS_SECURITY_HEADER,SEC_HDR_FLAG
from aardwolf.extensions.RDPEDYC.vchannels import VirtualChannelBase

class RDPEDYCChannel(Channel):
	name = 'drdynvc'
	def __init__(self, iosettings):
		Channel.__init__(self, self.name, ChannelOption.INITIALIZED|ChannelOption.ENCRYPT_RDP)
		self.defined_channels = iosettings.vchannels
		self.compression_needed = False
		self.version = 1
		self.version_data_sent = False
		self.channels:Dict[int, VirtualChannelBase] = {}
	
	async def start(self):
		try:
			#print('START called!')
			return True, None
		except Exception as e:
			return None, e

	async def stop(self):
		try:
			return True, None
		except Exception as e:
			return None, e

	async def close_channel(self, channelid):
		resp = DYNVC_CLOSE()
		resp.ChannelId = channelid
		await self.fragment_and_send(resp.to_bytes())
		if channelid not in self.channels:
			return
		await self.channels[channelid].channel_closed()

	async def send_channel_create_response(self, channelid, result:int = 0):
		resp = DYNVC_CREATE_RSP()
		resp.ChannelId = channelid
		resp.CreationStatus = result
		await self.fragment_and_send(resp.to_bytes())
	
	async def process_channel_data(self, data):
		#print('CHANNELDATA: %s' % data)
		channeldata = CHANNEL_PDU_HEADER.from_bytes(data)
		#print(channeldata)
		msg = DYNVC_MESSAGE.from_bytes(channeldata.data)
		#print(msg)
		if msg.cmd == DYNVC_CMD.CAPS_RSP and self.version_data_sent is False:
			await self.fragment_and_send(DYNVC_CAPS_REQ().to_bytes())
			self.version_data_sent = True
			return
		
		if msg.cmd == DYNVC_CMD.CREATE_RSP:
			msg = cast(DYNVC_CREATE_REQ, msg)
			if msg.ChannelName not in self.defined_channels:
				logger.debug('Server supports channel "%s" but client doesn\'t have definition!' % msg.ChannelName)
				await self.send_channel_create_response(msg.ChannelId, result = 0xC0000001) #STATUS_UNSUCCESSFUL
				return
			
			_, err = await self.defined_channels[msg.ChannelName].channel_init_internal(msg.ChannelId, self)
			if err is not None:
				logger.debug('Channel initialization failed! Error: %s' % err)
				await self.send_channel_create_response(msg.ChannelId, result = 0xC0000001) #STATUS_UNSUCCESSFUL
				return
				
			self.channels[msg.ChannelId] = self.defined_channels[msg.ChannelName]
			await self.send_channel_create_response(msg.ChannelId, result = 0) #STATUS_SUCCESS
			return

		elif msg.cmd == DYNVC_CMD.DATA_FIRST:
			if msg.ChannelId not in self.channels:
				logger.debug('DATA arrived for unknown channel %s' % msg.ChannelId)
				return
			await self.channels[msg.ChannelId].channel_rawdata_in(msg)
		elif msg.cmd == DYNVC_CMD.DATA:
			if msg.ChannelId not in self.channels:
				logger.debug('DATA arrived for unknown channel %s' % msg.ChannelId)
				return
			await self.channels[msg.ChannelId].channel_rawdata_in(msg)

		elif msg.cmd == DYNVC_CMD.CLOSE:
			if msg.ChannelId not in self.channels:
				logger.debug('CLOSE arrived for unknown channel %s' % msg.ChannelId)
				return
			await self.channels[msg.ChannelId].channel_closed()
		
		elif msg.cmd in [DYNVC_CMD.DATA_FIRST_COMPRESSED, DYNVC_CMD.DATA_COMPRESSED]:
			logger.debug('Compressed data recieved! Currently compression is not supported!')
		
		elif msg.cmd in [DYNVC_CMD.SOFT_SYNC_REQUEST, DYNVC_CMD.SOFT_SYNC_REQUEST]:
			logger.debug('Softsync packets are currently not supported')
		
		else:
			logger.debug('Unknown message type of %s recieved!' % msg.cmd)

	async def fragment_and_send(self, data):
		try:
			if len(data) < 16000:
				if self.compression_needed is False:
					flags = CHANNEL_FLAG.CHANNEL_FLAG_FIRST|CHANNEL_FLAG.CHANNEL_FLAG_LAST #|CHANNEL_FLAG.CHANNEL_FLAG_SHOW_PROTOCOL
					packet = CHANNEL_PDU_HEADER.serialize_packet(flags, data)
				else:
					raise NotImplementedError('Compression not implemented!')
			else:
				raise NotImplementedError('Chunked send not implemented!')
			
			sec_hdr = None
			if self.connection.cryptolayer is not None:
				sec_hdr = TS_SECURITY_HEADER()
				sec_hdr.flags = SEC_HDR_FLAG.ENCRYPT
				sec_hdr.flagsHi = 0

			await self.send_channel_data(packet, sec_hdr, None, None, False)

			return True, False
		except Exception as e:
			traceback.print_exc()
			return None,e