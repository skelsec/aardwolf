
import asyncio
import traceback
import enum
import datetime

from aardwolf import logger
from aardwolf.channels import Channel
from aardwolf.protocol.T124.userdata.constants import ChannelOption
from aardwolf.extensions.RDPECLIP.protocol import *
from aardwolf.extensions.RDPECLIP.protocol.clipboardcapabilities import CLIPRDR_GENERAL_CAPABILITY, CB_GENERAL_FLAGS
from aardwolf.protocol.channelpdu import CHANNEL_PDU_HEADER, CHANNEL_FLAG
from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT,CLIPRDR_SHORT_FORMAT_NAME, CLIPRDR_LONG_FORMAT_NAME
from aardwolf.commons.queuedata import RDP_CLIPBOARD_FORMAT_LIST_RESPONSE, RDP_CLIPBOARD_NEW_DATA_AVAILABLE, RDP_CLIPBOARD_READY, RDPDATATYPE
from aardwolf.commons.queuedata.clipboard import RDP_CLIPBOARD_DATA, RDP_CLIPBOARD_DATA_TXT, RDP_CLIPBOARD_DATA_FILELIST
from aardwolf.extensions.RDPECLIP.protocol.formatdataresponse import CLIPRDR_FILELIST
from aardwolf.extensions.RDPECLIP.protocol.filecontentsresponse import CLIPRDR_FILECONTENTS_RESPONSE
from aardwolf.extensions.RDPECLIP.protocol.filecontentsrequest import CLIPRDR_FILECONTENTS_REQUEST, FILECONTENTS_FLAG
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
		self.clipboard = iosettings.clipboard
		self.use_pyperclip = iosettings.clipboard_use_pyperclip
		self.status = CLIPBRDSTATUS.WAITING_SERVER_INIT
		self.compression_needed = False #TODO: tie it to flags
		self.server_caps = None
		self.server_general_caps = None
		self.client_general_caps_flags = CB_GENERAL_FLAGS.USE_LONG_FORMAT_NAMES | CB_GENERAL_FLAGS.HUGE_FILE_SUPPORT_ENABLED | CB_GENERAL_FLAGS.FILECLIP_NO_FILE_PATHS | CB_GENERAL_FLAGS.STREAM_FILECLIP_ENABLED # | CB_GENERAL_FLAGS.CAN_LOCK_CLIPDATA
		self.negotiated_general_caps_flags = CB_GENERAL_FLAGS(0)
		self.current_server_formats = {}
		self.__requested_format = None
		self.__channel_fragment_buffer = b''
		self.__channel_writer_lock = asyncio.Lock()

		# inbound file download (server -> client) state
		self.__server_file_format_id = None
		self.__requesting_file_list = False
		self.__next_stream_id = 0
		self.__filecontents_futures = {}  # streamId -> asyncio.Future
		self.__filecontents_is_size = {}  # streamId -> bool
		self.__filecontents_timeout = 30

		self.clipboard.register_handler(self)

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
			self.clipboard.unregister_handler(self)
			return True, None
		except Exception as e:
			return None, e

	async def __send_capabilities(self):
		# server sent monitor ready, now we must send our capabilites
		try:
			# sending capabilities
			gencap = CLIPRDR_GENERAL_CAPABILITY()
			if self.server_general_caps is None:
				# Server capabilities are optional. If omitted, MS-RDPECLIP
				# defines default capabilities with generalFlags set to zero.
				self.negotiated_general_caps_flags = CB_GENERAL_FLAGS(0)
			else:
				self.negotiated_general_caps_flags = self.client_general_caps_flags & self.server_general_caps.generalFlags
			gencap.generalFlags = self.negotiated_general_caps_flags

			logger.debug(f'Sending capabilities: {repr(gencap.generalFlags)}')

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
			for reqfmt, name in self.clipboard.formats.items():
				fe = self._generate_format_name(reqfmt, name)
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
					encoding = 'ascii' if CB_FLAG.CB_ASCII_NAMES in hdr.msgFlags else 'utf-16-le'
					fmtl = CLIPRDR_FORMAT_LIST.from_bytes(payload[:hdr.dataLen], longnames=self._longnames_enabled(), encoding=encoding)
					await self._handle_format_list(fmtl)
				elif hdr.msgType == CB_TYPE.CB_FILECONTENTS_REQUEST:
					fileContentsRequest = CLIPRDR_FILECONTENTS_REQUEST.from_bytes(payload[:hdr.dataLen])
					await self._handle_filecontents_request(fileContentsRequest)
				elif hdr.msgType == CB_TYPE.CB_FILECONTENTS_RESPONSE:
					await self._handle_filecontents_response(hdr, payload[:hdr.dataLen])
				elif hdr.msgType == CB_TYPE.CB_FORMAT_DATA_RESPONSE:
					if hdr.msgFlags != hdr.msgFlags.CB_RESPONSE_OK:
						logger.debug('Server rejected our copy request!')
						self.__requesting_file_list = False
						self.__requested_format = None
					elif self.__requesting_file_list is True:
						try:
							filelist = CLIPRDR_FILELIST.from_bytes(payload[:hdr.dataLen])
							await self._handle_remote_file_list(filelist)
						finally:
							self.__requesting_file_list = False
							self.__requested_format = None
					else:
						try:
							fmtdata = CLIPRDR_FORMAT_DATA_RESPONSE.from_bytes(payload[:hdr.dataLen],otype=self.__requested_format)
							await self._handle_format_data_response(fmtdata)
						
						except Exception as e:
							raise e
						finally:
							self.__requested_format = None
				
				elif hdr.msgType == CB_TYPE.CB_FORMAT_DATA_REQUEST:
					fmtr = CLIPRDR_FORMAT_DATA_REQUEST.from_bytes(payload[:hdr.dataLen])
					await self._handle_format_data_request(fmtr)
				elif hdr.msgType == CB_TYPE.CB_FORMAT_LIST_RESPONSE:
					if CB_FLAG.CB_RESPONSE_OK in hdr.msgFlags:
						logger.debug('Server accepted our copy request!')
						await self.send_user_data(RDP_CLIPBOARD_FORMAT_LIST_RESPONSE(True))
					else:
						logger.debug('Server rejected our copy request!')
						await self.send_user_data(RDP_CLIPBOARD_FORMAT_LIST_RESPONSE(False))
			
			elif self.status == CLIPBRDSTATUS.WAITING_SERVER_INIT:
				# we expect either CLIPRDR_CAPS or CLIPRDR_MONITOR_READY
				if hdr.msgType == CB_TYPE.CB_CLIP_CAPS:
					self.server_caps = CLIPRDR_CAPS.from_bytes(payload[:hdr.dataLen])
					if self.server_caps.capabilitySets:
						self.server_general_caps = self.server_caps.capabilitySets[0]
					logger.debug(f'Received server capabilities: {self.server_general_caps}')
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
		
	def _longnames_enabled(self) -> bool:
		return CB_GENERAL_FLAGS.USE_LONG_FORMAT_NAMES in self.negotiated_general_caps_flags

	def _get_format_name(self, format) -> str:
		if self._longnames_enabled():
			return format.wszFormatName
		else:
			return format.formatName
		
	def _generate_format_name(self, format_id, format_name, use_ascii = False):
		if self._longnames_enabled():
			fe = CLIPRDR_LONG_FORMAT_NAME()
			fe.formatId = format_id
			fe.wszFormatName = format_name
			return fe
		else:
			encoding = 'ascii' if use_ascii else 'utf-16-le'
			fe = CLIPRDR_SHORT_FORMAT_NAME(encoding=encoding)
			fe.formatId = format_id
			fe.formatName = format_name
			return fe

	async def _handle_format_list(self, fmtl:CLIPRDR_FORMAT_LIST):
		self.current_server_formats = {}
		for fmte in fmtl.templist:
			# key by the real numeric id (clpfmt); the parsed formatId collapses
			# to CLIPBRD_FORMAT.UNKNOWN for any dynamically registered format
			# (e.g. FileGroupDescriptorW), which would otherwise collide
			self.current_server_formats[fmte.clpfmt] = fmte

			# Lookup format name in clipboard formats?
			if fmte.clpfmt not in self.clipboard.formats:
				format_name = self._get_format_name(fmte)
				logger.debug(f'Received unknown format: {format_name} with id {fmte.formatId} -> {fmte.clpfmt}')
		
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
			return

		# detect the server advertising files via the FileGroupDescriptorW format
		self.__server_file_format_id = self._find_server_format_id('FileGroupDescriptorW')
		if self.__server_file_format_id is not None:
			# request the file descriptor list so the caller can choose what to download
			self.__requested_format = self.__server_file_format_id
			self.__requesting_file_list = True
			dreq = CLIPRDR_FORMAT_DATA_REQUEST()
			dreq.requestedFormatId = self.__server_file_format_id
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_DATA_REQUEST, 0, dreq)
			await self.fragment_and_send(msg)

	async def _handle_filecontents_request(self, fileContentsRequest:CLIPRDR_FILECONTENTS_REQUEST):
		# Paste: The remote machine is requesting the contents of a file
		logger.debug(f'Server requested file contents for index {fileContentsRequest.lindex}!')
		if fileContentsRequest.dwFlags == FILECONTENTS_FLAG.FILECONTENTS_SIZE:
			logger.debug('Server requested file size')
			resp = CLIPRDR_FILECONTENTS_RESPONSE(is_size=True)
			resp.streamId = fileContentsRequest.streamId
			resp.requestedFileContentsData = self.clipboard.get_file_size(fileContentsRequest.lindex)
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FILECONTENTS_RESPONSE, CB_FLAG.CB_RESPONSE_OK, resp)
			await self.fragment_and_send(msg)
		elif fileContentsRequest.dwFlags == FILECONTENTS_FLAG.FILECONTENTS_RANGE:
			logger.debug(f'Server requested up to {fileContentsRequest.cbRequested} bytes in range ({fileContentsRequest.nPositionLow}-{fileContentsRequest.nPositionHigh})')
			resp = CLIPRDR_FILECONTENTS_RESPONSE(is_size=False)
			resp.streamId = fileContentsRequest.streamId
			resp.requestedFileContentsData = self.clipboard.get_file_data(fileContentsRequest.lindex, fileContentsRequest.nPositionLow, fileContentsRequest.cbRequested)
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FILECONTENTS_RESPONSE, CB_FLAG.CB_RESPONSE_OK, resp)
			await self.fragment_and_send(msg)
		else: 
			logger.debug('Bad server request.')
			resp = CLIPRDR_FILECONTENTS_RESPONSE(is_size=False)
			resp.streamId = fileContentsRequest.streamId
			resp.requestedFileContentsData = b''
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FILECONTENTS_RESPONSE, CB_FLAG.CB_RESPONSE_FAIL, resp)
			await self.fragment_and_send(msg)

	def _find_server_format_id(self, format_name:str):
		# returns the real numeric format id (clpfmt) the server advertised for
		# the given name, or None. We must use clpfmt (not the parsed formatId,
		# which is UNKNOWN for dynamically registered formats) since this id is
		# echoed back in the CB_FORMAT_DATA_REQUEST.
		for fmte in self.current_server_formats.values():
			if self._get_format_name(fmte) == format_name:
				return fmte.clpfmt
		return None

	async def _handle_remote_file_list(self, filelist:CLIPRDR_FILELIST):
		# Download: the server advertised a list of files, store it and notify the client
		logger.debug(f'Received remote file list with {len(filelist.fileDescriptorArray)} entries')
		self.clipboard.set_remote_file_list(filelist)
		msg = RDP_CLIPBOARD_DATA_FILELIST(data=filelist, datatype=self.__server_file_format_id)
		await self.send_user_data(msg)
		# also notify via the generic "new data available" event
		await self.send_user_data(RDP_CLIPBOARD_NEW_DATA_AVAILABLE())

	async def _handle_filecontents_response(self, hdr:CLIPRDR_HEADER, payload:bytes):
		# Download: the server responded to one of our CB_FILECONTENTS_REQUESTs
		streamId = int.from_bytes(payload[:4], byteorder='little', signed=False)
		future = self.__filecontents_futures.get(streamId)
		if future is None:
			logger.debug('Received CB_FILECONTENTS_RESPONSE for unknown streamId %s' % streamId)
			return
		if future.done():
			return
		if CB_FLAG.CB_RESPONSE_OK not in hdr.msgFlags:
			future.set_exception(Exception('Server rejected file contents request (streamId %s)' % streamId))
			return
		is_size = self.__filecontents_is_size.get(streamId, False)
		resp = CLIPRDR_FILECONTENTS_RESPONSE.from_bytes(payload, is_size)
		future.set_result(resp.requestedFileContentsData)

	async def request_file_contents(self, lindex:int, dwFlags:FILECONTENTS_FLAG, nPosition:int = 0, cbRequested:int = 0):
		# Download: ask the server for either the size or a byte range of a remote file.
		# Returns an int (size) when dwFlags is FILECONTENTS_SIZE, otherwise the raw bytes.
		streamId = self.__next_stream_id
		self.__next_stream_id += 1

		req = CLIPRDR_FILECONTENTS_REQUEST()
		req.streamId = streamId
		req.lindex = lindex
		req.dwFlags = dwFlags
		req.nPosition = nPosition
		req.cbRequested = cbRequested if dwFlags == FILECONTENTS_FLAG.FILECONTENTS_RANGE else 8

		future = asyncio.get_event_loop().create_future()
		self.__filecontents_futures[streamId] = future
		self.__filecontents_is_size[streamId] = (dwFlags == FILECONTENTS_FLAG.FILECONTENTS_SIZE)
		try:
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FILECONTENTS_REQUEST, 0, req)
			await self.fragment_and_send(msg)
			return await asyncio.wait_for(future, timeout=self.__filecontents_timeout)
		finally:
			self.__filecontents_futures.pop(streamId, None)
			self.__filecontents_is_size.pop(streamId, None)

	async def _handle_format_data_request(self, fmtr:CLIPRDR_FORMAT_DATA_REQUEST):
		# Paste: The remote machine is requesting clipboard data
		logger.debug(f'Got a CB_FORMAT_DATA_REQUEST for formatid {fmtr.requestedFormatId}')
		if self.clipboard.data is not None and fmtr.requestedFormatId == self.clipboard.data.datatype:
			resp = CLIPRDR_FORMAT_DATA_RESPONSE()
			resp.dataobj = self.clipboard.data.data
			resp = resp.to_bytes(self.clipboard.data.datatype)
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_DATA_RESPONSE, CB_FLAG.CB_RESPONSE_OK, resp)
			await self.fragment_and_send(msg)
		
		else:
			# We either have no clipboard data yet, or we don't hold the format
			# the server asked for (we advertise all formats in our capabilities,
			# and remote-side clipboard activity can race our local data). Reply
			# with a FAIL response so the server stops waiting instead of letting
			# the unhandled request tear down the whole RDP connection.
			logger.debug('Server requested a formatid which we dont have. %s' % fmtr.requestedFormatId)
			msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_DATA_RESPONSE, CB_FLAG.CB_RESPONSE_FAIL, None)
			await self.fragment_and_send(msg)

	async def _handle_format_data_response(self, fmtdata:CLIPRDR_FORMAT_DATA_RESPONSE):
		# Paste: The remote machine has responded to our request for clipboard data
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

		msg = RDP_CLIPBOARD_DATA_TXT(data=fmtdata.dataobj, datatype=self.__requested_format)
		await self.send_user_data(msg)
		self.clipboard.data = msg

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
	
	async def _send_format_list(self, data:RDP_CLIPBOARD_DATA):
		fmtl = CLIPRDR_FORMAT_LIST()
		name = self._generate_format_name(data.datatype, self.clipboard.formats[data.datatype])
		fmtl.templist.append(name)
		msg = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_FORMAT_LIST, 0, fmtl)
		logger.debug(f'Sending CB_FORMAT_LIST: {repr(fmtl)}')
		logger.debug(f'Serialized message: {msg.hex()}')
		await self.fragment_and_send(msg)

	async def process_user_data(self, data):
		#print('clipboard out! %s' % data)
		if data.type == RDPDATATYPE.CLIPBOARD_DATA_TXT:
			await self.clipboard.set_data(data, False)
				
		else:
			logger.debug('Unhandled data type in! %s' % data.type)

	async def on_copy(self, data:RDP_CLIPBOARD_DATA):
		await self._send_format_list(data)
