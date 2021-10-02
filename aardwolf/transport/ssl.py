import asyncio

import platform
import traceback
try:
	import ssl
except:
	if platform.system() == 'Emscripten':
		#pyodide doesnt support SSL for now.
		pass


import logging
from asn1crypto.x509 import Certificate, PublicKeyInfo

class SSLClientTunnel:
	def __init__(self):
		self.in_queue = None
		self.out_queue = None
		self.ssl_ctx = None
		self.transport = None
		self.ssl_in_buff = None
		self.ssl_out_buff = None
		self.ssl_obj = None
		self.__ssl_in_q = None
		self.stop_evt = None
		self.server_certificate = None

		self.__enc_task = None
		self.__dec_task = None
		self.__process_task = None
	
	async def disconnect(self):
		try:
			if self.__enc_task is not None:
				self.__enc_task.cancel()
			if self.__dec_task is not None:
				self.__dec_task.cancel()
			if self.__process_task is not None:
				self.__process_task.cancel()

			if self.transport is not None:
				self.transport.out_queue.put_nowait(b'')
				await self.transport.disconnect()
		except Exception as e:
			pass
	
	async def get_server_pubkey(self):
		try:
			if self.server_certificate is None:
				return None
			cert = Certificate.load(self.server_certificate)
			return cert['tbs_certificate']['subject_public_key_info']['public_key'].dump()[5:] #why?
		except Exception as e:
			return e
	
	async def setup(self):
		try:
			self.in_queue = asyncio.Queue()
			self.out_queue = asyncio.Queue()
			self.stop_evt = asyncio.Event()
			self.__ssl_in_q = asyncio.Queue()
			self.ssl_in_buff = ssl.MemoryBIO()
			self.ssl_out_buff = ssl.MemoryBIO()
			self.ssl_obj = self.ssl_ctx.wrap_bio(self.ssl_in_buff, self.ssl_out_buff, server_side=False, server_hostname = None)
			_, err = await self.__do_handshake()
			if err is not None:
				raise err
			#print('Handshake ok!')
			self.server_certificate = self.ssl_obj.getpeercert(binary_form=True)
			self.__enc_task = asyncio.create_task(self.__encrypt_ssl_rec())
			self.__dec_task = asyncio.create_task(self.__decrypt_ssl_rec())
			self.__process_task = asyncio.create_task(self.__read_ssl_record())
			return True, None

		except Exception as e:
			return None, e
	
	async def __encrypt_ssl_rec(self):
		try:
			while True:
				try:
					raw_data = await self.out_queue.get()
					if raw_data == b'':
						await self.in_queue.put(None)
						#print('Connection terminated')
						return
					
					self.ssl_obj.write(raw_data)
					while True:
						try:
							enc_data = self.ssl_out_buff.read()
							if enc_data == b'':
								break
							await self.transport.out_queue.put(enc_data)
						except Exception as e:
							raise e
				except Exception as e:
							raise e

		except asyncio.CancelledError:
			return
		except Exception as e:
			logging.debug('__encrypt_ssl_rec %s' % e)
	
	async def __decrypt_ssl_rec(self):
		"""
		Decrypting the encrypted SSL records from the internal queue and putting them in the queue for the uppr layers to use
		"""
		try:
			while not self.stop_evt.is_set():
				ssl_data = await self.__ssl_in_q.get()
				if ssl_data == b'':
					await self.in_queue.put((ssl_data, None))
					#print('Connection terminated')
					return
				self.ssl_in_buff.write(ssl_data)

				data_buff = b''
				while not self.stop_evt.is_set():
					try:
						data_buff += self.ssl_obj.read()
					except ssl.SSLWantReadError:
						break
					except Exception as e:
						raise e
				#print('data_buff %s' % data_buff)
				if data_buff != b'':
					await self.in_queue.put((data_buff, None))

		except asyncio.CancelledError:
			return
		except Exception as e:
			logging.debug('__decrypt_ssl_rec %s' % e)

	async def __read_ssl_record(self):
		try:
			"""
			buffering the incoming SSL (encrypted) recodrs and putting them in an internal queue one record at a time
			"""
			buffer = b''
			length = None
			while not self.stop_evt.is_set():
				if length is None and len(buffer) >= 6:
					length = int.from_bytes(buffer[3:5], byteorder = 'big', signed = False)
				
				if length is not None and len(buffer) >= length + 5:
					#print('LB raw %s' % len(buffer[:length+5]))
					await self.__ssl_in_q.put(buffer[:length+5])
					buffer = buffer[length+5:]
					length = None
					continue
				
				data, err = await self.transport.in_queue.get()
				if err is not None:
					raise err
				if data == b'':
					await self.__ssl_in_q.put(b'')
					return
				buffer+= data
				

		except asyncio.CancelledError:
			return

		except Exception as e:
			logging.debug('__read_ssl_record %s' % e)
			await self.__ssl_in_q.put(b'')

		#finally:
		#	self.stop_evt.set()
	
	async def __do_handshake(self):
		try:
			ctr = 0
			while not self.stop_evt.is_set():
				ctr += 1
				#print('DST Performing handshake!')
				try:
					self.ssl_obj.do_handshake()
				except ssl.SSLWantReadError:
					#print('DST want %s' % ctr)
					while True:
						client_hello = self.ssl_out_buff.read()
						if client_hello != b'':
							#print('DST client_hello %s' % len(client_hello))
							await self.transport.out_queue.put(client_hello)
						else:
							break
					
					#print('DST wating server hello %s' % ctr)
					server_hello, err = await self.transport.in_queue.get()
					if err is not None:
						raise err
					if server_hello == b'':
						raise Exception('Server closed the connection!')
					#print('DST server_hello %s' % len(server_hello))
					self.ssl_in_buff.write(server_hello)

					continue
				except:
					raise
				else:
					#print('DST handshake ok %s' % ctr)
					#server_fin = tls_out_buff.read()
					#print('DST server_fin %s ' %  server_fin)
					#await out_q.put(server_fin)
					break			

			return True, None

		except Exception as e:
			logging.debug('__do_handshake %s' % e)
			return None, e

	@staticmethod
	async def from_transport(transport, ssl_ctx = None, ssl_cert = None, ssl_key = None):
		try:
			tunnel = SSLClientTunnel()
			tunnel.transport = transport
			if ssl_ctx is not None:
				tunnel.ssl_ctx = ssl_ctx
			elif ssl_key is not None:
				raise NotImplementedError()
			else:
				tunnel.ssl_ctx = ssl.create_default_context()
				tunnel.ssl_ctx.check_hostname = False
				tunnel.ssl_ctx.verify_mode = ssl.CERT_NONE
			_, err = await tunnel.setup()
			if err is not None:
				raise err

			return tunnel, None
		except Exception as e:
			return None, e