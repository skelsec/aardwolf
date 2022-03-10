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
from aardwolf.commons.proxy import RDPProxy

class RDPConnectionDialect(enum.Enum):
	RDP = 'RDP'
	VNC = 'VNC'

class RDPConnectionProtocol(enum.Enum):
	TCP = 'TCP'

class RDPTarget:
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
			proxy:RDPProxy = None, 
			protocol:RDPConnectionProtocol = RDPConnectionProtocol.TCP, 
			serverip = None, 
			dialect:RDPConnectionDialect = RDPConnectionDialect.RDP):
		
		self.ip = ip
		self.port = port
		self.hostname = hostname
		self.timeout = timeout
		self.dc_ip = dc_ip
		self.domain = domain
		self.proxy = proxy
		self.protocol = protocol
		self.serverip = serverip
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
			serverip = self.serverip,
			dialect = self.dialect
		)
		return t
	
	@staticmethod
	def from_connection_string(s, is_rdp = True):
		port = 3389
		if is_rdp is False:
			port = 5900
		
		dc = None
		
		_, target = s.rsplit('@', 1)
		if target.find('/') != -1:
			target, dc = target.split('/')
			
		if target.find(':') != -1:
			target, port = target.split(':')
			
		st = RDPTarget()
		st.port = port
		st.dc_ip = dc
		st.domain, _ = s.split('/', 1)
		
		try:
			st.ip = str(ipaddress.ip_address(target))
		except:
			st.hostname = target
	
		return st
		
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