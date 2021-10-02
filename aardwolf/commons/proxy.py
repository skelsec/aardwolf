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

#class RDPProxy:
#	def __init__(self, 
#				ip = None,
#				port = None,
#				timeout = 5,
#				proxy_type = None,
#				username = None,
#				domain = None,
#				secret = None,
#				secret_type = RDPProxySecretType.NONE,
#				agent_id = None):
#		self.ip = ip
#		self.port = port
#		self.timeout = timeout
#		self.type = proxy_type
#		self.username = username
#		self.domain = domain
#		self.secret = secret
#		self.secret_type = secret_type
#		self.agent_id = agent_id #used by multiplexor only
#		self.settings = {}
#	
#	@staticmethod
#	def from_url(url_str):
#		proxy = RDPProxy()
#		url_e = urlparse(url_str)
#		if url_e.query is None:
#			return None
#		
#		query = parse_qs(url_e.query)
#		if 'proxytype' not in query and 'sametype' not in query:
#			return None
#
#		for k in query:
#			if k.startswith('proxy') or k.startswith('same'):
#				key = 'same'
#				if k.startswith('proxy'):
#					key = 'proxy'
#				
#				if k == key+'type':
#					proxy.type = RDPProxyType(query[k][0].replace('-','_').upper())
#				elif k == key+'user':
#					proxy.username = query[k][0]
#				elif k == key+'domain':
#					proxy.domain = query[k][0]
#				elif k == key+'pass':
#					proxy.secret = query[k][0]
#				elif k == key+'host':
#					proxy.ip = query[k][0]
#				elif k == key+'port':
#					proxy.port = int(query[k][0])
#				elif k == key+'timeout':
#					proxy.timeout = int(query[k][0])
#				elif k == key+'agentid':
#					proxy.agent_id = query[k][0]
#				else:
#					proxy.settings[k[len(key):]] = query[k] #the result is a list for each entry because this preprocessor is not aware which elements should be lists!
#		
#		if proxy.secret is not None:
#			proxy.secret_type = RDPProxySecretType.PLAIN
#		else:
#			proxy.secret_type = RDPProxySecretType.NONE
#
#		if proxy.ip is None:
#			raise Exception('Proxy server specified with missing servber address! (add proxyhost to params)')
#		
#		if proxy.type in [RDPProxyType.MULTIPLEXOR_SSL, RDPProxyType.MULTIPLEXOR]:
#			if proxy.agent_id is None:
#				raise Exception('MULTIPLEXOR proxy requires agentid to be set!')
#
#		return proxy
#
#	
#	@staticmethod
#	def from_connection_string(s):
#		"""
#		URL format required
#		socks5://user:password@ipaddress:port
#		socks5+ssl://user:password@ipaddress:port
#		multiplexor://user:password@ipaddress:port/agentid
#		"""
#		st = RDPProxy()
#		o = urlparse(s)
#
#		st.type = RDPProxyType(o.scheme.upper().replace('+','_'))
#		st.ip = o.hostname
#		st.username = o.username
#		st.secret = o.password
#		st.port = int(o.port)
#		if st.secret is not None:
#			st.secret_type = RDPProxySecretType.PLAIN
#		
#		if st.type in [RDPProxyType.MULTIPLEXOR, RDPProxyType.MULTIPLEXOR_SSL]:
#			st.agent_id = o.path.replace('/','')
#		
#		return st
#		
#	def __str__(self):
#		t = '==== RDPProxy ====\r\n'
#		for k in self.__dict__:
#			t += '%s: %s\r\n' % (k, self.__dict__[k])
#			
#		return t
#		
		
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