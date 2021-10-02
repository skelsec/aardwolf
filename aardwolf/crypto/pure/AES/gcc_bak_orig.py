#from Cryptodome.Cipher import AES
import struct
from hashlib import sha256

from .AES import AESModeOfOperationCTR, AESModeOfOperationCBC, Counter
from .blockfeeder import Decrypter, Encrypter, PADDING_NONE

def aesCCMEncrypt(plaintext, aad, key, nonce, macLen = 16):
	blockSize = 16 # For AES...
	if macLen not in (4, 6, 8, 10, 12, 14, 16):
		raise ValueError("Parameter 'mac_len' must be even and in the range 4..16 (not %d)" % macLen)
	if not (nonce and 7 <= len(nonce) <= 13):
		raise ValueError("Length of parameter 'nonce' must be in the range 7..13 bytes")
			
	# Encryption
	q = 15 - len(nonce)
	#cipher = AES.new(key=key, mode=AES.MODE_CTR, nonce=struct.pack("B", q - 1) + nonce)
	t_nonce = struct.pack("B", q - 1) + nonce
	t_noncepad = b'\x00'*(blockSize - (len(t_nonce) % blockSize))
	t_nonce += t_noncepad
	#print(t_nonce.hex())
	ctr_start = Counter(int.from_bytes(t_nonce, byteorder='big', signed=False))
	cipher = AESModeOfOperationCTR(key, ctr_start)
	s0 = cipher.encrypt(b'\x00'*16) # For mac
	#print(f"My s0 {s0}")
	c =  cipher.encrypt(plaintext)
	
	# Mac
	pLen = len(plaintext)
	aadLen = len(aad)
	#mac = AES.new(key=key, mode=AES.MODE_CBC, iv=b'\x00'*blockSize)
	mac = Encrypter(AESModeOfOperationCBC(key, iv=b'\x00'*blockSize), padding = PADDING_NONE)
	flags = (64 * (aadLen > 0) + 8 * ((macLen - 2) // 2) + (q - 1))
	b0 = struct.pack("B", flags) + nonce +  pLen.to_bytes(q, 'big')
	
	
	assocLenEncoded = b''
	if aadLen > 0:
		if aadLen < (2 ** 16 - 2 ** 8):
			encSize = 2
		elif aadLen < (2 ** 32):
			assocLenEncoded = b'\xFF\xFE'
			encSize = 4
		else:
			assocLenEncoded = b'\xFF\xFF'
			encSize = 8
		
		assocLenEncoded += aadLen.to_bytes(encSize, 'big')
		
	
	aadPadded =  assocLenEncoded + aad 
	#print(f"aad Format before pad: {len(aadPadded)}" )
	aadPad = b''
	if len(aadPadded) % blockSize != 0:
		#print("need to padd aad")
		aadPad =  b'\x00'*(blockSize - (len(aadPadded) % blockSize))
	
	aadPadded += aadPad
	ptxtPadded = plaintext 
	#ptxt padding
	ptxtPad = b''
	if (pLen % blockSize) != 0:
		#print("Should pad ptxt")
		ptxtPad = b'\x00'*(blockSize - (pLen % blockSize))
	
	ptxtPadded += ptxtPad
	
	macData = b0  + aadPadded + ptxtPadded
	#print(f"MAC input {macData}")
	t = mac.feed(macData)
	t += mac.feed()
	t = t[-16:]
	tag = bytes([a ^ b for (a,b) in zip(t,s0)])[:macLen] 
	return (c, tag)



def aesCCMDecrypt(ciphertext, aad, key, nonce, macValue):
	# Decrytion: in CTR Encrypt == Decrypt
	blockSize = 16 # For AES...
	macLen = len(macValue)
	if macLen not in (4, 6, 8, 10, 12, 14, 16):
		raise ValueError("Parameter 'mac_len' must be even and in the range 4..16 (not %d)" % macLen)
	if not (nonce and 7 <= len(nonce) <= 13):
		 raise ValueError("Length of parameter 'nonce' must be in the range 7..13 bytes")
			
	# Decryption
	q = 15 - len(nonce) 
	#cipher = AES.new(key=key, mode=AES.MODE_CTR, nonce=struct.pack("B", q - 1) + nonce)
	t_nonce = struct.pack("B", q - 1) + nonce
	t_noncepad = b'\x00'*(blockSize - (len(t_nonce) % blockSize))
	t_nonce += t_noncepad
	#print(t_nonce.hex())
	ctr_start = Counter(int.from_bytes(t_nonce, byteorder='big', signed=False))
	cipher = AESModeOfOperationCTR(key, ctr_start)

	s0 = cipher.encrypt(b'\x00'*16) # For mac
	#print(f"My s0 {s0}")
	plaintext =  cipher.encrypt(ciphertext)
	#print(f"recoverd plaintex {plaintext}")
	# Mac
	pLen = len(plaintext)
	aadLen = len(aad)
	#mac = AES.new(key=key, mode=AES.MODE_CBC, iv=b'\x00'*blockSize)
	mac = Encrypter(AESModeOfOperationCBC(key, iv=b'\x00'*blockSize), padding = PADDING_NONE)
	flags = (64 * (aadLen > 0) + 8 * ((macLen - 2) // 2) + (q - 1))
	b0 = struct.pack("B", flags) + nonce +  pLen.to_bytes(q, 'big')
	
	
	assocLenEncoded = b''
	if aadLen > 0:
		if aadLen < (2 ** 16 - 2 ** 8):
			encSize = 2
		elif aadLen < (2 ** 32):
			assocLenEncoded = b'\xFF\xFE'
			encSize = 4
		else:
			assocLenEncoded = b'\xFF\xFF'
			encSize = 8
		
		assocLenEncoded += aadLen.to_bytes(encSize, 'big')
		
	
	aadPadded =  assocLenEncoded + aad 
	#print(f"aad Format before pad: {len(aadPadded)}" )
	aadPad = b''
	if len(aadPadded) % blockSize != 0:
		#print("need to padd aad")
		aadPad =  b'\x00'*(blockSize - (len(aadPadded) % blockSize))
	
	aadPadded += aadPad
	ptxtPadded = plaintext 
	#ptxt padding
	ptxtPad = b''
	if pLen % blockSize != 0:
		#print("Should pad ptxt")
		ptxtPad = b'\x00'*(blockSize - (pLen % blockSize))
	
	ptxtPadded += ptxtPad
	
	macData = b0  + aadPadded + ptxtPadded
	#t = mac.encrypt(macData)[-16:]
	t = mac.feed(macData)
	t += mac.feed()
	t = t[-16:]
	tag = bytes([a ^ b for (a,b) in zip(t,s0)])[:macLen] 
	
	return plaintext
	
	
	## Attempt to secure comparison... Idea: hash expected and received macs and compare the result in constant time...
	## Ideally should be done with HMAC with a RANDOM KEY! Doesn't cost much on a performance level.
	## For now we use shake_128(SHA3 without a key)
	print(f"received mac {macValue} \nComputed {tag}")
	h1 = sha256()
	h1.update(tag)
	digest1 = h1.digest() 
	
	h2 = sha256() 
	h2.update(macValue)
	digest2 = h2.digest()
	
	# Constant time comparison of hashes. Probably overkill here because of the randomization introduced by HMAC..
	result = 0
	for x, y in zip(digest1, digest2):
		result |= x ^ y
	
	#print(f"Reuslt {result}")
	
	if result != 0:
		raise ValueError("Incorrect MAC")
	else:
		return plaintext



