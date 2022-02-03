
import asyncio
import os
import io
from sys import byteorder
import traceback
from struct import pack, unpack
from typing import cast

from aardwolf import logger
from aardwolf.network.selector import NetworkSelector
from aardwolf.transport.tcpstream import TCPStream
from aardwolf.crypto.symmetric import DES
from aardwolf.crypto.BASE import cipherMODE

from aardwolf.commons.queuedata import *

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
import rle

# https://datatracker.ietf.org/doc/html/rfc6143

RAW_ENCODING = 0
COPY_RECTANGLE_ENCODING = 1
RRE_ENCODING = 2
CORRE_ENCODING = 4
HEXTILE_ENCODING = 5
ZLIB_ENCODING = 6
TIGHT_ENCODING = 7
ZLIBHEX_ENCODING = 8
TRLE_ENCODING = 15
ZRLE_ENCODING = 16

class VNCConnection:
	def __init__(self, target, credentials, iosettings):
		self.target = target
		self.credentials = credentials
		self.authapi = None
		self.iosettings = iosettings
		self.shared_flag = False
		self.client_version = '003.008'
		self.server_version = None
		self.server_name = None
		self.disconnected_evt = asyncio.Event() #this will be set if we disconnect for whatever reason
		self.server_supp_security_types = []
		self.__selected_security_type = 2

		# these are the main queues with which you can communicate with the server
		# ext_out_queue: yields video data
		# ext_in_queue: expects keyboard/mouse data
		self.ext_out_queue = asyncio.Queue()
		self.ext_in_queue = asyncio.Queue()

		self.__reader = None
		self.__writer = None


		self.bpp = None
		self.bypp = None
		self.depth = None
		self.bigendian = None
		self.truecolor = None 
		self.redmax = None 
		self.greenmax = None
		self.bluemax = None
		self.redshift = None 
		self.greenshift = None
		self.blueshift = None
		self.width = None
		self.height = None
		self.__desktop_buffer = None
		self.__frame_update_req_evt = asyncio.Event()

	
	async def terminate(self):
		try:			
			return True, None
		except Exception as e:
			traceback.print_exc()
			return None, e
		finally:
			self.disconnected_evt.set()
	
	async def __aenter__(self):
		return self
		
	async def __aexit__(self, exc_type, exc, traceback):
		await asyncio.wait_for(self.terminate(), timeout = 5)
	
	async def connect(self):
		"""
		Performs the entire connection sequence 
		"""
		try:
			# starting lower-layer transports 
			logger.debug('Selecting network')
			remote_socket, err = await NetworkSelector.select(self.target)
			if err is not None:
				raise err

			logger.debug('Connecting sockets')
			_, err = await remote_socket.connect()
			if err is not None:
				raise err
			
			logger.debug('Wrapping sockets to streamer')
			self.__reader, self.__writer = await TCPStream.from_tcpsocket(remote_socket)

			logger.debug('Performing banner exchange')
			_, err = await self.__banner_exchange()
			if err is not None:
				raise err
			logger.debug('Banner exchange OK')

			logger.debug('Performing security handshake')
			_, err = await self.__security_handshake()
			if err is not None:
				raise err
			logger.debug('Security handshake OK')
			
			logger.debug('Client init')
			_, err = await self.__client_init()
			if err is not None:
				raise err
			logger.debug('Client init OK')

			self.__reader_loop_task = asyncio.create_task(self.__reader_loop())
			self.__external_reader_task = asyncio.create_task(self.__external_reader())
			
			return True, None
		except Exception as e:
			self.disconnected_evt.set()
			return None, e
	
	async def __banner_exchange(self):
		try:
			banner = await self.__reader.readuntil(b'\n')
			self.server_version = banner[4:-1].decode()
			logger.debug('Server version: %s' % self.server_version)
			version_reply = b'RFB %s\n' % self.client_version.encode()
			logger.debug('Version reply: %s' % version_reply)
			self.__writer.write(version_reply)

			print(self.server_version)
			return True, None
		except Exception as e:
			return None, e

	async def __security_handshake(self):
		try:
			no_sec_types = await self.__reader.readexactly(1)
			no_sec_types = ord(no_sec_types)
			if no_sec_types == 0:
				logger.debug('Server sent empty support security types, connection will terminate soon')
				err_string_size = await self.__reader.readexactly(1)
				err_string_size = ord(err_string_size)
				err_string = await self.__reader.readexactly(err_string_size)
				err_string = err_string.decode()
				raise Exception(err_string)
			sec_types = await self.__reader.readexactly(no_sec_types)
			for sectype in sec_types:
				self.server_supp_security_types.append(sectype)
			
			if self.__selected_security_type == 2:
				logger.debug('Selecting default VNC auth type')
				self.__writer.write(bytes([self.__selected_security_type]))
				challenge = await self.__reader.readexactly(16)

				password = self.credentials.secret.ljust(8, '\x00').encode('ascii')
				print(password)
				# converting password to key
				newkey = b''
				for ki in range(len(password)):
					bsrc = password[ki]
					btgt = 0
					for i in range(8):
						if bsrc & (1 << i):
							btgt = btgt | (1 << 7 - i)
					newkey+= bytes([btgt])
				ctx = DES(newkey, mode = cipherMODE.ECB, IV = None)
				response = ctx.encrypt(challenge)
				print(response)
				self.__writer.write(response)

			else:
				raise Exception('Unsupported security type selected!')
			
			auth_result = await self.__reader.readexactly(4)
			auth_result = int.from_bytes(auth_result, byteorder = 'big', signed=False)
			if auth_result != 0:
				logger.debug('Auth Failed!')
				err_string_size = await self.__reader.readexactly(4)
				err_string_size = int.from_bytes(err_string_size, byteorder = 'big', signed=False)
				err_string = await self.__reader.readexactly(err_string_size)
				err_string = err_string.decode()
				raise Exception(err_string)
			logger.debug('Auth OK!')

			print(self.server_supp_security_types)
			return True, None
		except Exception as e:
			return None, e
	
	async def __client_init(self):
		try:
			# sending client init
			self.__writer.write(bytes([int(self.shared_flag)]))
			# reading server_init
			framebuffer_width = await self.__reader.readexactly(2)
			self.width = int.from_bytes(framebuffer_width, byteorder = 'big', signed = False)
			framebuffer_height = await self.__reader.readexactly(2)
			self.height = int.from_bytes(framebuffer_height, byteorder = 'big', signed = False)
			pixel_format_raw = await self.__reader.readexactly(16)
			self.bpp, self.depth, self.bigendian, self.truecolor, \
			self.redmax, self.greenmax, self.bluemax, self.redshift, \
			self.greenshift, self.blueshift = unpack("!BBBBHHHBBBxxx", pixel_format_raw)
			self.bypp = self.bpp // 8  # calc bytes per pixel

			name_string_size = await self.__reader.readexactly(4)
			name_string_size = int.from_bytes(name_string_size, byteorder = 'big', signed=False)
			name_string = await self.__reader.readexactly(name_string_size)
			self.server_name = name_string.decode()


			self.__desktop_buffer = Image.new(mode="RGBA", size=(self.width, self.height))
			_, err = await self.set_encodings()
			if err is not None:
				raise err

			await self.set_pixel_format()
			await self.framebuffer_update_request()
			await self.framebuffer_update_request(incremental = 1)
			
			asyncio.create_task(self.testloop())
			return True, None
		except Exception as e:
			return None, e

	async def __external_reader(self):
		# This coroutine handles keyboard/mouse etc input from the user
		# It wraps the data in it's appropriate format then dispatches it to the server
		try:
			while True:
				indata = await self.ext_in_queue.get()
				if indata is None:
					#signaling exit
					await self.terminate()
					return
				if indata.type == RDPDATATYPE.KEYSCAN:
					indata = cast(RDP_KEYBOARD_SCANCODE, indata)
					#await self.handle_out_data(cli_input, sec_hdr, data_hdr, None, self.__joined_channels['MCS'].channel_id, False)
				
				if indata.type == RDPDATATYPE.KEYUNICODE:
					indata = cast(RDP_KEYBOARD_UNICODE, indata)
					#await self.handle_out_data(cli_input, sec_hdr, data_hdr, None, self.__joined_channels['MCS'].channel_id, False)
			
				elif indata.type == RDPDATATYPE.MOUSE:
					#PointerEvent
					indata = cast(RDP_MOUSE, indata)
					if indata.xPos < 0 or indata.yPos < 0:
						continue
					
					#print('sending mouse!')
					msg = pack("!BBHH", 5, int(indata.pressed), indata.xPos, indata.yPos)
					self.__writer.write(msg)

				elif indata.type == RDPDATATYPE.CLIPBOARD_DATA_TXT:
					indata = cast(RDP_CLIPBOARD_DATA_TXT, indata)
					txtdata = indata.data.encode('ascii')
					msg = pack("!BxxxIs", 6, len(txtdata), txtdata)
					self.__writer.write(msg)

		except asyncio.CancelledError:
			return None, None

		except Exception as e:
			traceback.print_exc()
			return None, e

	async def testloop(self):
		ctr = 0
		while True:
			await self.__frame_update_req_evt.wait()
			if ctr == 100:
				ctr = 0
				await self.framebuffer_update_request(1)
			else:
				await self.framebuffer_update_request(incremental=1)
			#await self.framebuffer_update_request(incremental=1)
			#await self.framebuffer_update_request(incremental=1)
			self.__frame_update_req_evt.clear()
			ctr += 1
			#x = RDP_MOUSE()
			#x.yPos = 1
			#x.xPos = 1
			#x.pressed = False
			#await self.ext_in_queue.put(x)

	async def __send_rect(self, x, y, width, height, image:Image):
		try:
			#image.save('./test/test_%s.png' % os.urandom(4).hex(), 'PNG')
			#updating desktop buffer to have a way to copy rectangles later
			if self.width == width and self.height == height:
				self.__desktop_buffer = image
				self.__desktop_buffer.save('test.png', 'PNG')
			else:
				self.__desktop_buffer.paste(image, [x, y, x+width, y+height])
			
			#if self.iosettings.video_out_format == 'pil' or self.iosettings.video_out_format == 'pillow':
			#	return image
			
			if self.iosettings.video_out_format == 'raw':
				image = image.tobytes()

			elif self.iosettings.video_out_format == 'qt':
				image = ImageQt(image)
			
			elif self.iosettings.video_out_format == 'png':
				img_byte_arr = io.BytesIO()
				image.save(img_byte_arr, format=self.iosettings.video_out_format.upper())
				image = img_byte_arr.getvalue()
			else:
				raise ValueError('Output format of "%s" is not supported!' % self.iosettings.video_out_format)
									
			rect = RDP_VIDEO()
			rect.x = x
			rect.y = y
			rect.width = width
			rect.height = height
			rect.bitsPerPixel = self.bpp
			rect.is_compressed = False
			rect.data = image
			await self.ext_out_queue.put(rect)


		except Exception as e:
			traceback.print_exc()
			return None, e

		
	
	async def __reader_loop(self):
		try:
			while True:
				msgtype = await self.__reader.readexactly(1)
				msgtype = ord(msgtype)
				print(msgtype)
				if msgtype == 0:
					# framebufferupdate
					num_rect = await self.__reader.readexactly(3)
					num_rect = int.from_bytes(num_rect[1:], byteorder = 'big', signed = False)
					print(num_rect)
					for _ in range(num_rect):
						rect_hdr = await self.__reader.readexactly(12)
						(x, y, width, height, encoding) = unpack("!HHHHI", rect_hdr)
						

						if encoding == RAW_ENCODING:
							#print(width*height*self.bypp)
							try:
								#print(self.bypp)
								#print('x %s' % x)
								#print('y %s' % y)
								#print('width %s' % width)
								#print('height %s' % height)
								data = await self.__reader.readexactly(width*height*self.bypp)
								image = bytes(width * height * self.bypp)
								rle.mask_rgbx(image, data)
								#print(image[:4])
								#print(len(image))
								#print(width*height*self.bypp)
								image = Image.frombytes('RGBA', [width, height], image)
								await self.__send_rect(x,y,width, height, image)
							except Exception as e:
								traceback.print_exc()
								continue

						elif encoding == COPY_RECTANGLE_ENCODING:
							try:
								data = await self.__reader.readexactly(4)
								(srcx, srcy) = unpack("!HH", data)

								#print('copy')
								#print('width %s' % width)
								#print('height %s' % height)
								#print('x %s' % x)
								#print('y %s' % y)
								#print('srcx %s' % srcx)
								#print('srcy %s' % srcy)
								
								newrect = self.__desktop_buffer.crop([srcx, srcy, srcx+width, srcy+height])
								await self.__send_rect(x,y,width,height, newrect)
								continue
							except Exception as e:
								traceback.print_exc()
								return


						elif encoding == RRE_ENCODING:
							try:
								print('RRE!')
								sub_rect_num = await self.__reader.readexactly(4)
								sub_rect_num = int.from_bytes(sub_rect_num, byteorder = 'big', signed = False)
								#print(sub_rect_num)
								backgroud_pixel = await self.__reader.readexactly(self.bypp)
								r,g,b,a = unpack("BBBB", backgroud_pixel)
								a = 255
								rect = Image.new('RGBA', [width, height])
								rect.paste((r,g,b,a), [0,0, width, height])
								
								format = "!%dsHHHH" % self.bypp
								for _ in range(sub_rect_num):
									data = await self.__reader.readexactly(self.bypp + 8)
									(color, subx, suby, subwidth, subheight) = unpack(format, data)
									r,g,b,a = unpack("BBBB", color)
									a = 255
									#rect = Image.new('RGBA', subwidth, subheight)
									rect.paste((r,g,b,a), [subx,suby, subx+subwidth, suby+subheight])
									#await self.__send_rect(subx + x, suby + y, width, height)
								await self.__send_rect(x,y, width, height, rect)
							except Exception as e:
								traceback.print_exc()
								return
						
						
						elif encoding == TRLE_ENCODING:
							try:
								sub_enc = await self.__reader.readexactly(1)
								sub_enc = ord(sub_enc)
								run_length_encoded = bool(sub_enc >> 7)
								palette_size = sub_enc
								if run_length_encoded is True:
									palette_size -= 128
								if palette_size == 0:
									data = await self.__reader.readexactly(width*height*self.bypp)
								elif palette_size == 1:
									data = await self.__reader.readexactly(self.bypp)
								
								




							except Exception as e:
								traceback.print_exc()
								return

						else:
							print('Unknown encoding %s' % encoding)
				elif msgtype == 1:
					print('colormap')
					hdr = await self.__reader.readexactly(5)
					(_, firstcolor, numcolor) = unpack("!BHH", hdr)
					for _ in range(numcolor):
						color_raw = await self.__reader.readexactly(6)
						(red, green, blue) = unpack("!HHH", color_raw)
				
				elif msgtype == 2:
					print('bell')
				
				elif msgtype == 3:
					hdr = await self.__reader.readexactly(7)
					(_,_,_, cliplen ) = unpack("!BBBI", hdr)
					cliptext = await self.__reader.readexactly(cliplen)
					cliptext = cliptext.decode()
					print(cliptext)
				else:
					print('Unexpected message tpye %s' % msgtype)

				if msgtype == 0:
					self.__frame_update_req_evt.set()

					
			return True, None
		except Exception as e:
			return None, e

	async def set_encodings(self, list_of_encodings = [2, 1, 0]):
		try:
			enc_encodings = b''
			for encoding in list_of_encodings:
				enc_encodings += encoding.to_bytes(4, byteorder = 'big', signed = True)
			sendbuff = pack("!BxH", 2, len(list_of_encodings)) + enc_encodings
			print(sendbuff)
			self.__writer.write(sendbuff)
			return True, None
		except Exception as e:
			return None, e
		

	async def set_pixel_format(self, bpp=32, depth=24, bigendian=0, truecolor=1, redmax=255, greenmax=255, bluemax=255,
						 redshift=0, greenshift=8, blueshift=16):
		pixformat = pack("!BBBBHHHBBBxxx", bpp, depth, bigendian, truecolor, redmax, greenmax, bluemax, redshift,
						 greenshift, blueshift)
		print(pixformat)
		self.__writer.write(b'\x00\x00\x00\x00' + pixformat)
		# rember these settings
		self.bpp, self.depth, self.bigendian, self.truecolor = bpp, depth, bigendian, truecolor
		self.redmax, self.greenmax, self.bluemax = redmax, greenmax, bluemax
		self.redshift, self.greenshift, self.blueshift = redshift, greenshift, blueshift
		self.bypp = self.bpp // 8  # calc bytes per pixel
		# ~ print self.bypp

	async def framebuffer_update_request(self, x=0, y=0, width=None, height=None, incremental=0):
		if width is None:
			width = self.width - x

		if height is None:
			height = self.height - y

		self.__writer.write(pack("!BBHHHH", 3, incremental, x, y, width, height))
	
	def _handle_rectangle(self, block):
		(x, y, width, height, encoding) = unpack("!HHHHI", block)
		if self.rectangles:
			self.rectangles -= 1
			self.rectanglePos.append((x, y, width, height))
			if encoding == COPY_RECTANGLE_ENCODING:
				self._handleDecodeCopyrect( 4, x, y, width, height)
			elif encoding == RAW_ENCODING:
				self._handle_decode_raw( width * height * self.bypp, x, y, width, height)
			elif encoding == HEXTILE_ENCODING:
				self._do_next_hextile_subrect(None, None, x, y, width, height, None, None)
			elif encoding == CORRE_ENCODING:
				self._handle_decode_corre( 4 + self.bypp, x, y, width, height)
			elif encoding == RRE_ENCODING:
				self._handleDecodeRRE(4 + self.bypp, x, y, width, height)
			else:
				logger.msg("unknown encoding received (encoding %d)\n" % encoding)
				self._do_connection()
		else:
			self._do_connection()
	
	def _handle_decode_raw(self, block, x, y, width, height):
		# TODO convert pixel format?
		self.update_rectangle(x, y, width, height, block)

	def _handleDecodeCopyrect(self, block, x, y, width, height):
		(srcx, srcy) = unpack("!HH", block)
		self.copy_rectangle(srcx, srcy, x, y, width, height)
	
	def _handle_decode_corre_rectangles(self, block, topx, topy):
		# ~ print "_handleDecodeCORRERectangle"
		pos = 0
		end = len(block)
		sz = self.bypp + 4
		format = "!%dsBBBB" % self.bypp
		while pos < sz:
			(color, x, y, width, height) = unpack(format, block[pos:pos + sz])
			self.fill_rectangle(topx + x, topy + y, width, height, color)
			pos += sz

	def _do_next_hextile_subrect(self, bg, color, x, y, width, height, tx, ty):
		"""
		# Hextile Encoding
		:param bg:
		:param color:
		:param x:
		:param y:
		:param width:
		:param height:
		:param tx:
		:param ty:
		:return:
		"""
		# ~ print "_doNextHextileSubrect %r" % ((color, x, y, width, height, tx, ty), )
		# coords of next tile
		# its line after line of tiles
		# finished when the last line is completly received

		# dont inc the first time
		if tx is not None:
			# calc next subrect pos
			tx += 16
			if tx >= x + width:
				tx = x
				ty += 16
		else:
			tx = x
			ty = y
		# more tiles?
		if ty >= y + height:
			self._do_connection() # read more!
		else:
			self._handle_decode_hextile(1, bg, color, x, y, width, height, tx, ty)
	
	def _handle_decode_hextile(self, block, bg, color, x, y, width, height, tx, ty):
		"""
		# Hextile Decoding
		:param block:
		:param bg:
		:param color:
		:param x:
		:param y:
		:param width:
		:param height:
		:param tx:
		:param ty:
		:return:
		"""
		(sub_encoding,) = unpack("!B", block)
		# calc tile size
		tw = th = 16
		if x + width - tx < 16:
			tw = x + width - tx

		if y + height - ty < 16:
			th = y + height - ty

		# decode tile
		if sub_encoding & 1:  # RAW
			self._handle_decode_hextile_raw( tw * th * self.bypp, bg, color, x, y, width, height, tx, ty, tw, th)
		else:
			num_bytes = 0
			if sub_encoding & 2:  # BackgroundSpecified
				num_bytes += self.bypp
			if sub_encoding & 4:  # ForegroundSpecified
				num_bytes += self.bypp
			if sub_encoding & 8:  # AnySubrects
				num_bytes += 1
			if num_bytes:
				self._handle_decode_hextile_subrect(num_bytes, sub_encoding, bg, color, x, y, width, height, tx, ty, tw, th)
			else:
				self.fill_rectangle(tx, ty, tw, th, bg)
				self._do_next_hextile_subrect(bg, color, x, y, width, height, tx, ty)
	
	def _handle_decode_hextile_raw(self, block, bg, color, x, y, width, height, tx, ty, tw, th):
		"""the tile is in raw encoding"""
		self.update_rectangle(tx, ty, tw, th, block)
		self._do_next_hextile_subrect(bg, color, x, y, width, height, tx, ty)
	
	def _handle_decode_corre_rectangles(self, block, topx, topy):
		# ~ print "_handleDecodeCORRERectangle"
		pos = 0
		end = len(block)
		sz = self.bypp + 4
		format = "!%dsBBBB" % self.bypp
		while pos < sz:
			(color, x, y, width, height) = unpack(format, block[pos:pos + sz])
			self.fill_rectangle(topx + x, topy + y, width, height, color)
			pos += sz
	
	def _handleDecodeRRE(self, block, x, y, width, height):
		(subrects,) = unpack("!I", block[:4])
		color = block[4:]
		self.fill_rectangle(x, y, width, height, color)
		self._handle_rre_sub_rectangles((8 + self.bypp) * subrects, x, y)
	
	def _handle_rre_sub_rectangles(self, block, topx, topy):
		"""
		# RRE Sub Rectangles
		:param block:
		:param topx:
		:param topy:
		:return:
		"""

		pos = 0
		end = len(block)
		sz = self.bypp + 8
		format = "!%dsHHHH" % self.bypp
		while pos < end:
			(color, x, y, width, height) = unpack(format, block[pos:pos + sz])
			self.fill_rectangle(topx + x, topy + y, width, height, color)
			pos += sz

	def fill_rectangle(self, x, y, width, height, color):
		"""fill the area with the color. the color is a string in
		   the pixel format set up earlier"""
		# fallback variant, use update recatngle
		# override with specialized function for better performance
		self.update_rectangle(x, y, width, height, color * width * height)

	def update_rectangle(self, x, y, width, height, size):
		print(x, y, width, height, size)

	def copy_rectangle(self, srcx, srcy, x, y, width, height):
		print(srcx, srcy, x, y, width, height)

async def amain():
	try:
		logger.setLevel(1)
		from aardwolf.commons.url import RDPConnectionURL
		from aardwolf.commons.iosettings import RDPIOSettings

		iosettings = RDPIOSettings()
		iosettings.video_out_format = 'raw'
		
		url = 'vnc+plain://alma:alma@10.10.10.102:5900'
		url = RDPConnectionURL(url)
		connection = url.get_connection(iosettings)
		print(connection)
		print(connection.target.port)

		_, err = await connection.connect()
		if err is not None:
			raise err

		while True:
			await asyncio.sleep(10)

		return True, None
	except Exception as e:
		traceback.print_exc()
		return None, e

def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()