
from aardwolf.authentication.credssp.messages.asn1_structs import *

## this is not implemented yet!

"""
typedef struct _NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL {
      ULONG Version; 
      ULONG Flags;
      MSV1_0_CREDENTIAL_KEY_TYPE reserved;
      MSV1_0_CREDENTIAL_KEY reserved;
      ULONG reservedsize;
      [size_is(reservedSize)] UCHAR* reserved;
    } NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL; 




"""
import enum

class MSV1_0_CREDENTIAL_KEY_TYPE(enum.Enum):
	InvalidCredKey = 0 #        // reserved 
	IUMCredKey = 1 #             // reserved 
	DomainUserCredKey = 2 #     
	LocalUserCredKey = 3 #      // For internal use only - should never be present in MSV1_0_REMOTE_ENCRYPTED_SECRETS
	ExternallySuppliedCredKey = 4 # // reserved

class NRSC_FLAG(enum.IntFlag):
	LMOWF = 1
	NTOWF = 2
	CREDKEY_PRESENT = 8

class NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL:
	def __init__(self):
		self.Version:int = None
		self.Flags:int = None
		self.KeyType:MSV1_0_CREDENTIAL_KEY_TYPE = None
		self.Key:bytes = None
		self.reservedSize: int = None
		self.reserved6: bytes = None #size is 'reservedSize'

		
	def to_bytes(self):
		t  = self.Version.to_bytes(4, byteorder='little', signed = False)
		t += self.Flags.to_bytes(4, byteorder='little', signed = False)
		t += self.KeyType.value.to_bytes(4, byteorder='little', signed = False)
		t += self.Key
		t += len(self.reserved6).to_bytes(4, byteorder='little', signed = False)
		t += self.reserved6

		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL()
		msg.Version = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.Flags = NRSC_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.Key = buff.read(20)
		msg.KeyType = MSV1_0_CREDENTIAL_KEY_TYPE(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		msg.reservedSize = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.reserved6 = buff.read(msg.reservedSize)
		return msg

	def __repr__(self):
		t = '==== NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t



# TSRemoteGuardPackageCred
data = bytes.fromhex('3081dea00a04084e0054004c004d00a181cf0481cc0200ffff08000000d389fe0bc98d23bfef683a874e048c59000000000200000054000000ca7a124b7c282f0c714e025b3f5486310100000000000000000000000000000047e7674810c28f0cdb956d0aa1f4cac4005fb744b102871e16b207d789b3da815b9fac95ba79da02c2ba0e134472979f4b592621000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')

x = TSRemoteGuardPackageCred.load(data)
print(x.native)

print(x.native['credBuffer'])

credbuff = NTLM_REMOTE_SUPPLEMENTAL_CREDENTIAL.from_bytes(x.native['credBuffer'])
print(credbuff)

print(credbuff.reserved6[:16])
print(credbuff.reserved6[16:32])
print(credbuff.reserved6[32:])

data = bytes.fromhex('30820157a003020104a382014e0482014a050407ff0000001c00000000681ec3f55cbce0b2ef037dbe8afa8f7a6dbc5e7439ff675453fbcdb7cfd0c5b4af942453acf92677f21be4dc829c9e553280c5f37c08c5db5453330328d2fb8e65dd3f1a4f934d6888645365fee5e65888219f6dcaf5020ecea4a91595c1c95b1e3229d1b389c2ee23876e1c89a2fa3b06610201fce4a2427c8a95d52234c2343fbaaeeedecd636a0dc8b3fad75b3be9736ab488183e0bdc793dcce61fc019811970c1d56a02fcd7827ea64f60e163adf01b47ae1641d48ac719ba77c78ec5818d6a09c41c38da69b359a63a602319ab735243acf6c18d40307290d622bf6546a4650494b481228fcaaa62393e29fd10e6d31646eed50fa658eb0d8454ccf88dc4bf859cd98feed69d17fafce30bd03a6e0ccdccd55ba7cc146b60648308cabd2ee989e711675e4150da79ea9070df22223d2df1e41ed687a6575a2ecbce')
x = TSRequest.load(data)
print(x.native)