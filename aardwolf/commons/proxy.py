import ipaddress
import enum
from urllib.parse import urlparse, parse_qs

from asysocks.common.clienturl import SocksClientURL 


def stru(x):
	return str(x).upper()

class RDPProxySecretType(enum.Enum):
	NONE = 'NONE'
	PLAIN = 'PLAIN'

class RDPProxyType(enum.Enum):
	SOCKS4 = 'SOCKS4'
	SOCKS4_SSL = 'SOCKS4_SSL'
	SOCKS5 = 'SOCKS5'
	SOCKS5_SSL = 'SOCKS5_SSL'
	MULTIPLEXOR = 'MULTIPLEXOR'
	MULTIPLEXOR_SSL = 'MULTIPLEXOR_SSL'
	WSNET = 'WSNET'
	WSNETWS = 'WSNETWS'
	WSNETWSS = 'WSNETWSS'

multiplexorproxyurl_param2var = {
	'type' : ('version', [stru, RDPProxyType]),
	'host' : ('ip', [str]),
	'port' : ('port', [int]),
	'timeout': ('timeout', [int]),
	'user' : ('username', [str]),
	'pass' : ('password', [str]),
	#'authtype' : ('authtype', [SOCKS5Method]),
	'agentid' : ('agent_id', [str]),
	'domain' : ('domain', [str])

}


class RDPProxy:
	def __init__(self):
		self.type = None
		self.target = None
		self.auth   = None

	@staticmethod
	def from_params(url_str):
		proxy = RDPProxy()
		url = urlparse(url_str)
		if url.query is None:
			return None

		query = parse_qs(url.query)
		if 'proxytype' not in query and 'sametype' not in query:
			return None

		proxy.type = RDPProxyType(query['proxytype'][0].upper())
		
		if proxy.type in [RDPProxyType.WSNET, RDPProxyType.WSNETWS, RDPProxyType.WSNETWSS, RDPProxyType.SOCKS4, RDPProxyType.SOCKS4_SSL, RDPProxyType.SOCKS5, RDPProxyType.SOCKS5_SSL]:
			cu = SocksClientURL.from_params(url_str)
			cu[-1].endpoint_port = 3389
			proxy.target = cu
		else:
			proxy.target = RDPMultiplexorProxy.from_params(url_str)
		
		return proxy

	def __str__(self):
		t = '==== RDPProxy ====\r\n'
		for k in self.__dict__:
			t += '%s: %s\r\n' % (k, self.__dict__[k])
			
		return t

class RDPMultiplexorProxy:
	def __init__(self):
		self.ip = None
		self.port = None
		self.timeout = 10
		self.type = RDPProxyType.MULTIPLEXOR
		self.username = None
		self.password = None
		self.domain = None
		self.agent_id = None
		self.virtual_socks_port = None
		self.virtual_socks_ip = None
	
	def sanity_check(self):
		if self.ip is None:
			raise Exception('MULTIPLEXOR server IP is missing!')
		if self.port is None:
			raise Exception('MULTIPLEXOR server port is missing!')
		if self.agent_id is None:
				raise Exception('MULTIPLEXOR proxy requires agentid to be set!')

	def get_server_url(self):
		con_str = 'ws://%s:%s' % (self.ip, self.port)
		if self.type == RDPProxyType.MULTIPLEXOR_SSL:
			con_str = 'wss://%s:%s' % (self.ip, self.port)
		return con_str

	@staticmethod
	def from_params(url_str):
		res = RDPMultiplexorProxy()
		url = urlparse(url_str)
		res.endpoint_ip = url.hostname
		if url.port:
			res.endpoint_port = int(url.port)
		if url.query is not None:
			query = parse_qs(url.query)

			for k in query:
				if k.startswith('proxy'):
					if k[5:] in multiplexorproxyurl_param2var:

						data = query[k][0]
						for c in multiplexorproxyurl_param2var[k[5:]][1]:
							data = c(data)

						setattr(
							res, 
							multiplexorproxyurl_param2var[k[5:]][0], 
							data
						)
		res.sanity_check()

		return res

def test():
	t = ['socks5://10.10.10.1',
			'socks5+ssl://10.10.10.1',
			'socks5+ssl://admin:password@10.10.10.1',
			'multiplexor+ssl://admin:password@10.10.10.1/alma',
	]
	for x in t:
		s = RDPProxy.from_connection_string(x)
		print(str(s))

	
if __name__ == '__main__':
	test()