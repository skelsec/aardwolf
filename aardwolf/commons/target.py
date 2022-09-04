#!/usr/bin/env python3
#
# Author:
#  Tamas Jos (@skelsec)
#
# Comments:
#


import ipaddress
import enum
import copy
from typing import List
from urllib.parse import urlparse, parse_qs

from asysocks.unicomm.common.target import UniTarget, UniProto
from asysocks.unicomm.common.proxy import UniProxyProto, UniProxyTarget

class RDPConnectionDialect(enum.Enum):
	RDP = 'RDP'
	VNC = 'VNC'

rdpurlconnection_param2var = {
	'RDP' : UniProto.CLIENT_TCP,
	'VNC' : UniProto.CLIENT_TCP,
}

class RDPTarget(UniTarget):
	"""
	"""
	def __init__(
			self, 
			ip:str = None, 
			port:int = 3389, 
			hostname:str = None, 
			timeout:int = 1, 
			dc_ip:int=None, 
			domain:str = None, 
			proxies:List[UniProxyTarget] = None, 
			protocol:UniProto = UniProto.CLIENT_TCP, 
			dialect:RDPConnectionDialect = RDPConnectionDialect.RDP,
			dns:str = None):
		UniTarget.__init__(self, ip, port, protocol, timeout, hostname = hostname, proxies = proxies, domain = domain, dc_ip = dc_ip, dns=dns)
		self.dialect = dialect
		if self.dialect == RDPConnectionDialect.VNC:
			self.port = 5900

	def to_target_string(self):
		return 'termsrv/%s@%s' % (self.hostname, self.domain)

	def get_copy(self, ip, port, hostname = None):
		t = RDPTarget(
			ip = ip, 
			port = port, 
			hostname = hostname, 
			timeout = self.timeout, 
			dc_ip= self.dc_ip, 
			domain = self.domain, 
			proxy = copy.deepcopy(self.proxy),
			protocol = self.protocol,
			dialect = self.dialect,
			dns=self.dns
		)
		return t

	@staticmethod
	def from_url(connection_url):
		url_e = urlparse(connection_url)
		schemes = url_e.scheme.upper().split('+')
		connection_tags = schemes[0].split('-')
		if len(connection_tags) > 1:
			dialect = RDPConnectionDialect(connection_tags[0])
			protocol = rdpurlconnection_param2var[connection_tags[1]]
		else:
			dialect = RDPConnectionDialect(connection_tags[0])
			protocol = UniProto.CLIENT_TCP
		
		if url_e.port:
			port = url_e.port
		elif dialect == RDPConnectionDialect.RDP:
			port = 3389
		elif dialect == RDPConnectionDialect.VNC:
			port = 5800
		else:
			raise Exception('Port must be provided!')
		
		unitarget, extraparams = UniTarget.from_url(connection_url, protocol, port)

		target = RDPTarget(
			ip = unitarget.ip,
			port = unitarget.port,
			hostname = unitarget.hostname,
			timeout = unitarget.timeout,
			dc_ip = unitarget.dc_ip,
			domain = unitarget.domain,
			proxies = unitarget.proxies,
			protocol = unitarget.protocol,
			dns = unitarget.dns,
			dialect = dialect,
		)
		
		return target
		
	def get_ip(self):
		if not self.ip and not self.hostname:
			raise Exception('RDPTarget must have ip or hostname defined!')
		return self.ip if self.ip is not None else self.hostname
		
	def get_hostname(self):
		return self.hostname
	
	def get_hostname_or_ip(self):
		if self.hostname:
			return self.hostname
		return self.ip
	
	def get_port(self):
		return self.port
		
	def __str__(self):
		t = '==== RDPTarget ====\r\n'
		for k in self.__dict__:
			t += '%s: %s\r\n' % (k, self.__dict__[k])
			
		return t
		
		
def test():
	s = 'TEST/victim/ntlm/nt:AAAAAAAA@10.10.10.2:3389'
	creds = RDPTarget.from_connection_string(s)
	print(str(creds))
	
	s = 'TEST/victim/sspi@10.10.10.2:3389/aaaa'
	creds = RDPTarget.from_connection_string(s)
	
	print(str(creds))
	
if __name__ == '__main__':
	test()