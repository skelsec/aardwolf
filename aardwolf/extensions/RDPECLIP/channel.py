
import asyncio
import traceback
import enum
import datetime

from aardwolf import logger
from aardwolf.channels import Channel
from aardwolf.protocol.T124.userdata.constants import ChannelOption
from aardwolf.extensions.RDPECLIP.protocol import *
from aardwolf.extensions.RDPECLIP.protocol.clipboardcapabilities import CLIPRDR_GENERAL_CAPABILITY, CB_GENERAL_FALGS
from aardwolf.protocol.channelpdu import CHANNEL_PDU_HEADER, CHANNEL_FLAG
from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT,CLIPRDR_SHORT_FORMAT_NAME, CLIPRDR_LONG_FORMAT_NAME
from aardwolf.commons.queuedata import RDP_CLIPBOARD_NEW_DATA_AVAILABLE, RDP_CLIPBOARD_READY, RDPDATATYPE
from aardwolf.commons.queuedata.clipboard import RDP_CLIPBOARD_DATA_TXT
from aardwolf.protocol.T128.security import TS_SECURITY_HEADER,SEC_HDR_FLAG

class CLIPBRDSTATUS(enum.Enum):
	WAITING_SERVER_INIT = enum.auto()
	CLIENT_INIT = enum.auto()
	RUNNING = enum.auto()


