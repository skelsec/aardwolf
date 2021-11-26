
import asyncio
import traceback
import typing

from asn1tools.codecs import restricted_utc_time_from_datetime

from aardwolf.protocol.T124.userdata.constants import ChannelOption
from aardwolf.protocol.T128.share import TS_SHARECONTROLHEADER, PDUTYPE
from aardwolf.protocol.T128.security import TS_SECURITY_HEADER,SEC_HDR_FLAG, TS_SECURITY_HEADER1

class Channel:
	def __init__(self, name, options = ChannelOption.INITIALIZED|ChannelOption.ENCRYPT_RDP):
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
			if self.monitor_data_task is not None:
				self.monitor_data_task.cancel()
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
			self.monitor_data_task = asyncio.create_task(self.__monitor_data_out())
			_, err = await self.start()
			if err is not None:
				raise err
			return True, None
		except Exception as e:
			return None, e


	async def start(self):
		try:
			return True, None

		except Exception as e:
			return None, e

	async def monitor_in(self):
		try:
			while True:
				data, err = await self.raw_in_queue.get()
				#if data is not None:
				#	if self.connection.cryptolayer is not None:
				#		sec_hdr = TS_SECURITY_HEADER1.from_bytes(data)
				#		print(sec_hdr)
				#		if SEC_HDR_FLAG.ENCRYPT in sec_hdr.flags:
				#			orig_data = data[12:]
				#			data = self.connection.cryptolayer.client_dec(orig_data)
				#			if SEC_HDR_FLAG.SECURE_CHECKSUM in sec_hdr.flags:
				#				mac = self.connection.cryptolayer.calc_salted_mac(data, is_server=True)
				#			else:
				#				mac = self.connection.cryptolayer.calc_mac(data)
				#			if mac != sec_hdr.dataSignature:
				#				print('ERROR! Signature mismatch! Printing debug data')
				#				print('Encrypted data: %s' % orig_data)
				#				print('Decrypted data: %s' % data)
				#				print('Original MAC  : %s' % sec_hdr.dataSignature)
				#				print('Calculated MAC: %s' % mac)
						
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
	
	async def __monitor_data_out(self):
		try:
			while True:
				dataobj, sec_hdr, datacontrol_hdr, sharecontrol_hdr  = await self.data_in_queue.get()
				#print('Sending data on channel "%s(%s)"' % (self.name, self.channel_id))
				data = dataobj.to_bytes()
				hdrs = b''
				if sharecontrol_hdr is not None:
					sharecontrol_hdr.pduSource = self.channel_id
					sharecontrol_hdr.totalLength = len(data) + 6
					hdrs += sharecontrol_hdr.to_bytes()

				elif datacontrol_hdr is not None:
					datacontrol_hdr.shareControlHeader = TS_SHARECONTROLHEADER()
					datacontrol_hdr.shareControlHeader.pduType = PDUTYPE.DATAPDU
					datacontrol_hdr.shareControlHeader.pduSource = self.channel_id
					datacontrol_hdr.shareControlHeader.totalLength = len(data) + 24
					datacontrol_hdr.uncompressedLength = len(data) + 24 # since there is no compression implemented yet
					datacontrol_hdr.compressedType = 0
					datacontrol_hdr.compressedLength = 0
					hdrs += datacontrol_hdr.to_bytes()
				if sec_hdr is not None:
					sec_hdr = typing.cast(TS_SECURITY_HEADER, sec_hdr)
					if SEC_HDR_FLAG.ENCRYPT in sec_hdr.flags:
						#print('PacketCount: %s' % self.connection.cryptolayer.PacketCount)
						data = hdrs+data
						

						if self.connection.cryptolayer.use_encrypted_mac is True:
							checksum = self.connection.cryptolayer.calc_salted_mac(data)
							sec_hdr.flags |= SEC_HDR_FLAG.SECURE_CHECKSUM
						else:
							checksum = self.connection.cryptolayer.calc_mac(data)
						
						# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/9791c9e2-e5be-462f-8c23-3404c4af63b3
						enc_data = self.connection.cryptolayer.client_enc(data)
						
						data = checksum + enc_data
						hdrs = sec_hdr.to_bytes()
					else:
						hdrs += sec_hdr.to_bytes()
				userdata = hdrs + data
				data_wrapper = {
				'initiator': self.connection._initiator, 
				'channelId': self.channel_id, 
				'dataPriority': 'high', 
				'segmentation': (b'\xc0', 2), 
				'userData': userdata
				}
				userdata_wrapped = self.connection._t125_per_codec.encode('DomainMCSPDU', ('sendDataRequest', data_wrapper))
				await self.raw_out_queue.put(userdata_wrapped)

		except asyncio.CancelledError:
			return None, None

		except Exception as e:
			traceback.print_exc()
			return None, e
