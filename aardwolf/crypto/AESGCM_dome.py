from Cryptodome.Cipher import AES

def aesGCMEncrypt(plaintext, aad, key, nonce, macLen = 16):
	cipher = AES.new(key, AES.MODE_GCM,  nonce=nonce)
	cipher.update(aad)
	return cipher.encrypt_and_digest(plaintext)

def aesGCMDecrypt(ciphertext, aad, key, nonce, macValue):
	cipher = AES.new(key, AES.MODE_GCM,  nonce=nonce)
	cipher.update(aad)
	plaintext = cipher.decrypt(ciphertext)
	return plaintext
