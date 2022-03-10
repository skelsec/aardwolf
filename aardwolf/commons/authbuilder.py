import enum
import platform
import os

import copy
from aardwolf.commons.credential import *
from aardwolf.commons.proxy import  RDPProxyType
from aardwolf.authentication.spnego.native import SPNEGO
from aardwolf.authentication.ntlm.native import NTLMAUTHHandler, NTLMHandlerSettings
from aardwolf.authentication.kerberos.native import RDPKerberos
from aardwolf.authentication.credssp.native import CredSSPAuth
from minikerberos.common.target import KerberosTarget
from minikerberos.common.proxy import KerberosProxy
from minikerberos.common.creds import KerberosCredential
from minikerberos.common.spn import KerberosSPN

from aardwolf.commons.target import RDPTarget


if platform.system().upper() == 'WINDOWS':
	from aardwolf.authentication.kerberos.sspi import RDPKerberosSSPI
	from aardwolf.authentication.ntlm.sspi import RDPNTLMSSPI

class AuthenticatorBuilder:
	def __init__(self):
		pass
	
	@staticmethod
	def wrap_credssp(spnego, credtype, cred):
		if credtype.find('KERBEROS') != -1:
			ntlm = spnego
		else:
			ntlm = spnego.get_original_context('NTLMSSP - Microsoft NTLM Security Support Provider')
		credssp_ctx = CredSSPAuth()
		credssp_ctx.auth_ctx = ntlm
		credssp_ctx.credtype = credtype
		credssp_ctx.cred = cred
		return credssp_ctx



	@staticmethod
	def to_credssp(creds:RDPCredential, target:RDPTarget = None):
		if creds.authentication_type == RDPAuthProtocol.PLAIN:
			ntlmcred = RDPNTLMCredential()
			ntlmcred.username = creds.username
			ntlmcred.domain = creds.domain if creds.domain is not None else ''
			ntlmcred.workstation = None
			ntlmcred.is_guest = False
			
			if creds.secret is None:
				if creds.username is None and creds.domain is None:
					ntlmcred.is_guest = True
				else:
					raise Exception('Authentication requres password!')
			
			ntlmcred.password = creds.secret
			
			settings = NTLMHandlerSettings(ntlmcred)
			handler = NTLMAUTHHandler(settings)
			
			#setting up SPNEGO
			spneg = SPNEGO()
			spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
			
			return AuthenticatorBuilder.wrap_credssp(spneg, 'NTLM', ntlmcred)

		elif creds.authentication_type == RDPAuthProtocol.NTLM:
			ntlmcred = RDPNTLMCredential()
			ntlmcred.username = creds.username
			ntlmcred.domain = creds.domain if creds.domain is not None else ''
			ntlmcred.workstation = None
			ntlmcred.is_guest = False
			
			if creds.secret is None:
				if creds.username is None and creds.domain is None:
					ntlmcred.is_guest = True
				else:
					raise Exception('NTLM authentication requres password!')
				
			if creds.secret_type == RDPCredentialsSecretType.NT:
				if isinstance(creds.secret, str) is True and len(creds.secret) != 32:
					raise Exception('This is not an NT hash!')
				ntlmcred.nt_hash = creds.secret
			elif creds.secret_type == RDPCredentialsSecretType.PASSWORD:
				ntlmcred.password = creds.secret
			
			settings = NTLMHandlerSettings(ntlmcred)
			handler = NTLMAUTHHandler(settings)
			
			#setting up SPNEGO
			spneg = SPNEGO()
			spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
			
			return AuthenticatorBuilder.wrap_credssp(spneg, 'NTLM', ntlmcred)
		
		elif creds.authentication_type == RDPAuthProtocol.KERBEROS:
			if target is None:
				raise Exception('Target must be specified with Kerberos!')
				
			if target.hostname is None:
				raise Exception('target must have a domain name or hostname for kerberos!')
				
			if target.dc_ip is None:
				raise Exception('target must have a dc_ip for kerberos!')
			
			if creds.secret_type == RDPCredentialsSecretType.KEYTAB:
				filename = creds.secret
				if creds.secret.upper() == 'ENV':
					filename = os.environ['KRB5KEYTAB']

				kc = KerberosCredential.from_keytab(filename, creds.username, creds.domain)

			elif creds.secret_type == RDPCredentialsSecretType.CCACHE:
				filename = creds.secret
				if creds.secret.upper() == 'ENV':
					try:
						filename = os.environ['KRB5CCACHE']
					except:
						raise Exception('Kerberos auth missing environment variable KRB5CCACHE')
				kc = KerberosCredential.from_ccache_file(filename)
				kc.username = creds.username
				kc.domain = creds.domain
			
			elif creds.secret_type == RDPCredentialsSecretType.KIRBI:
				filename = creds.secret
				kc = KerberosCredential.from_kirbi(filename)
				kc.username = creds.username
				kc.domain = creds.domain
			
			else:
				kc = KerberosCredential()
				kc.username = creds.username
				kc.domain = creds.domain
				if creds.secret_type == RDPCredentialsSecretType.PASSWORD:
					kc.password = creds.secret
				elif creds.secret_type == RDPCredentialsSecretType.NT:
					kc.nt_hash = creds.secret
					
				elif creds.secret_type == RDPCredentialsSecretType.AES:
					if len(creds.secret) == 32:
						kc.kerberos_key_aes_128 = creds.secret
					elif len(creds.secret) == 64:
						kc.kerberos_key_aes_256 = creds.secret
						
				elif creds.secret_type == RDPCredentialsSecretType.RC4:
					kc.kerberos_key_rc4 = creds.secret

			if kc is None:
				raise Exception('No suitable secret type found to set up kerberos!')
			
				
			kcred = RDPKerberosCredential()
			kcred.ccred = kc
			kcred.spn = KerberosSPN.from_target_string(target.to_target_string())
			
			if target.proxy is not None:
				if target.proxy.type == RDPProxyType.ASYSOCKS:
					kcred.target = KerberosTarget(target.dc_ip)
					kcred.target.proxy = KerberosProxy()
					kcred.target.proxy.target = copy.deepcopy(target.proxy.target)
					kcred.target.proxy.target[-1].endpoint_ip = target.dc_ip
					kcred.target.proxy.target[-1].endpoint_port = 88
				
				else:
					raise NotImplementedError("Proxy type '%s' not implemented!" % target.proxy.type)

			else:
				kcred.target = KerberosTarget(target.dc_ip)
			handler = RDPKerberos(kcred)
			#setting up SPNEGO
			spneg = SPNEGO()
			spneg.add_auth_context('MS KRB5 - Microsoft Kerberos 5', handler)
			return AuthenticatorBuilder.wrap_credssp(spneg, 'KERBEROS', kc)
			
		elif creds.authentication_type == RDPAuthProtocol.SSPI_KERBEROS:
			if target is None:
				raise Exception('Target must be specified with Kerberos SSPI!')
				
			kerbcred = RDPKerberosSSPICredential()
			kerbcred.client = None #creds.username #here we could submit the domain as well for impersonation? TODO!
			kerbcred.password = creds.secret
			kerbcred.target = target.to_target_string()
			
			handler = RDPKerberosSSPI(kerbcred)
			#setting up SPNEGO
			spneg = SPNEGO()
			spneg.add_auth_context('MS KRB5 - Microsoft Kerberos 5', handler)
			return AuthenticatorBuilder.wrap_credssp(spneg, 'SSPI-KERBEROS', kerbcred)
		
		elif creds.authentication_type == RDPAuthProtocol.SSPI_NTLM:
			ntlmcred = RDPNTLMSSPICredential()
			ntlmcred.client = creds.username #here we could submit the domain as well for impersonation? TODO!
			ntlmcred.password = creds.secret
			
			handler = RDPNTLMSSPI(ntlmcred)
			#setting up SPNEGO
			spneg = SPNEGO()
			spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
			return AuthenticatorBuilder.wrap_credssp(spneg, 'SSPI-NTLM', ntlmcred)

		elif creds.authentication_type.value.startswith('MPN'):
			if creds.authentication_type in [RDPAuthProtocol.MPN_SSL_NTLM, RDPAuthProtocol.MPN_NTLM]:
				from aardwolf.authentication.ntlm.mpn import RDPNTLMMPN
				ntlmcred = RDPMPNCredential()
				ntlmcred.type = 'NTLM'
				ntlmcred.is_ssl = True if creds.authentication_type == RDPAuthProtocol.MPN_SSL_NTLM else False
				ntlmcred.parse_settings(creds.settings)
				
				handler = RDPNTLMMPN(ntlmcred)
				#setting up SPNEGO
				spneg = SPNEGO()
				spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'MPN-NTLM', ntlmcred)

			elif creds.authentication_type in [RDPAuthProtocol.MPN_SSL_KERBEROS, RDPAuthProtocol.MPN_KERBEROS]:
				from aardwolf.authentication.kerberos.mpn import RDPKerberosMPN

				ntlmcred = RDPMPNCredential()
				ntlmcred.type = 'KERBEROS'
				ntlmcred.target = creds.target
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False
				ntlmcred.is_ssl = True if creds.authentication_type == RDPAuthProtocol.MPN_SSL_KERBEROS else False
				ntlmcred.parse_settings(creds.settings)

				handler = RDPKerberosMPN(ntlmcred)
				#setting up SPNEGO
				spneg = SPNEGO()
				spneg.add_auth_context('MS KRB5 - Microsoft Kerberos 5', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'MPN-KERBEROS', ntlmcred)

				

		elif creds.authentication_type.value.startswith('MULTIPLEXOR'):
			if creds.authentication_type in [RDPAuthProtocol.MULTIPLEXOR_SSL_NTLM, RDPAuthProtocol.MULTIPLEXOR_NTLM]:
				from aardwolf.authentication.ntlm.multiplexor import RDPNTLMMultiplexor

				ntlmcred = RDPMultiplexorCredential()
				ntlmcred.type = 'NTLM'
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False
				ntlmcred.is_ssl = True if creds.authentication_type == RDPAuthProtocol.MULTIPLEXOR_SSL_NTLM else False
				ntlmcred.parse_settings(creds.settings)
				
				handler = RDPNTLMMultiplexor(ntlmcred)
				#setting up SPNEGO
				spneg = SPNEGO()
				spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'MULTIPLEXOR-NTLM', ntlmcred)

			elif creds.authentication_type in [RDPAuthProtocol.MULTIPLEXOR_SSL_KERBEROS, RDPAuthProtocol.MULTIPLEXOR_KERBEROS]:
				from aardwolf.authentication.kerberos.multiplexor import RDPKerberosMultiplexor

				ntlmcred = RDPMultiplexorCredential()
				ntlmcred.type = 'KERBEROS'
				ntlmcred.target = creds.target
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False
				ntlmcred.is_ssl = True if creds.authentication_type == RDPAuthProtocol.MULTIPLEXOR_SSL_NTLM else False
				ntlmcred.parse_settings(creds.settings)

				handler = RDPKerberosMultiplexor(ntlmcred)
				#setting up SPNEGO
				spneg = SPNEGO()
				spneg.add_auth_context('MS KRB5 - Microsoft Kerberos 5', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'MULTIPLEXOR-KERBEROS', ntlmcred)

		elif creds.authentication_type.value.startswith('WSNET'):
			if creds.authentication_type in [RDPAuthProtocol.WSNET_NTLM]:
				from aardwolf.authentication.ntlm.wsnet import RDPWSNetNTLMAuth
				
				ntlmcred = RDPWSNETCredential()
				ntlmcred.type = 'NTLM'
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False
				
				handler = RDPWSNetNTLMAuth(ntlmcred)
				spneg = SPNEGO()
				spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'WSNET-NTLM', ntlmcred)
			

			elif creds.authentication_type in [RDPAuthProtocol.WSNET_KERBEROS]:
				from aardwolf.authentication.kerberos.wsnet import RDPWSNetKerberosAuth

				ntlmcred = RDPWSNETCredential()
				ntlmcred.type = 'KERBEROS'
				ntlmcred.target = creds.target
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False

				handler = RDPWSNetKerberosAuth(ntlmcred)
				#setting up SPNEGO
				spneg = SPNEGO()
				spneg.add_auth_context('MS KRB5 - Microsoft Kerberos 5', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'WSNET-KERBEROS', ntlmcred)
		
		elif creds.authentication_type.value.startswith('SSPIPROXY'):
			if creds.authentication_type == RDPAuthProtocol.SSPIPROXY_NTLM:
				from aardwolf.authentication.ntlm.sspiproxy import RDPSSPIProxyNTLMAuth
				
				ntlmcred = RDPSSPIProxyCredential()
				ntlmcred.type = 'NTLM'
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False
				ntlmcred.host = creds.settings['host'][0]
				ntlmcred.port = int(creds.settings['port'][0])
				ntlmcred.proto = 'ws'
				if 'proto' in creds.settings:
					ntlmcred.proto = creds.settings['proto'][0]
				if 'agentid' in creds.settings:
					ntlmcred.agent_id = bytes.fromhex(creds.settings['agentid'][0])
				
				handler = RDPSSPIProxyNTLMAuth(ntlmcred)
				spneg = SPNEGO()
				spneg.add_auth_context('NTLMSSP - Microsoft NTLM Security Support Provider', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'SSPIPROXY-NTLM', ntlmcred)
			

			elif creds.authentication_type == RDPAuthProtocol.SSPIPROXY_KERBEROS:
				from aardwolf.authentication.kerberos.sspiproxy import RDPSSPIProxyKerberosAuth

				ntlmcred = RDPSSPIProxyCredential()
				ntlmcred.type = 'KERBEROS'
				ntlmcred.target = creds.target
				if creds.username is not None:
					ntlmcred.username = '<CURRENT>'
				if creds.domain is not None:
					ntlmcred.domain = '<CURRENT>'
				if creds.secret is not None:
					ntlmcred.password = '<CURRENT>'
				ntlmcred.is_guest = False
				ntlmcred.host = creds.settings['host'][0]
				ntlmcred.port = int(creds.settings['port'][0])
				ntlmcred.proto = 'ws'
				if 'proto' in creds.settings:
					ntlmcred.proto = creds.settings['proto'][0]
				if 'agentid' in creds.settings:
					ntlmcred.agent_id = bytes.fromhex(creds.settings['agentid'][0])

				handler = RDPSSPIProxyKerberosAuth(ntlmcred)
				#setting up SPNEGO
				spneg = SPNEGO()
				spneg.add_auth_context('MS KRB5 - Microsoft Kerberos 5', handler)
				return AuthenticatorBuilder.wrap_credssp(spneg, 'SSPIPROXY-KERBEROS', ntlmcred)
		