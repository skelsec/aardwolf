
import os
from aardwolf import logger
from aardwolf.authentication.spnego.native import SPNEGO
from aardwolf.authentication.credssp.messages.asn1_structs import *
from hashlib import sha256

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/385a7489-d46b-464c-b224-f7340e308a5c

class CredSSPAuth:
	def __init__(self, mode = 'CLIENT'):
		self.mode = mode
		self.auth_ctx:SPNEGO = None
		self.credtype:str = None
		self.cred = None
		self.version = 4 #ver 5 and 6 not working TODO
		self.nonce = os.urandom(32)
		self.__internal_auth_continue = True
		self.seqno = 0

	def get_extra_info(self):
		return self.auth_ctx.get_extra_info()

	async def authenticate(self, token, flags = None, pubkey = None, remote_credguard = False):
		try:
			# currently only SSPI supported

			if self.mode != 'CLIENT':
				raise NotImplementedError()
			else:
				if token is None:
					# initial auth
					returndata, self.__internal_auth_continue, err = await self.auth_ctx.authenticate(token, flags = flags, seq_number = None)
					if err is not None:
						raise err
					
					negotoken = {
						'negoToken' : returndata
					}
					retoken = {
						'version' : self.version,
						'negoTokens' : NegoDatas([NegoData(negotoken)])
					}
					return TSRequest(retoken).dump(), True, None
				else:
					if self.__internal_auth_continue is True:
						tdata = TSRequest.load(token)
						if tdata.native['version'] < self.version:
							logger.debug('[CREDSSP] Server supports version %s which is smaller than our supported version %s' % (tdata.native['version'], self.version))
							self.version = tdata.native['version']
						if tdata.native['negoTokens'] is None:
							raise Exception('SSPI auth not supported by server')
						sspitoken = tdata.native['negoTokens'][0]['negoToken']
						returndata, self.__internal_auth_continue, err = await self.auth_ctx.authenticate(sspitoken, flags = flags)
						if err is not None:
							raise err
						
						negotoken = {
							'negoToken' : returndata
						}
						retoken = {
							'version' : self.version,
						}
						if returndata is not None:
							retoken['negoTokens'] = NegoDatas([NegoData(negotoken)])
						
						
						if self.__internal_auth_continue is False:
							if self.version in [5,6]:
								ClientServerHashMagic = b"CredSSP Client-To-Server Binding Hash\x00"
								ClientServerHash = sha256(ClientServerHashMagic + self.nonce + pubkey).digest()
								sealedMessage, signature = await self.auth_ctx.encrypt(ClientServerHash, self.seqno)
								self.seqno += 1
								#print(sealedMessage)
								retoken['pubKeyAuth'] = signature+sealedMessage
								retoken['clientNonce'] = self.nonce
							
							elif self.version in [2,3,4]:
								sealedMessage, signature = await self.auth_ctx.encrypt(pubkey, self.seqno)
								self.seqno += 1
								#print(sealedMessage)
								retoken['pubKeyAuth'] = signature+sealedMessage
						
						return TSRequest(retoken).dump(), True, None
					else:
						# sub-level auth protocol finished, now for the other stuff
						
						# waiting for server to reply with the re-encrypted verification string + b'\x01'
						tdata = TSRequest.load(token).native
						if tdata['errorCode'] is not None:
							raise Exception('CredSSP - Server sent an error! Code: %s' % tdata['errorCode'])
						if tdata['pubKeyAuth'] is None:
							raise Exception('Missing pubKeyAuth')
						verification_data, _ = await self.auth_ctx.decrypt(tdata['pubKeyAuth'], 0)
						#print('DEC: %s' % verification_data)

						# at this point the verification should be implemented
						# TODO: maybe later...

						
						# sending credentials
						if remote_credguard is False:
							creds = {
								'domainName' : b'',
								'userName'   : b'',
								'password'   : b'',
							}
							if self.cred.password is not None:
								creds = {
									'domainName' : self.cred.domain.encode('utf-16-le'),
									'userName'   : self.cred.username.encode('utf-16-le'),
									'password'   : self.cred.password.encode('utf-16-le'),
								}							 
								 
										
							res = TSPasswordCreds(creds)
							res = TSCredentials({'credType': 1, 'credentials': res.dump()})
							sealedMessage, signature = await self.auth_ctx.encrypt(res.dump(), self.seqno) #seq number must be incremented here..
							self.seqno += 1
							retoken = {
								'version' : self.version,
								'authInfo' : signature+sealedMessage
							}
							return TSRequest(retoken).dump(), False, None
						else:
							credBuffer = b''
							data = {
								'packageName' : 'KERBEROS'.encode('utf-16-le'), #dont forget the encoding!
								'credBuffer' : credBuffer
							}

							remcredguardcreds = TSRemoteGuardCreds({
								'logonCred' : TSRemoteGuardPackageCred(data),
								#'supplementalCreds' : [TSRemoteGuardPackageCred(xxxx)]
							})

							#print(remcredguardcreds)
							sealedMessage, signature = await self.auth_ctx.encrypt(remcredguardcreds.dump(), self.seqno) #seq number must be incremented here..
							self.seqno += 1

							retoken = {
								'version' : self.version,
								'authInfo' : signature+sealedMessage
							}
							return TSRequest(retoken).dump(), False, None
						
		except Exception as e:
			return None, None, e