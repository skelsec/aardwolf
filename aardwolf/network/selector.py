from aardwolf.commons.proxy import RDPProxyType
from aardwolf.commons.target import RDPConnectionProtocol, RDPTarget
from aardwolf.transport.tcp import TCPSocket
from aardwolf.network.socks import SocksProxyConnection


class NetworkSelector:
	def __init__(self):
		pass

	@staticmethod
	async def select(target: RDPTarget):
		"""Selects the appropriate network connection library based on the target"""
		try:
			if target.proxy is None:
				if target.protocol == RDPConnectionProtocol.TCP:
					return TCPSocket(target = target), None
				else:
					raise NotImplementedError()
			elif target.proxy.type == RDPProxyType.ASYSOCKS:
				return SocksProxyConnection(target = target), None

			else:
				raise Exception('Cant select correct connection type!')
		except Exception as e:
			return None, e