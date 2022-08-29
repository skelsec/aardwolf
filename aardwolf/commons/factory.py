import enum
from typing import List
from asysocks.unicomm.common.proxy import UniProxyProto, UniProxyTarget
from aardwolf.commons.iosettings import RDPIOSettings

from aardwolf.commons.target import RDPTarget, RDPConnectionDialect
from asyauth.common.credentials import UniCredential
from aardwolf.connection import RDPConnection
from aardwolf.vncconnection import VNCConnection
import ipaddress
import copy


class RDPConnectionFactory:
	def __init__(self, iosettings=None, target:RDPTarget = None, credential:UniCredential = None, proxies:List[UniProxyTarget] = None):
		self.credential = credential
		self.target = target
		self.proxies = proxies
		self.iosettings = iosettings

	def get_connection(self, iosettings):
		tio = copy.deepcopy(iosettings)
		credential = self.get_credential()
		target = self.get_target()
		if target.dialect is not None:
			if target.dialect == RDPConnectionDialect.RDP:
				return RDPConnection(target, credential, tio)
			elif target.dialect == RDPConnectionDialect.VNC:
				return VNCConnection(target, credential, tio)
			else:
				raise Exception('Unknown dialect %s' % target.dialect)
		raise Exception('Either target or dialect must be defined first!')

	def create_connection_newtarget(self, ip_or_hostname, iosettings):
		tio = copy.deepcopy(iosettings)
		credential = self.get_credential()

		target = self.get_target()
		try:
			ipaddress.ip_address(ip_or_hostname)
			target.ip = ip_or_hostname
			target.hostname = None
		except:
			target.hostname = ip_or_hostname
			target.ip = ip_or_hostname

		if target.dialect == RDPConnectionDialect.RDP:
			return RDPConnection(target, credential, tio)
		elif target.dialect == RDPConnectionDialect.VNC:
			return VNCConnection(target, credential, tio)
		else:
			raise Exception('Unknown dialect %s' % target.dialect)

	def get_proxy(self) -> List[UniProxyTarget]:
		return copy.deepcopy(self.target.proxies)

	def get_target(self) -> RDPTarget:
		return copy.deepcopy(self.target)	

	def get_credential(self) -> UniCredential:
		return copy.deepcopy(self.credential)
	
	def get_settings(self) -> RDPIOSettings:
		return copy.deepcopy(self.iosettings)

	@staticmethod
	def from_url(connection_url, iosettings):
		target = RDPTarget.from_url(connection_url)
		credential = UniCredential.from_url(connection_url)
		return RDPConnectionFactory(iosettings, target, credential)


	def __str__(self):
		t = '==== RDPConnectionFactory ====\r\n'
		for k in self.__dict__:
			val = self.__dict__[k]
			if isinstance(val, enum.IntFlag):
				val = val
			elif isinstance(val, enum.Enum):
				val = val.name
			
			t += '%s: %s\r\n' % (k, str(val))
			
		return t

	
			
if __name__ == '__main__':
	url_tests = [
		#'RDP://10.10.10.2',
		#'RDP://10.10.10.2:9000',
		#'RDP-tcp://10.10.10.2',
		#'RDP-tcp://10.10.10.2:9000',
		#'RDP-udp://10.10.10.2:138',
		#'RDP+ntlm-password://domain\\user@10.10.10.2',
		#'RDP-tcp+ntlm-password://domain\\user:password@10.10.10.2',
		#'RDP-tcp+ntlm-password://domain\\user:password@10.10.10.2:10000',
		#'RDP-tcp+ntlm-nt://domain\\user:alma@10.10.10.2',
		#'RDP+ntlm-nt://domain\\user:alma@10.10.10.2',
		#'RDP+ntlm-nt://domain\\user:alma@10.10.10.2',
		#'RDP-tcp+kerberos-password://domain\\alma:password@10.10.10.10.2',
		#'RDP-tcp+kerberos-aes://domain\\alma:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@10.10.10.10.2',
		#'RDP-tcp+kerberos-aes://domain\\alma:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@10.10.10.10.2',
		#'RDP-tcp+kerberos-nt://domain\\alma:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@10.10.10.10.2',
		#'RDP-tcp+kerberos-rc4://domain\\alma:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@10.10.10.10.2',
		#'RDP+sspi://10.10.10.10.2',
		#'RDP+sspi-ntlm://10.10.10.10.2',
		#'RDP+sspi-kerberos://10.10.10.10.2',
		#'RDP+multiplexor://10.10.10.10.2',
		#'RDP+multiplexor-ssl://10.10.10.10.2',
		#'RDP+multiplexor-ssl-ntlm://10.10.10.10.2',
		#'RDP+multiplexor-ssl-kerberos://10.10.10.10.2',
		#'RDP://10.10.10.2/?timeout=10',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=socks5',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=socks5&proxyserver=127.0.0.1',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=socks5&proxyserver=127.0.0.1&proxyuser=admin&proxypass=alma',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=socks5&proxyserver=127.0.0.1&proxyuser=admin&proxypass=alma&dc=10.10.10.2&dns=8.8.8.8',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=socks5-ssl&proxyserver=127.0.0.1&proxyuser=admin&proxypass=alma&dc=10.10.10.2&dns=8.8.8.8',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=multiplexor&proxyserver=127.0.0.1',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=multiplexor&proxyserver=127.0.0.1&proxyagentid=alma',
		#'RDP://10.10.10.2/?timeout=10&dc=10.10.10.2&proxytype=multiplexor&proxyserver=127.0.0.1&proxyagentid=alma&proxytimeout=111',
		'RDP://10.10.10.2/C$/test/tst111.dmp?timeout=10&dc=10.10.10.2&proxytype=multiplexor&proxyhost=127.0.0.1&proxyport=1&proxyagentid=alma&proxytimeout=111',

	]
	for url in url_tests:
		print('===========================================================================')
		print(url)
		try:
			dec = RDPConnectionFactory.from_url(url)
			creds = dec.get_credential()
			target = dec.get_target()
			RDPfile = dec.get_file()
			print(RDPfile)
		except Exception as e:
			import traceback
			traceback.print_exc()
			print('ERROR! Reason: %s' % e)
			input()
		else:
			print(str(creds))
			print(str(target))
			input()
			
			
