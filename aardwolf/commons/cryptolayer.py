import os
from hashlib import md5, sha1
from aardwolf.crypto.symmetric import RC4

class RDPCryptoLayer:
	def __init__(self, ServerRandom, keysize = 128, is_FIPS = False):
		self.keysize = keysize
		self.ClientRandom:bytes = os.urandom(32) #os.urandom(keysize//8)
		self.ServerRandom:bytes = ServerRandom
		self.PacketCount:int = 0
		self.PreMasterSecret:bytes = self.First192Bits(self.ClientRandom) + self.First192Bits(self.ServerRandom)
		self.MasterSecret:bytes = None
		self.SessionKeyBlob:bytes = None
		self.MACKey128:bytes = None
		self.InitialServerEncryptKey128:bytes = None
		self.InitialServerDecryptKey128:bytes = None
		self.InitialClientDecryptKey128:bytes = None
		self.InitialClientEncryptKey128:bytes = None
		self.InitialServerEncryptKey128:bytes = None
		self.InitialServerDecryptKey128:bytes = None
		self.InitialClientDecryptKey128:bytes = None
		self.InitialClientEncryptKey128:bytes = None
		self.MACKey40:bytes = None
		self.InitialServerEncryptKey40:bytes = None
		self.InitialServerDecryptKey40:bytes = None
		self.InitialClientEncryptKey40:bytes = None
		self.InitialClientDecryptKey40:bytes = None
		self.MACKey56:bytes = None
		self.InitialServerEncryptKey56:bytes = None
		self.InitialServerDecryptKey56:bytes = None
		self.InitialClientEncryptKey56:bytes = None
		self.InitialClientDecryptKey56:bytes = None

		self.client_crypto_enc = None
		self.client_crypto_dec = None
		self.server_crypto_enc = None
		self.server_crypto_dec = None
		self.current_mac = None

		self.setup()

	def client_enc(self, data:bytes):
		self.PacketCount += 1
		return self.client_crypto_enc.encrypt(data)
	
	def client_dec(self, data:bytes):
		return self.client_crypto_dec.encrypt(data)
	
	def server_enc(self, data:bytes):
		return self.server_crypto_enc.encrypt(data)
	
	def server_dec(self, data:bytes):
		return self.server_crypto_dec.encrypt(data)
	
	def calc_mac(self, data:bytes):
		# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/7c61b54e-f6cd-4819-a59a-daf200f6bf94
		Pad1 = b'\x36'*40 # repeated 40 times to give 320 bits
		Pad2 = b'\x5C'*48 # repeated 48 times to give 384 bits

		DataLength = len(data).to_bytes(4, byteorder='little', signed=False)
		
		SHAComponent = sha1(self.current_mac + Pad1 + DataLength + data).digest()
		return self.First64Bits(md5(self.current_mac + Pad2 + SHAComponent).digest())

	def calc_salted_mac(self, data:bytes):
		# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/f390586a-3fdd-4a96-bbe0-a31575e92056
		Pad1 = b'\x36'*40 # repeated 40 times to give 320 bits
		Pad2 = b'\x5C'*48 # repeated 48 times to give 384 bits

		DataLength = len(data).to_bytes(4, byteorder='little', signed=False)
		EncryptionCount = self.PacketCount.to_bytes(4, byteorder='little', signed=False)
		
		SHAComponent = sha1(self.current_mac + Pad1 + DataLength + data + EncryptionCount).digest()
		return self.First64Bits(md5(self.current_mac + Pad2 + SHAComponent).digest())


	def setup(self):
		self.MasterSecret = self.PreMasterHash(b'\x41') + self.PreMasterHash(b'\x42\x42') + self.PreMasterHash(b'\x43\x43\x43')
		self.SessionKeyBlob = self.MasterHash(b'\x58') + self.MasterHash(b'\x59\x59') + self.MasterHash(b'\x5A\x5A\x5A')
		self.MACKey128 = self.First128Bits(self.SessionKeyBlob)

		self.InitialServerEncryptKey128 = self.FinalHash(self.Second128Bits(self.SessionKeyBlob))
		self.InitialServerDecryptKey128 = self.FinalHash(self.Third128Bits(self.SessionKeyBlob))
		self.InitialClientDecryptKey128 = self.FinalHash(self.Second128Bits(self.SessionKeyBlob))
		self.InitialClientEncryptKey128 = self.FinalHash(self.Third128Bits(self.SessionKeyBlob))

		self.MACKey40 = b'\xD1\x26\x9E' + self.Last40Bits(self.First64Bits(self.MACKey128))
  
		self.InitialServerEncryptKey40 = b'\xD1\x26\x9E' + self.Last40Bits(self.First64Bits(self.InitialServerEncryptKey128))
		self.InitialServerDecryptKey40 = b'\xD1\x26\x9E' + self.Last40Bits(self.First64Bits(self.InitialServerDecryptKey128))
		
		self.InitialClientEncryptKey40 = b'\xD1\x26\x9E' + self.Last40Bits(self.First64Bits(self.InitialClientEncryptKey128))
		self.InitialClientDecryptKey40 = b'\xD1\x26\x9E' + self.Last40Bits(self.First64Bits(self.InitialClientDecryptKey128))

		self.MACKey56 = b'\xD1' + self.Last56Bits(self.First64Bits(self.MACKey128))
  
		self.InitialServerEncryptKey56 = b'\xD1' + self.Last56Bits(self.First64Bits(self.InitialServerEncryptKey128))
		self.InitialServerDecryptKey56 = b'\xD1' + self.Last56Bits(self.First64Bits(self.InitialServerDecryptKey128))
		
		self.InitialClientEncryptKey56 = b'\xD1' + self.Last56Bits(self.First64Bits(self.InitialClientEncryptKey128))
		self.InitialClientDecryptKey56 = b'\xD1' + self.Last56Bits(self.First64Bits(self.InitialClientDecryptKey128))

		if self.keysize == 128:
			self.current_mac = self.MACKey128
			self.server_crypto_enc = RC4(self.InitialServerEncryptKey128)
			self.server_crypto_dec = RC4(self.InitialServerDecryptKey128)
			self.client_crypto_dec = RC4(self.InitialClientDecryptKey128)
			self.client_crypto_enc = RC4(self.InitialClientEncryptKey128)
		
		if self.keysize == 56:
			self.current_mac = self.MACKey56
			self.server_crypto_enc = RC4(self.InitialServerEncryptKey56)
			self.server_crypto_dec = RC4(self.InitialServerDecryptKey56)
			self.client_crypto_enc = RC4(self.InitialClientEncryptKey56)
			self.client_crypto_dec = RC4(self.InitialClientDecryptKey56)
		
		if self.keysize == 40:
			self.current_mac = self.MACKey40
			self.server_crypto_enc = RC4(self.InitialServerEncryptKey40)
			self.server_crypto_dec = RC4(self.InitialServerDecryptKey40)
			self.client_crypto_enc = RC4(self.InitialClientEncryptKey40)
			self.client_crypto_dec = RC4(self.InitialClientDecryptKey40)

	def Last56Bits(self, x:bytes):
		return x[-7:]

	def First64Bits(self, x:bytes):
		return x[:8]

	def Last40Bits(self, x:bytes):
		return x[-5:]

	def Second128Bits(self, x:bytes):
		return x[16:32]
	
	def Third128Bits(self, x:bytes):
		return x[32:48]

	def First192Bits(self, x:bytes):
		return x[:24]
	
	def First128Bits(self, x:bytes):
		return x[:16]
	
	def SaltedHash(self, S:bytes, I:bytes):
		return md5(S + sha1(I + S + self.ClientRandom + self.ServerRandom).digest()).digest()
	
	def MasterHash(self, I:bytes):
		return self.SaltedHash(self.MasterSecret, I)

	def FinalHash(self, K:bytes):
		return md5(K + self.ClientRandom + self.ServerRandom).digest()
	
	def PreMasterHash(self, x:bytes):
		return self.SaltedHash(self.PreMasterSecret, x)
	

	
