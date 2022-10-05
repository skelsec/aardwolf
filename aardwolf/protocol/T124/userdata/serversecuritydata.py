
import io
import enum

from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE, ENCRYPTION_FLAG, ENCRYPTION_LEVEL
from asn1crypto.x509 import Certificate

class CERT_CHAIN_VERSION(enum.Enum):
	VERSION_0 = 0x00000000 # same as ver1
	VERSION_1 = 0x00000001 #The certificate contained in the certData field is a Server Proprietary Certificate (section 2.2.1.4.3.1.1).
	VERSION_2 = 0x00000002

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/54e72cc6-3422-404c-a6b4-2486db125342
class SERVER_CERTIFICATE:
	def __init__(self):
		self.certChainVersion:int = None
		self.t:bool = None
		self.certData:bytes = None

		self.certificate = None
		self.exponent:int = None
		self.modulus:int = None
		self.bitlen:int = None
		
	def to_bytes(self):
		raise NotImplementedError()

	@staticmethod
	def from_bytes(bbuff: bytes):
		return SERVER_CERTIFICATE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = SERVER_CERTIFICATE()
		temp = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.certChainVersion = CERT_CHAIN_VERSION((temp << 1) >> 1)
		msg.t = bool(temp >> 31)
		if msg.certChainVersion in [CERT_CHAIN_VERSION.VERSION_1, CERT_CHAIN_VERSION.VERSION_0]:
			msg.certificate = PROPRIETARYSERVERCERTIFICATE.from_buffer(buff)
			msg.exponent = msg.certificate.PublicKeyBlob.pubExp
			msg.modulus = int.from_bytes(msg.certificate.PublicKeyBlob.modulus, byteorder='little', signed=False)
			msg.bitlen = msg.certificate.PublicKeyBlob.bitlen
		else:
			msg.certificate = Certificate.load(buff.read())
			msg.exponent = msg.certificate.public_key.native["public_key"]["public_exponent"]
			msg.modulus = msg.certificate.public_key.native["public_key"]["modulus"]
			msg.bitlen = msg.certificate.public_key.native["public_key"]["modulus"].bit_length()

		return msg
	
	def encrypt(self, secret: bytes):
		# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/761e2583-6406-4a71-bfec-cca52294c099
		# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/6fd7c8aa-884b-4b43-b036-c86d9d6737e6 <<< little???!!!
		
		temp = pow(int.from_bytes(secret, byteorder='little', signed = False), self.exponent, self.modulus)
		return temp.to_bytes((temp.bit_length() + 7) // 8, 'little').ljust((self.bitlen // 8) + 8, b'\x00')


	def __repr__(self):
		t = '==== SERVER_CERTIFICATE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/fe93545c-772a-4ade-9d02-ad1e0d81b6af
class RSA_PUBLIC_KEY:
	def __init__(self):
		self.magic:bytes = b'\x31\x41\x53\x52'
		self.keylen:int = None
		self.bitlen:int = None
		self.datalen:int = None
		self.pubExp:int = None
		self.modulus:bytes = None
		
	def to_bytes(self):
		t = self.magic
		t += len(self.modulus).to_bytes(4, byteorder='little', signed = False)
		t += self.bitlen.to_bytes(4, byteorder='little', signed = False)
		t += self.datalen.to_bytes(4, byteorder='little', signed = False)
		t += self.pubExp.to_bytes(4, byteorder='little', signed = False)
		t += self.modulus
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return RSA_PUBLIC_KEY.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = RSA_PUBLIC_KEY()
		msg.magic = buff.read(4)
		msg.keylen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.bitlen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.datalen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.pubExp = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.modulus = buff.read(msg.keylen)
		return msg

	def __repr__(self):
		t = '==== RSA_PUBLIC_KEY ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/a37d449a-73ac-4f00-9b9d-56cefc954634
class PROPRIETARYSERVERCERTIFICATE:
	def __init__(self):
		self.dwSigAlgId:int = None
		self.dwKeyAlgId:int = None
		self.wPublicKeyBlobType:int = None
		self.wPublicKeyBlobLen:int = None
		self.PublicKeyBlob:RSA_PUBLIC_KEY = None
		self.wSignatureBlobType:int = None
		self.wSignatureBlobLen:int = None
		self.SignatureBlob:bytes = None
		
	def to_bytes(self):
		t = self.dwSigAlgId.to_bytes(4, byteorder='little', signed = False)
		t += self.dwKeyAlgId.to_bytes(4, byteorder='little', signed = False)
		t += self.wPublicKeyBlobType.to_bytes(2, byteorder='little', signed = False)
		t += len(self.PublicKeyBlob.to_bytes()).to_bytes(2, byteorder='little', signed = False)
		t += self.PublicKeyBlob.to_bytes()
		t += self.wSignatureBlobType.to_bytes(2, byteorder='little', signed = False)
		t += len(self.SignatureBlob).to_bytes(2, byteorder='little', signed = False)
		t += self.SignatureBlob
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return PROPRIETARYSERVERCERTIFICATE.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = PROPRIETARYSERVERCERTIFICATE()
		msg.dwSigAlgId = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.dwKeyAlgId = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.wPublicKeyBlobType = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wPublicKeyBlobLen = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.PublicKeyBlob = RSA_PUBLIC_KEY.from_bytes(buff.read(msg.wPublicKeyBlobLen-8))
		zeros = buff.read(8) #
		msg.wSignatureBlobType = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.wSignatureBlobLen = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.SignatureBlob = buff.read(msg.wSignatureBlobLen-8)
		zeros = buff.read(8) #
		return msg

	def __repr__(self):
		t = '==== PROPRIETARYSERVERCERTIFICATE ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/379a020e-9925-4b4f-98f3-7d634e10b411
class TS_UD_SC_SEC1:
	def __init__(self):
		self.length:int = None
		self.type:TS_UD_TYPE = TS_UD_TYPE.SC_SECURITY
		self.encryptionMethod:ENCRYPTION_FLAG = None
		self.encryptionLevel:ENCRYPTION_LEVEL = None
		self.serverRandomLen:int = None
		self.serverCertLen:int = None
		self.serverRandom:bytes = None
		self.serverCertificate:SERVER_CERTIFICATE = None
		
	def to_bytes(self):
		def finish(t):
			t = (len(t)+4).to_bytes(2, byteorder='little', signed = False) + t
			t = self.type.value.to_bytes(2, byteorder='little', signed = False) + t
			return t
		t = self.encryptionMethod.value.to_bytes(4, byteorder='little', signed = False)
		t += self.encryptionLevel.value.to_bytes(4, byteorder='little', signed = False)
		t += len(self.serverRandom).to_bytes(4, byteorder='little', signed = False)
		t += len(self.serverCertificate).to_bytes(4, byteorder='little', signed = False)
		t += self.serverRandom
		if self.serverCertificate is not None:
			t += self.serverCertificate.to_bytes()
		return finish(t)

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_UD_SC_SEC1.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_UD_SC_SEC1()
		msg.type = TS_UD_TYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.length = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.encryptionMethod = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.encryptionLevel = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.serverRandomLen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.serverCertLen = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.serverRandom = buff.read(msg.serverRandomLen)

		if msg.serverCertLen > 0:
			msg.serverCertificate = SERVER_CERTIFICATE.from_bytes(buff.read(msg.serverCertLen))
		
		return msg

	def __repr__(self):
		t = '==== TS_UD_SC_SEC1 ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t