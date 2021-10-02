from Cryptodome.Cipher import AES

import struct


# https://tools.ietf.org/html/rfc3610

def aesCCMEncrypt(plaintext, aad, key, nonce, macLen):
	blockSize = 16 # For AES...
	if macLen not in (4, 6, 8, 10, 12, 14, 16):
		raise ValueError("Parameter 'mac_len' must be even and in the range 4..16 (not %d)" % macLen)
	if not (nonce and 7 <= len(nonce) <= 13):
		raise ValueError("Length of parameter 'nonce' must be in the range 7..13 bytes")
			

	# Encryption
	q = 15 - len(nonce) 
	cipher = AES.new(key=key, mode=AES.MODE_CTR, nonce=struct.pack("B", q - 1) + nonce)
	s0 = cipher.encrypt(b'\x00'*16) # For mac
	c =  cipher.encrypt(plaintext)
	
	# Mac
	pLen = len(plaintext)
	aadLen = len(aad)
	mac = AES.new(key=key, mode=AES.MODE_CBC, iv=b'\x00'*blockSize)
	flags = (64 * (aadLen > 0) + 8 * ((macLen - 2) // 2) + (q - 1))
	b0 = struct.pack("B", flags) + nonce +  pLen.to_bytes(q, 'big')
	
	
	assocLenEncoded = b''
	if aadLen > 0:
		if aadLen < (2 ** 16 - 2 ** 8):
			encsize = 2
		elif aadLen < (2 ** 32):
			assocLenEncoded = b'\xFF\xFE'
			encsize = 4
		else:
			assocLenEncoded = b'\xFF\xFF'
			encsize = 8
		assocLenEncoded += aadLen.to_bytes(encsize, 'big')
		
	print(f"Length of block 0: {len(b0)}" )
	aadPadded =  assocLenEncoded + aad 
	aadPadded += b'\x00'*(blockSize - (len(aadPadded) % blockSize))
	ptxtPadded = plaintext + b'\x00'*(blockSize - (pLen % blockSize))
	macData = b0  + aadPadded + ptxtPadded
	print(f"Length of MAC input {len(macData)}")
	t = mac.encrypt(macData)[-16:]
	tag = bytes([a ^ b for (a,b) in zip(t,s0)])
	return (c, tag)



if __name__ == '__main__':
	import os
	EncryptionKey = b'\xff'*16
	nonce = os.urandom(11)
	hdr = b'\xFF'* 40
	msg_data = b'\xAA' * 1024

	cipher = AES.new(EncryptionKey, AES.MODE_CCM, nonce)
	cipher.update(hdr)
	enc_data = cipher.encrypt(msg_data)
	sig = cipher.digest()
	
	print(enc_data.hex())
	print(sig.hex())


	c, t = aesCCMEncrypt(msg_data, hdr, EncryptionKey, nonce, 16)

	print('other')
	print(c.hex())
	print(t.hex())

	if c == enc_data:
		print('Encryption OK!')
	else:
		print('Encryption fail')
