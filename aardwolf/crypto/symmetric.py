import importlib
import importlib.util

#
##key = name of the cipher, value=list of module names, in order of preference
preftable = {
	'DES' : ['pyCryptodome','pyCrypto','pure'], 
	'TDES': ['pyCryptodome','pyCrypto','pure'], 
	'AES' : ['pyCryptodome','cryptography','pyCrypto','pure'], 
	'RC4' : ['pyCryptodome','cryptography','pyCrypto','pure'],
}

#
available_modules = ['pure']

if importlib.util.find_spec("cryptography") is not None:
	#print('Found cryptography package!')
	available_modules.append("cryptography")

if importlib.util.find_spec("pyCrypto") is not None:
	#print('Found cryptography package!')
	available_modules.append("pyCrypto")

if importlib.util.find_spec("Cryptodome") is not None:
	#print('Found cryptography package!')
	available_modules.append("pyCryptodome")

#print(available_modules)

#https://stackoverflow.com/questions/8790003/dynamically-import-a-method-in-a-file-from-a-string
def import_from(module, name):
	module = __import__(module, fromlist=[name])
	return getattr(module, name)


def getPreferredCipher(cipherName):
	if cipherName not in preftable:
		raise Exception('Cipher %s doesnt have any preferences set!' % cipherName)
	#print('available_modules %s' % available_modules)
	possible_prefmodule = list(set(preftable[cipherName]).intersection(set(available_modules)))
	#print('possible_prefmodule %s' % possible_prefmodule)
	selected_module = None
	for moduleName in preftable[cipherName]:
		if moduleName in possible_prefmodule:
			selected_module = moduleName
			break

	if selected_module is None:
		raise Exception('Could not find any modules to load cipher %s' % cipherName)
	
	#print('Preferred module selected for cipher %s is %s' % (cipherName, selected_module))
	moduleName = 'aardwolf.crypto.%s' % cipherName
	objectName = selected_module + cipherName
	return import_from(moduleName , objectName)

def getSpecificCipher(cipherName, moduleBaseName):
	moduleName = 'aardwolf.crypto.%s' % cipherName
	objectName = '%s%s' % (moduleBaseName, cipherName)
	return import_from(moduleName , objectName)

def get_ccm_enc():
	if 'pyCryptodome' in available_modules:
		from aardwolf.crypto.AESCCM_dome import aesCCMEncrypt, aesCCMDecrypt
		return (aesCCMEncrypt, aesCCMDecrypt)
	
	else:
		from aardwolf.crypto.pure.AES.AESCCM import aesCCMEncrypt, aesCCMDecrypt
		return (aesCCMEncrypt, aesCCMDecrypt)

def get_gcm_enc():
	return None, None
	#if 'pyCryptodome' in available_modules:
	#	from aardwolf.crypto.AESGCM_dome import aesGCMEncrypt, aesGCMEncrypt
	#	print('pyCryptodome')
	#	return (aesGCMEncrypt, aesGCMEncrypt)
	#
	#else:
	#	from aardwolf.crypto.pure.AES.AESGCM import aesGCMEncrypt, aesGCMDecrypt
	#	return (aesGCMEncrypt, aesGCMDecrypt)


#import ciphers
# TODO: fix the dynamic imports, currently only supporting pure-python ciphers for two reasons:
# 1. dynamic import messes up some scripts like pyinstaller/nuitka/py2exe
# 2. additional effort needed to support more crypto libs anyhow



from aardwolf.crypto.DES import pureDES

DES  = getPreferredCipher('DES')
AES  = getPreferredCipher('AES')
RC4  = getPreferredCipher('RC4')

#TDES = getPreferredCipher('TDES')

aesCCMEncrypt, aesCCMDecrypt = get_ccm_enc()
#aesGCMEncrypt, aesGCMDecrypt = get_gcm_enc()


#from aardwolf.crypto.AES import pureAES
#from aardwolf.crypto.DES import pureDES
#from aardwolf.crypto.DES import pureRC4

#DES = pureDES #getPreferredCipher('DES')
#AES = pureAES #getPreferredCipher('AES')
#RC4 = pureRC4
