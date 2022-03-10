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
	ASYSOCKS = 'ASYSOCKS'

class RDPProxy:
	def __init__(self):
		self.type:RDPProxyType = None
		self.target = None

	@staticmethod
	def from_params(url_str):
		proxy = RDPProxy()
		url = urlparse(url_str)
		if url.query is None:
			return None

		query = parse_qs(url.query)
		if 'proxytype' not in query and 'sametype' not in query:
			return None

		if query['proxytype'][0].upper() in ['SOCKS5', 'SOCKS4', 'SOCKS4A', 'SOCKS5-SSL', 'SOCKS4-SSL', 'SOCKS4A-SSL', 'WSNET', 'WSNETWS', 'WSNETWSS']:
			proxy.type = RDPProxyType.ASYSOCKS
		else:
			raise NotImplementedError(query['proxytype'][0].upper())
		
		if proxy.type == RDPProxyType.ASYSOCKS:
			cu = SocksClientURL.from_params(url_str)
			cu[-1].endpoint_port = 3389
			proxy.target = cu
		else:
			raise NotImplementedError('Unknown proxy type "%s"' % proxy.type)
		
		return proxy

	def __str__(self):
		t = '==== RDPProxy ====\r\n'
		for k in self.__dict__:
			t += '%s: %s\r\n' % (k, self.__dict__[k])
			
		return t

def test():
	t = ['socks5://10.10.10.1',
			'socks5+ssl://10.10.10.1',
			'socks5+ssl://admin:password@10.10.10.1',
	]
	for x in t:
		s = RDPProxy.from_connection_string(x)
		print(str(s))

	
if __name__ == '__main__':
	test()