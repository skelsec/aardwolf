from aardwolf.commons.proxy import RDPProxy, RDPProxyType
from aardwolf.commons.target import RDPConnectionProtocol
from aardwolf.transport.tcp import TCPSocket
from aardwolf.network.socks import SocksProxyConnection
#from aardwolf.network.multiplexornetwork import MultiplexorProxyConnection


class NetworkSelector:
	def __init__(self):
		pass

	@staticmethod
	async def select(target):
		try:
			if target.proxy is None:
				if target.protocol == RDPConnectionProtocol.TCP:
					return TCPSocket(target = target), None
				else:
					raise NotImplementedError()
			elif target.proxy.type in [RDPProxyType.WSNET,RDPProxyType.WSNETWS, RDPProxyType.WSNETWSS, RDPProxyType.SOCKS5, RDPProxyType.SOCKS5_SSL, RDPProxyType.SOCKS4, RDPProxyType.SOCKS4_SSL]:
				return SocksProxyConnection(target = target), None

			else:
				return None, Exception('Cant select correct connection type!')
		except Exception as e:
			return None, e