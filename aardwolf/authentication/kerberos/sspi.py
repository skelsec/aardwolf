#
# This is just a simple interface to the winsspi library to support Kerberos
# Will only work on windows, ovbiously
# 
#
#

from aardwolf.authentication.spnego.asn1_structs import KRB5Token
from winsspi.sspi import KerberosMSLDAPSSPI
from winsspi.common.function_defs import ISC_REQ, GetSequenceNumberFromEncryptdataKerberos
from minikerberos.gssapi.gssapi import get_gssapi
from minikerberos.protocol.asn1_structs import AP_REQ, AP_REP
from minikerberos.protocol.encryption import Enctype, Key, _enctype_table

class RDPKerberosSSPI:
	def __init__(self, settings):
		self.iterations = 0
		self.settings = settings
		self.mode = 'CLIENT'
		self.ksspi = KerberosMSLDAPSSPI()
		self.client = None
		self.target = None
		self.gssapi = None
		self.etype = None
		self.actual_ctx_flags = None

		self.seq_number = None
		
		self.setup()

	def get_seq_number(self):
		"""
		Fetches the starting sequence number. This is either zero or can be found in the authenticator field of the 
		AP_REQ structure. As windows uses a random seq number AND a subkey as well, we can't obtain it by decrypting the 
		AP_REQ structure. Insead under the hood we perform an encryption operation via EncryptMessage API which will 
		yield the start sequence number
		"""
		self.seq_number = GetSequenceNumberFromEncryptdataKerberos(self.ksspi.context)
		return self.seq_number
		
	def setup(self):
		self.mode = self.settings.mode
		self.client = self.settings.client
		self.target = self.settings.target
		
	async def encrypt(self, data, message_no):
		return self.gssapi.GSS_Wrap(data, message_no)
		
	async def decrypt(self, data, message_no, direction='init', auth_data=None):
		return self.gssapi.GSS_Unwrap(data, message_no, direction=direction, auth_data=auth_data)
	
	def get_session_key(self):
		return self.ksspi.get_session_key()
	
	async def authenticate(self, authData = None, flags = ISC_REQ.CONNECTION, seq_number = 0, is_rpc = False):
		#authdata is only for api compatibility reasons
		if is_rpc == True:
			if self.iterations == 0:
				flags = ISC_REQ.CONFIDENTIALITY | \
						ISC_REQ.INTEGRITY | \
						ISC_REQ.MUTUAL_AUTH | \
						ISC_REQ.REPLAY_DETECT | \
						ISC_REQ.SEQUENCE_DETECT|\
						ISC_REQ.USE_DCE_STYLE
						
				token, self.actual_ctx_flags, err = self.ksspi.get_ticket_for_spn(self.target, flags = flags, is_rpc = True, token_data = authData)
				#print(token.hex())
				self.iterations += 1
				return token, True, None
			
			elif self.iterations == 1:
				flags = ISC_REQ.USE_DCE_STYLE		
				token, self.actual_ctx_flags, err = self.ksspi.get_ticket_for_spn(self.target, flags = flags, is_rpc = True, token_data = authData)
				
				aprep = AP_REP.load(token).native
				subkey = Key(aprep['enc-part']['etype'], self.get_session_key())

				self.get_seq_number()
				
				self.gssapi = get_gssapi(subkey)
				
				self.iterations += 1
				return token, False, None
				
			else:
				raise Exception('SSPI Kerberos -RPC - auth encountered too many calls for authenticate.')
			
		else:
			apreq, self.actual_ctx_flags, err = self.ksspi.get_ticket_for_spn(self.target, flags = flags)
			return apreq, False, None
		