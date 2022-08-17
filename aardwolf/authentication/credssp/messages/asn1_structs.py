
from asn1crypto.core import Integer, ObjectIdentifier, Sequence, SequenceOf, Enumerated, GeneralString, OctetString, BitString, Choice, Any, Boolean

TAG = 'explicit'

# class
UNIVERSAL = 0
APPLICATION = 1
CONTEXT = 2

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/9664994d-0784-4659-b85b-83b8d54c2336
#  NegoData ::= SEQUENCE OF SEQUENCE {
#         negoToken [0] OCTET STRING
# }

class NegoData(Sequence):
	_fields = [
		('negoToken', OctetString, {'explicit': 0}),]

class NegoDatas(SequenceOf):
	_child_spec = NegoData


# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/6aac4dea-08ef-47a6-8747-22ea7f6d8685
#  TSRequest ::= SEQUENCE {
#         version    [0] INTEGER,
#         negoTokens [1] NegoData  OPTIONAL,
#         authInfo   [2] OCTET STRING OPTIONAL,
#         pubKeyAuth [3] OCTET STRING OPTIONAL,
#         errorCode  [4] INTEGER OPTIONAL,
#         clientNonce [5] OCTET STRING OPTIONAL
# }

class TSRequest(Sequence):
	_fields = [
		('version', Integer, {'explicit': 0}),
		('negoTokens', NegoDatas, {'explicit': 1, 'optional': True}),
		('authInfo', OctetString, {'explicit': 2, 'optional': True}),
		('pubKeyAuth', OctetString, {'explicit': 3, 'optional': True}),
		('errorCode', Integer, {'explicit': 4, 'optional': True}),
		('clientNonce', OctetString, {'explicit': 5, 'optional': True}),
]



# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/94a1ab00-5500-42fd-8d3d-7a84e6c2cf03
# TSCredentials ::= SEQUENCE {
#         credType    [0] INTEGER,
#         credentials [1] OCTET STRING
# }

class TSCredentials(Sequence):
	_fields = [
		('credType', Integer, {'explicit': 0}),
		('credentials', OctetString, {'explicit': 1}),
]


# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/17773cc4-21e9-4a75-a0dd-72706b174fe5
# TSPasswordCreds ::= SEQUENCE {
#         domainName  [0] OCTET STRING,
#         userName    [1] OCTET STRING,
#         password    [2] OCTET STRING
# }

class TSPasswordCreds(Sequence):
	_fields = [
		('domainName', OctetString, {'explicit': 0}),
		('userName', OctetString, {'explicit': 1}),
		('password', OctetString, {'explicit': 2}),
]

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/34ee27b3-5791-43bb-9201-076054b58123
# TSCspDataDetail ::= SEQUENCE {
#         keySpec       [0] INTEGER,
#         cardName      [1] OCTET STRING OPTIONAL,
#         readerName    [2] OCTET STRING OPTIONAL,
#         containerName [3] OCTET STRING OPTIONAL,
#         cspName       [4] OCTET STRING OPTIONAL
# }

class TSCspDataDetail(Sequence):
	_fields = [
		('keySpec', Integer, {'explicit': 0}),
		('cardName', OctetString, {'explicit': 1,'optional': True}),
		('readerName', OctetString, {'explicit': 2,'optional': True}),
		('containerName', OctetString, {'explicit': 3,'optional': True}),
		('cspName', OctetString, {'explicit': 4,'optional': True }),
]


# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/4251d165-cf01-4513-a5d8-39ee4a98b7a4
# TSSmartCardCreds ::= SEQUENCE {
#         pin         [0] OCTET STRING,
#         cspData     [1] TSCspDataDetail,
#         userHint    [2] OCTET STRING OPTIONAL,
#         domainHint  [3] OCTET STRING OPTIONAL
# }
#

class TSSmartCardCreds(Sequence):
	_fields = [
		('pin', OctetString, {'explicit': 0}),
		('cspData', TSCspDataDetail, {'explicit': 1}),
		('userHint', OctetString, {'explicit': 2, 'optional': True}),
		('domainHint', OctetString, {'explicit': 3, 'optional': True}),
]

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/173eee44-1a2c-463f-b909-c15db01e68d7
# TSRemoteGuardPackageCred ::= SEQUENCE{
#     packageName [0] OCTET STRING,
#     credBuffer  [1] OCTET STRING,
# }

class TSRemoteGuardPackageCred(Sequence):
	_fields = [
		('packageName', OctetString, {'explicit': 0}),
		('credBuffer', OctetString, {'explicit': 1}),
]


# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cssp/7ef8229c-44ea-4c1b-867f-00369b882b38
# TSRemoteGuardCreds ::= SEQUENCE{
#     logonCred           [0] TSRemoteGuardPackageCred,
#     supplementalCreds   [1] SEQUENCE OF TSRemoteGuardPackageCred OPTIONAL,
# }


class TSRemoteGuardPackageCreds(SequenceOf):
	_child_spec = TSRemoteGuardPackageCred

class TSRemoteGuardCreds(Sequence):
	_fields = [
		('logonCred', TSRemoteGuardPackageCred, {'explicit': 0}),
		('supplementalCreds', TSRemoteGuardPackageCreds, {'explicit': 1, 'optional':True}),
]
