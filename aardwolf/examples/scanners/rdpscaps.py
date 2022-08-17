import copy
from asysocks.unicomm.common.scanner.common import *
from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS
from aardwolf.network.tpkt import TPKTPacketizer
from aardwolf.network.x224 import X224Network
from asysocks.unicomm.client import UniClient
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS, NEG_FLAGS


class RDPCapabilitiesRes:
	def __init__(self, restrictedadmin,restrictedauth,rdp,ssl,hybrid,hybridex):
		self.restrictedadmin = restrictedadmin
		self.restrictedauth = restrictedauth
		self.rdp = rdp
		self.ssl = ssl
		self.hybrid = hybrid
		self.hybridex = hybridex

	def get_header(self):
		return ['restrictedadmin', 'restrictedauth', 'rdp', 'ssl', 'hybrid', 'hybridex']

	def to_line(self, separator = '\t'):
		return separator.join([
			str(self.restrictedadmin),
			str(self.restrictedauth),
			str(self.rdp),
			str(self.ssl),
			str(self.hybrid),
			str(self.hybridex),
		])

class RDPCapabilitiesScanner:
	def __init__(self, factory:RDPConnectionFactory):
		self.factory:RDPConnectionFactory = factory
		self.protoflags = [SUPP_PROTOCOLS.RDP, SUPP_PROTOCOLS.SSL, SUPP_PROTOCOLS.SSL|SUPP_PROTOCOLS.RDP, SUPP_PROTOCOLS.SSL|SUPP_PROTOCOLS.HYBRID, SUPP_PROTOCOLS.SSL|SUPP_PROTOCOLS.HYBRID_EX]


	
	async def scan_flags(self, target, negflag, protoflag):
		try:
			packetizer = TPKTPacketizer()
			client = UniClient(target, packetizer)
			connection = await client.connect()

			# X224 channel is on top of TPKT, performs the initial negotiation
			# between the server and our client (restricted admin mode, authentication methods etc)
			# are set here
			x224net = X224Network(connection)

			reply, err = await x224net.client_negotiate(negflag, protoflag, to_raise=False)
			if err is not None:
				raise err

			if reply.rdpNegData.type == 3:
				#server refused our flags
				return False, reply, None

			return True, reply, None
		except Exception as e:
			return False, None, e

	async def run(self, targetid, target, out_queue):
		try:
			rdp = None
			ssl = None
			hybrid = None
			hybridex = None
			restrictedadmin = None
			restrictedauth = None

			rdptarget = self.factory.create_connection_newtarget(target, self.factory.get_settings()).target

			for protoflag in self.protoflags:
				negflag = 0
				ok, reply, err = await self.scan_flags(rdptarget, negflag, protoflag)
				if err is not None:
					raise err
				if ok is True:
					if SUPP_PROTOCOLS.SSL == reply.rdpNegData.selectedProtocol:
						ssl = True
					if SUPP_PROTOCOLS.HYBRID in reply.rdpNegData.selectedProtocol:
						hybrid = True
					if SUPP_PROTOCOLS.HYBRID_EX in reply.rdpNegData.selectedProtocol:
						hybridex = True
					if SUPP_PROTOCOLS.RDP == reply.rdpNegData.selectedProtocol:
						rdp = True

			ok, reply, err = await self.scan_flags(rdptarget, NEG_FLAGS.RESTRICTED_ADMIN_MODE_REQUIRED, SUPP_PROTOCOLS.SSL|SUPP_PROTOCOLS.HYBRID)
			if err is not None:
				raise err
			restrictedadmin = ok
			ok, reply, err = await self.scan_flags(rdptarget, NEG_FLAGS.REDIRECTED_AUTHENTICATION_MODE_REQUIRED, SUPP_PROTOCOLS.SSL|SUPP_PROTOCOLS.HYBRID)
			if err is not None:
				raise err
			restrictedauth = ok

			await out_queue.put(ScannerData(target, RDPCapabilitiesRes(rdp, ssl, hybrid, hybridex, restrictedadmin, restrictedauth)))

		except Exception as e:
			await out_queue.put(ScannerError(target, e))
