
##this file is present to force pure ciphers to be used
## reason: pyinstaller cant do dynamic imports
## usage: overwrite the "symmetric.py" file with tihs one

from aardwolf.crypto.AES import pureAES
from aardwolf.crypto.DES import pureDES
from aardwolf.crypto.RC4 import pureRC4
from aardwolf.crypto.pure.AES.AESCCM import aesCCMEncrypt as ae
from aardwolf.crypto.pure.AES.AESCCM import aesCCMDecrypt as ad

DES = pureDES
AES = pureAES
RC4 = pureRC4

aesCCMEncrypt = ae
aesCCMDecrypt = ad
