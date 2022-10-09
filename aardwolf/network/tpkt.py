import asyncio

import logging
import traceback
from aardwolf.protocol.tpkt import TPKT
from aardwolf.protocol.x224 import X224Packet
from aardwolf.protocol.x224.data import Data
from asysocks.unicomm.common.packetizers import Packetizer

class CredSSPPacketizer(Packetizer):
	def __init__(self):
		Packetizer.__init__(self, 65535)
		self.in_buffer = b''
	
	def flush_buffer(self):
		data = self.in_buffer
		self.in_buffer = b''
		return data

	@staticmethod
	def calcualte_length(data):
		if data[1] <= 127:
			return data[1] + 2
		else:
			bcount = data[1] - 128
			return int.from_bytes(data[2:2+bcount], byteorder = 'big', signed = False) + bcount + 2
	
	def process_buffer(self):
		preread = 6
		remaining_length = -1
		while True:
			if len(self.in_buffer) < preread:
				break
			lb = self.in_buffer[:preread]
			remaining_length = CredSSPPacketizer.calcualte_length(lb) - preread
			if len(self.in_buffer) >= remaining_length+preread:
				data = self.in_buffer[:remaining_length+preread]
				self.in_buffer = self.in_buffer[remaining_length+preread:]
				yield data
				continue
			break
		

	async def data_out(self, data):
		yield data

	async def data_in(self, data):
		if data is None:
			yield data
		self.in_buffer += data
		for packet in self.process_buffer():
			yield packet

class TPKTPacketizer(Packetizer):
	def __init__(self):
		Packetizer.__init__(self)
		self.wrap_x224 = False
		self.in_buffer = b''
	
	def flush_buffer(self):
		data = self.in_buffer
		self.in_buffer = b''
		return data

	def packetizer_control(self, cmd):
		if cmd == 'X224':
			self.wrap_x224 = True
	
	def process_buffer(self):
		msgsize = None
		is_fastpath = False
		while True:
			if len(self.in_buffer) < 4:
				break
			if self.in_buffer[0] == 3:
				msgsize = int.from_bytes(self.in_buffer[2:4], byteorder='big', signed=False)
			else:
				is_fastpath = True
				msgsize = self.in_buffer[1]
				if msgsize >> 7 == 1:
					msgsize = int.from_bytes(self.in_buffer[1:3], byteorder='big', signed=False)
					msgsize = msgsize & 0x7fff
			
			if len(self.in_buffer)>=msgsize:
				if is_fastpath is False:
					msg = TPKT.from_bytes(self.in_buffer[:msgsize])
					self.in_buffer = self.in_buffer[msgsize:]
					msgsize = None
					if self.wrap_x224 is True:
						yield (False, X224Packet.from_bytes(msg.tpdu))
					else:
						yield (False, msg.tpdu)
					
				else:
					res = self.in_buffer[:msgsize]
					self.in_buffer = self.in_buffer[msgsize:]
					msgsize = None
					is_fastpath = False
					yield (True, res)

				if len(self.in_buffer) > 0:
					continue
			break

	async def data_out(self, data):
		tpkt = TPKT()
		tpkt.tpdu = data
		#print('TPKT -> %s' % tpkt.to_bytes())
		yield tpkt.to_bytes()

	async def data_in(self, data):
		if data is None:
			yield data
		self.in_buffer += data
		for packet in self.process_buffer():
			yield packet