class RDPECLIPChannel(Channel):
	name = 'cliprdr'
	def __init__(self, iosettings):
		Channel.__init__(self, self.name, ChannelOption.INITIALIZED|ChannelOption.ENCRYPT_RDP|ChannelOption.COMPRESS_RDP|ChannelOption.SHOW_PROTOCOL)
		self.iosettings = iosettings
		self.use_pyperclip = iosettings.clipboard_use_pyperclip
		self.status = CLIPBRDSTATUS.WAITING_SERVER_INIT
		self.compression_needed = False #TODO: tie it to flags
		self.supported_formats = [CLIPBRD_FORMAT.CF_UNICODETEXT] #, CLIPBRD_FORMAT.CF_HDROP
		self.server_caps = None
		self.server_general_caps = None
		self.client_general_caps_flags = CB_GENERAL_FALGS.HUGE_FILE_SUPPORT_ENABLED | CB_GENERAL_FALGS.FILECLIP_NO_FILE_PATHS | CB_GENERAL_FALGS.STREAM_FILECLIP_ENABLED #| CB_GENERAL_FALGS.USE_LONG_FORMAT_NAMES # CB_GENERAL_FALGS.CAN_LOCK_CLIPDATA | #| CB_GENERAL_FALGS.USE_LONG_FORMAT_NAMES
		self.current_server_formats = {}
		self.__requested_format = None
		self.__current_clipboard_data:RDP_CLIPBOARD_DATA_TXT = None
		self.__channel_fragment_buffer = b''
		self.__channel_writer_lock = asyncio.Lock()

	async def start(self):
		try:
			if self.use_pyperclip is True:
				try:
					import pyperclip
				except ImportError:
					logger.debug('Could not import pyperclip! Copy-paste will not work!')
					self.use_pyperclip = False
				else:
					if not pyperclip.is_available():
						logger.debug("pyperclip - Copy functionality available!")
			
			return True, None
		except Exception as e:
			return None, e

	async def stop(self):
		try:				
			return True, None
		except Exception as e:
			return None, e

	async def __send_capabilities(self):
		# server sent monitor ready, now we must send our capabilites
		try:
			# sending capabilities
			gencap = CLIPRDR_GENERAL_CAPABILITY()
			gencap.generalFlags = self.client_general_caps_flags

			caps = CLIPRDR_CAPS()
			caps.capabilitySets.append(gencap)

			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_CLIP_CAPS, 0, caps)
			await self.fragment_and_send(msg)

			## if remote drive is attached this should be sent
			# sending tempdir location
			# tempdir = CLIPRDR_TEMP_DIRECTORY()
			# tempdir.wszTempDir = 'C:\\Windows\\Temp\\'
			# msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_TEMP_DIRECTORY, 0, tempdir)
			# await self.fragment_and_send(msg)

			# synchronizing formatlist
			fmtl = CLIPRDR_FORMAT_LIST()
			for reqfmt in self.supported_formats:
				fe = CLIPRDR_LONG_FORMAT_NAME()
				fe.formatId = reqfmt
				fmtl.templist.append(fe)

			self.status = CLIPBRDSTATUS.CLIENT_INIT
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_LIST, 0, fmtl)
			await self.fragment_and_send(msg)
		
			return True, None
		except Exception as e:
			return None, e
	
	async def __process_in(self, hdr:CLIPRDR_HEADER, payload:bytes):
		try:
			#hdr = CLIPRDR_HEADER.from_bytes(self.__buffer)

			if self.status == CLIPBRDSTATUS.RUNNING:
				#print(hdr.msgType)
				if hdr.msgType == CB_TYPE.CB_FORMAT_LIST:
					fmtl = CLIPRDR_FORMAT_LIST.from_bytes(payload[:hdr.dataLen], longnames=CB_GENERAL_FALGS.USE_LONG_FORMAT_NAMES in self.client_general_caps_flags, encoding='ascii' if CB_FLAG.CB_ASCII_NAMES in hdr.msgFlags else 'utf-16-le')
					
					self.current_server_formats = {}
					for fmte in fmtl.templist:
						self.current_server_formats[fmte.formatId] = fmte
					
					# sending back an OK
					msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_LIST_RESPONSE, CB_FLAG.CB_RESPONSE_OK, None)
					await self.fragment_and_send(msg)

					if CLIPBRD_FORMAT.CF_UNICODETEXT in self.current_server_formats.keys():
						# pyperclip is in use and server just notified us about a new text copied, so we request the text
						# automatically
						self.__requested_format = CLIPBRD_FORMAT.CF_UNICODETEXT
						dreq = CLIPRDR_FORMAT_DATA_REQUEST()
						dreq.requestedFormatId = CLIPBRD_FORMAT.CF_UNICODETEXT
						msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_DATA_REQUEST, 0, dreq)
						await self.fragment_and_send(msg)

						# notifying client that new data is available
						msg = RDP_CLIPBOARD_NEW_DATA_AVAILABLE()
						await self.send_user_data(msg)

				
				elif hdr.msgType == CB_TYPE.CB_FORMAT_DATA_RESPONSE:
					if hdr.msgFlags != hdr.msgFlags.CB_RESPONSE_OK:
						logger.debug('Server rejected our copy request!')
					else:
						try:
							fmtdata = CLIPRDR_FORMAT_DATA_RESPONSE.from_bytes(payload[:hdr.dataLen],otype=self.__requested_format)
						
							if self.use_pyperclip is True and self.__requested_format in [CLIPBRD_FORMAT.CF_TEXT, CLIPBRD_FORMAT.CF_UNICODETEXT]:
								import pyperclip
								#print(fmtdata.dataobj)
								pyperclip.copy(fmtdata.dataobj)
							
							if self.iosettings.clipboard_store_data is True or isinstance(self.iosettings.clipboard_store_data, str) is True:
								fname = self.iosettings.clipboard_store_data
								if self.iosettings.clipboard_store_data is True or len(fname) == 0:
									fname = 'clipboard_%s.txt' % (datetime.datetime.utcnow().strftime("%Y_%m_%d_%H%MZ"))
								with open(fname, 'a+') as f:
									f.write(str(fmtdata.dataobj))

							msg = RDP_CLIPBOARD_DATA_TXT()
							msg.data = fmtdata.dataobj
							msg.datatype = self.__requested_format
							await self.send_user_data(msg)
							self.__current_clipboard_data = msg
						
						except Exception as e:
							raise e
						finally:
							self.__requested_format = None
				
				elif hdr.msgType == CB_TYPE.CB_FORMAT_DATA_REQUEST:

					fmtr = CLIPRDR_FORMAT_DATA_REQUEST.from_bytes(payload[:hdr.dataLen])
					if fmtr.requestedFormatId == self.__current_clipboard_data.datatype:
						resp = CLIPRDR_FORMAT_DATA_RESPONSE()
						resp.dataobj = self.__current_clipboard_data.data
						resp = resp.to_bytes(self.__current_clipboard_data.datatype)

						
						msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_DATA_RESPONSE, CB_FLAG.CB_RESPONSE_OK, resp)
						#print('setting clipboard text! %s' % repr(msg))
						await self.fragment_and_send(msg)
					
					else:
						logger.debug('Server requested a formatid which we dont have. %s' % fmtr.requestedFormatId)
						
			
			elif self.status == CLIPBRDSTATUS.WAITING_SERVER_INIT:
				# we expect either CLIPRDR_CAPS or CLIPRDR_MONITOR_READY
				if hdr.msgType == CB_TYPE.CB_CLIP_CAPS:
					self.server_caps = CLIPRDR_CAPS.from_bytes(payload[:hdr.dataLen])
					self.server_general_caps = self.server_caps.capabilitySets[0] #it's always the generalflags
					logger.debug(self.server_general_caps)
				elif hdr.msgType == CB_TYPE.CB_MONITOR_READY:
					_, err = await self.__send_capabilities()
					if err is not None:
						raise err
				else:
					raise Exception('Unexpected packet type %s arrived!' % hdr.msgType.name)

				#await self.out_queue.put((data, err))
			elif self.status == CLIPBRDSTATUS.CLIENT_INIT:
				# initialization started, we already sent all necessary data
				# here we expect CB_FORMAT_LIST_RESPONSE
				if hdr.msgType == CB_TYPE.CB_FORMAT_LIST_RESPONSE:
					#this doesnt hold any data
					if CB_FLAG.CB_RESPONSE_OK in hdr.msgFlags:
						# everything was okay, now we can communicate on this channel normally
						# also we have to notify the client that they can use the keyboard now
						self.status = CLIPBRDSTATUS.RUNNING
						msg = RDP_CLIPBOARD_READY()
						await self.send_user_data(msg)

					elif CB_FLAG.CB_RESPONSE_FAIL in hdr.msgFlags:
						raise Exception('Server refused clipboard initialization!')
					else:
						raise Exception('Server sent unexpected data! %s' % hdr)
				


			#self.__buffer = self.__buffer[8+hdr.dataLen:]
			return True, None
		except Exception as e:
			return None, e

	async def process_channel_data(self, data):
		channeldata = CHANNEL_PDU_HEADER.from_bytes(data)
		data = data[8:] #discarding the lower layer headers
		if CHANNEL_FLAG.CHANNEL_FLAG_FIRST in channeldata.flags:
			self.__channel_fragment_buffer = b''

		self.__channel_fragment_buffer += data
		if CHANNEL_FLAG.CHANNEL_FLAG_LAST in channeldata.flags:
			hdr = CLIPRDR_HEADER.from_bytes(self.__channel_fragment_buffer)
			_, err = await self.__process_in(hdr, self.__channel_fragment_buffer[8:])
			if err is not None:
				raise err
	
	async def fragment_and_send(self, data):
		async with self.__channel_writer_lock:
			try:
				if self.compression_needed is True:
					raise NotImplementedError('Compression not implemented!')
				i = 0
				while(i <= len(data)):
					flags = CHANNEL_FLAG.CHANNEL_FLAG_SHOW_PROTOCOL
					chunk = data[i:i+1400]
					if i == 0:
						flags |= CHANNEL_FLAG.CHANNEL_FLAG_FIRST
						# the first fragment must contain the length of the total data we want to send
						length = len(data)
					else:
						# if it's not the first fragment then the length equals to the chunk's length
						length = None
					
					i+= 1400
					if i >= len(data):
						flags |= CHANNEL_FLAG.CHANNEL_FLAG_LAST
					packet = CHANNEL_PDU_HEADER.serialize_packet(flags, chunk, length = length)

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
	
	async def get_current_clipboard_text(self):
		if self.__current_clipboard_data is None:
			return ''
		return str(self.__current_clipboard_data.data)

	async def set_current_clipboard_text(self, text:str):
		data = RDP_CLIPBOARD_DATA_TXT()
		data.datatype = CLIPBRD_FORMAT.CF_UNICODETEXT
		data.data = text
		await self.set_clipboard_data(data)
	

	async def set_clipboard_data(self, data, force_refresh = True):
		if data == self.__current_clipboard_data and force_refresh is False:
			return

		fmtl = CLIPRDR_FORMAT_LIST()
		for fmtid in [CLIPBRD_FORMAT.CF_UNICODETEXT]: #CLIPBRD_FORMAT.CF_TEXT, CLIPBRD_FORMAT.CF_OEMTEXT
			if CB_GENERAL_FALGS.USE_LONG_FORMAT_NAMES not in self.server_general_caps.generalFlags:
				name = CLIPRDR_LONG_FORMAT_NAME()
				name.formatId = data.datatype
			else:
				name = CLIPRDR_SHORT_FORMAT_NAME()
				name.formatId = data.datatype
			fmtl.templist.append(name)
		msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_LIST, 0, fmtl)
		await self.fragment_and_send(msg)

		self.__current_clipboard_data = data

	async def process_user_data(self, data):
		#print('clipboard out! %s' % data)
		if data.type == RDPDATATYPE.CLIPBOARD_DATA_TXT:
			await self.set_clipboard_data(data, False)
				
		else:
			logger.debug('Unhandled data type in! %s' % data.type)