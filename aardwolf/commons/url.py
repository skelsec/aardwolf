import enum
from urllib.parse import urlparse, parse_qs
from aardwolf.commons.credential import RDPCredential, RDPCredentialsSecretType, RDPAuthProtocol
from aardwolf.commons.proxy import RDPProxy
from aardwolf.commons.target import RDPTarget, RDPConnectionDialect, RDPConnectionProtocol
from aardwolf.commons.authbuilder import AuthenticatorBuilder
from aardwolf.connection import RDPConnection
from aardwolf.vncconnection import VNCConnection
from getpass import getpass
import base64
import ipaddress
import copy


class RDPConnectionURL:
	def __init__(self, connection_url, target = None, cred = None, proxy = None):
		self.connection_url = connection_url
		
		#credential
		self.authentication_protocol = None
		self.secret_type = None
		self.domain = None
		self.username = None
		self.secret = None
		self.is_anonymous = None
		self.auth_settings = {}
		self.cred = cred

		#target
		self.dialect = None
		self.protocol = None
		self.hostname = None
		self.dc_ip = None
		self.port = None
		self.ip = None
		self.timeout = 5
		self.serverip = None
		self.fragment = None
		self.path = None
		self.compression = False
		self.scheme = None

		self.target = target

		#proxy
		self.proxy = proxy

		if self.connection_url is not None:
			self.parse()

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
		credential.target = ip_or_hostname

		target = self.get_target()
		try:
			ipaddress.ip_address(ip_or_hostname)
			target.ip = ip_or_hostname
			target.hostname = None
		except:
			target.hostname = ip_or_hostname
			target.ip = ip_or_hostname

		#spneg = AuthenticatorBuilder.to_credssp(credential, target)
		if target.dialect == RDPConnectionDialect.RDP:
			return RDPConnection(target, credential, tio)
		elif target.dialect == RDPConnectionDialect.VNC:
			return VNCConnection(target, credential, tio)
		else:
			raise Exception('Unknown dialect %s' % target.dialect)

	def get_file(self):
		return RDPFile.from_RDPurl(self)

	def get_proxy(self):
		if self.proxy is not None:
			copy.deepcopy(self.proxy)
		return None

	def get_target(self):
		if self.target is not None:
			return copy.deepcopy(self.target)

		if self.ip is not None and self.hostname is None:
			try:
				ipaddress.ip_address(self.ip)
			except:
				self.hostname = self.ip
		if self.serverip is not None:
			self.ip = self.serverip
			
		t = RDPTarget(
			ip = self.ip, 
			port = self.port, 
			hostname = self.hostname, 
			timeout = self.timeout, 
			dc_ip= self.dc_ip, 
			domain = self.domain, 
			proxy = self.get_proxy(),
			protocol=self.protocol,
			dialect=self.dialect
		)
		return t

	def get_credential(self):
		if self.cred is not None:
			return copy.deepcopy(self.cred)
		return RDPCredential(
			username = self.username,
			domain = self.domain, 
			secret = self.secret, 
			secret_type = self.secret_type, 
			authentication_type = self.authentication_protocol, 
			settings = self.auth_settings,
			target = self.ip
		)
	

	def scheme_decoder(self, scheme):
		self.schemes = scheme.upper().split('+')
		
		connection_tags = self.schemes[0].split('-')
		if len(connection_tags) > 1:
			self.dialect = RDPConnectionDialect(connection_tags[0])
			self.protocol = RDPConnectionProtocol(connection_tags[1])
		else:
			self.dialect = RDPConnectionDialect(connection_tags[0])
			self.protocol = RDPConnectionProtocol.TCP

		if len(self.schemes) == 1:
			# user did not specify a requested auth scheme, defaulting to plain
			# later on when server requires credssp this will be converted to NTLM
			self.authentication_protocol = RDPAuthProtocol.PLAIN
			self.secret_type = RDPCredentialsSecretType.PASSWORD
			return

		auth_tags = self.schemes[1].replace('-','_')
		try:
			self.authentication_protocol = RDPAuthProtocol(auth_tags)
		except:
			auth_tags = self.schemes[1].split('-')
			#print(auth_tags)
			if len(auth_tags) > 1:
				if auth_tags[0] == 'MULTIPLEXOR':
					if auth_tags[1] == 'SSL':
						if len(auth_tags) == 2:
							self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_SSL_NTLM
						else:
							if auth_tags[2] == 'NTLM':
								self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_SSL_NTLM
							elif auth_tags[2] == 'KERBEROS':
								self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_SSL_KERBEROS
					else:
						if auth_tags[1] == 'NTLM':
							self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_NTLM
						elif auth_tags[1] == 'KERBEROS':
							self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_KERBEROS
				elif auth_tags[0] == 'SSPI':
					if auth_tags[1] == 'NTLM':
						self.authentication_protocol = RDPAuthProtocol.SSPI_NTLM
					elif auth_tags[1] == 'KERBEROS':
						self.authentication_protocol = RDPAuthProtocol.SSPI_KERBEROS
				else:
					self.authentication_protocol = RDPAuthProtocol(auth_tags[0])
					self.secret_type = RDPCredentialsSecretType(auth_tags[1])
			else:
				if auth_tags[0] == 'MULTIPLEXOR':
					self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_NTLM
				elif auth_tags[0] == 'MULTIPLEXOR_SSL':
					self.authentication_protocol = RDPAuthProtocol.MULTIPLEXOR_SSL_NTLM
				if auth_tags[0] == 'SSPI':
					self.authentication_protocol = RDPAuthProtocol.SSPI_NTLM
				else:
					self.authentication_protocol = RDPAuthProtocol(auth_tags[0])
				if self.authentication_protocol == RDPAuthProtocol.KERBEROS:
					raise Exception('For kerberos auth you need to specify the secret type in the connection string!')

	def __str__(self):
		t = '==== RDPConnectionURL ====\r\n'
		for k in self.__dict__:
			val = self.__dict__[k]
			if isinstance(val, enum.IntFlag):
				val = val
			elif isinstance(val, enum.Enum):
				val = val.name
			
			t += '%s: %s\r\n' % (k, str(val))
			
		return t

	def parse(self):
		url_e = urlparse(self.connection_url)
		self.scheme_decoder(url_e.scheme)
		
		if url_e.username is not None:
			if url_e.username.find('\\') != -1:
				self.domain , self.username = url_e.username.split('\\')
				if self.domain == '.':
					self.domain = None
			else:
				self.domain = None
				self.username = url_e.username
		
		self.secret = url_e.password
		
		if self.secret_type == RDPCredentialsSecretType.PWPROMPT:
			self.secret_type = RDPCredentialsSecretType.PASSWORD
			self.secret = getpass()

		if self.secret_type == RDPCredentialsSecretType.PWHEX:
			self.secret_type = RDPCredentialsSecretType.PASSWORD
			self.secret = bytes.fromhex(self.secret).decode()
		
		if self.secret_type == RDPCredentialsSecretType.PWB64:
			self.secret_type = RDPCredentialsSecretType.PASSWORD
			self.secret = base64.b64decode(self.secret).decode()
		
		if self.secret is None and self.username is None:
			self.is_anonymous = True
		
		if self.authentication_protocol == RDPAuthProtocol.NTLM and self.secret_type is None:
			if self.is_anonymous == True:
				self.secret_type = RDPCredentialsSecretType.NONE
			else:
				if len(self.secret) == 32:
					try:
						bytes.fromhex(self.secret)
					except:
						self.secret_type = RDPCredentialsSecretType.NT
					else:
						self.secret_type = RDPCredentialsSecretType.PASSWORD

		elif self.authentication_protocol in [RDPAuthProtocol.SSPI_KERBEROS, RDPAuthProtocol.SSPI_NTLM, 
												RDPAuthProtocol.MULTIPLEXOR_NTLM, RDPAuthProtocol.MULTIPLEXOR_KERBEROS]:
			if self.username is None:
				self.username = '<CURRENT>'
			if self.domain is None:
				self.domain = '<CURRENT>'
			if self.secret is None:
				self.secret = '<CURRENT>'


		self.ip = url_e.hostname
		if url_e.port:
			self.port = url_e.port
		elif self.protocol == RDPConnectionProtocol.TCP and self.dialect == RDPConnectionDialect.RDP:
			self.port = 3389
		elif self.protocol == RDPConnectionProtocol.TCP and self.dialect == RDPConnectionDialect.VNC:
			self.port = 5800
		#elif self.protocol == RDPConnectionProtocol.QUIC:
		#	self.port = 443
		else:
			raise Exception('Port must be provided!')

		if url_e.path not in ['/', '', None]:
			self.path = url_e.path
		

		# recognized parameters :
		# dc -> domain controller IP
		# proxytype -> proxy protocol
		# proxyuser -> username for proxy auth
		# proxypass -> password for proxy auth
		#  
		#
		proxy_present = False
		if url_e.query is not None:
			query = parse_qs(url_e.query)
			for k in query:
				if k.startswith('proxy') is True:
					proxy_present = True
				if k == 'dc':
					self.dc_ip = query[k][0]
				elif k == 'timeout':
					self.timeout = int(query[k][0])
				elif k == 'serverip':
					self.serverip = query[k][0]
				elif k == 'fragment':
					self.fragment = int(query[k][0])
				elif k == 'dns':
					self.dns = query[k] #multiple dns can be set, so not trimming here
				elif k == 'compress':
					self.compression = int(query[k][0])
				elif k.startswith('auth'):
					self.auth_settings[k[len('auth'):]] = query[k]
				elif k.startswith('same'):
					self.auth_settings[k[len('same'):]] = query[k]
		
		if proxy_present is True:
			self.proxy = RDPProxy.from_params(self.connection_url)
			
if __name__ == '__main__':
	from aardwolf.commons.interfaces.file import RDPFile
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
			dec = RDPConnectionURL(url)
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
			
			
