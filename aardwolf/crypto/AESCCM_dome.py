from Cryptodome.Cipher import AES

def aesCCMEncrypt(plaintext, aad, key, nonce, macLen = 16):
	cipher = AES.new(key, AES.MODE_CCM,  nonce)
	cipher.update(aad)
	ciphertext = cipher.encrypt(plaintext)
	mac = cipher.digest()
	return ciphertext, mac

def aesCCMDecrypt(ciphertext, aad, key, nonce, macValue):
	cipher = AES.new(key, AES.MODE_CCM,  nonce)
	cipher.update(aad)
	plaintext = cipher.encrypt(ciphertext)
	return plaintext
