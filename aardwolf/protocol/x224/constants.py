import enum

# https://github.com/serisman/FreeRDP/blob/master/include/freerdp/constants/pdu.h

class TPDU_TYPE(enum.Enum):
	CONNECTION_REQUEST = 0xE
	CONNECTION_CONFIRM = 0xD
	DISCONNECT_REQUEST = 0x8
	DATA = 0xF
	ERROR = 0x7

class NEGOTIATIONType(enum.Enum):
	NEG_REQ = 0x1
	NEG_RSP = 0x2
	NEG_FAILURE = 0x3

class NEG_FLAGS(enum.IntFlag):
	RESTRICTED_ADMIN_MODE_REQUIRED = 0x01 #Indicates that the client requires credential-less logon over CredSSP (also known as "restricted admin mode"). If the server supports this mode then it is acceptable for the client to send empty credentials in the TSPasswordCreds structure defined in [MS-CSSP] section 2.2.1.2.1.<2>
	REDIRECTED_AUTHENTICATION_MODE_REQUIRED = 0x02 #Indicates that the client requires credential-less logon over CredSSP with redirected authentication over CredSSP (also known as "Remote Credential Guard"). If the server supports this mode, the client can send a redirected logon buffer in the TSRemoteGuardCreds structure defined in [MS-CSSP] section 2.2.1.2.3.
	CORRELATION_INFO_PRESENT = 0x08 #The optional rdpCorrelationInfo field of the 224 Connection Request PDU (section 2.2.1.1) is present.

class RESP_FLAGS(enum.IntFlag):
	EXTENDED_CLIENT_DATA_SUPPORTED = 0x01 #The server supports Extended Client Data Blocks in the GCC Conference Create Request user data (section 2.2.1.3).
	DYNVC_GFX_PROTOCOL_SUPPORTED = 0x02 #The server supports the Graphics Pipeline Extension Protocol described in [MS-RDPEGFX] sections 1, 2, and 3.
	NEGRSP_FLAG_RESERVED = 0x04 #An unused flag that is reserved for future use. This flag SHOULD be ignored by the client.
	RESTRICTED_ADMIN_MODE_SUPPORTED = 0x08 #Indicates that the server supports credential-less logon over CredSSP (also known as "restricted admin mode") and it is acceptable for the client to send empty credentials in the TSPasswordCreds structure defined in [MS-CSSP] section 2.2.1.2.1.<3>
	REDIRECTED_AUTHENTICATION_MODE_SUPPORTED = 0x10 #Indicates that the server supports credential-less logon over CredSSP with credential redirection (also known as "Remote Credential Guard"). The client can send a redirected logon buffer in the TSRemoteGuardCreds structure defined in [MS-CSSP] section 2.2.1.2.3.

class SUPP_PROTOCOLS(enum.IntFlag):
	RDP = 0x00000000
	SSL = 0x00000001
	HYBRID = 0x00000002
	RDSTLS = 0x00000004
	HYBRID_EX = 0x00000008

class FAIL_CODE(enum.Enum):
	SSL_REQUIRED_BY_SERVER = 0x00000001 #The server requires that the client support Enhanced RDP Security (section 5.4) with either TLS 1.0, 1.1 or 1.2 (section 5.4.5.1) or CredSSP (section 5.4.5.2). If only CredSSP was requested then the server only supports TLS.
	SSL_NOT_ALLOWED_BY_SERVER = 0x00000002 #The server is configured to only use Standard RDP Security mechanisms (section 5.3) and does not support any External Security Protocols (section 5.4.5).
	SSL_CERT_NOT_ON_SERVER = 0x00000003 #The server does not possess a valid authentication certificate and cannot initialize the External Security Protocol Provider (section 5.4.5).
	INCONSISTENT_FLAGS = 0x00000004 #The list of requested security protocols is not consistent with the current security protocol in effect. This error is only possible when the Direct Approach (sections 5.4.2.2 and 1.3.1.2) is used and an External Security Protocol (section 5.4.5) is already being used.
	HYBRID_REQUIRED_BY_SERVER = 0x00000005 #The server requires that the client support Enhanced RDP Security (section 5.4) with CredSSP (section 5.4.5.2).
	SSL_WITH_USER_AUTH_REQUIRED_BY_SERVER = 0x00000006 #The server requires that the client support Enhanced RDP Security (section 5.4) with TLS 1.0, 1.1 or 1.2 (section 5.4.5.1) and certificate-based client authentication.<4>

class ERRORINFO(enum.Enum):
	# Protocol-independent codes: */
	RPC_INITIATED_DISCONNECT = 0x0001
	RPC_INITIATED_LOGOFF = 0x0002
	IDLE_TIMEOUT = 0x0003
	LOGON_TIMEOUT = 0x0004
	DISCONNECTED_BY_OTHERCONNECTION = 0x0005
	OUT_OF_MEMORY = 0x0006
	SERVER_DENIED_CONNECTION = 0x0007
	SERVER_INSUFFICIENT_PRIVILEGES = 0x0009
	SERVER_FRESH_CREDENTIALS_REQUIRED = 0x000A
	RPC_INITIATED_DISCONNECT_BYUSER = 0x000B
	# Protocol-independent licensing codes: */
	LICENSE_INTERNAL = 0x0100
	LICENSE_NO_LICENSE_SERVER = 0x0101
	LICENSE_NO_LICENSE = 0x0102
	LICENSE_BAD_CLIENT_MSG = 0x0103
	LICENSE_HWID_DOESNT_MATCH_LICENSE = 0x0104
	LICENSE_BAD_CLIENT_LICENSE = 0x0105
	LICENSE_CANT_FINISH_PROTOCOL = 0x0106
	LICENSE_CLIENT_ENDED_PROTOCOL = 0x0107
	LICENSE_BAD_CLIENT_ENCRYPTION = 0x0108
	LICENSE_CANT_UPGRADE_LICENSE = 0x0109
	LICENSE_NO_REMOTE_CONNECTIONS = 0x010A
	# RDP specific codes: */
	UNKNOWNPDUTYPE2 = 0x10C9
	UNKNOWNPDUTYPE = 0x10CA
	DATAPDUSEQUENCE = 0x10CB
	CONTROLPDUSEQUENCE = 0x10CD
	INVALIDCONTROLPDUACTION = 0x10CE
	INVALIDINPUTPDUTYPE = 0x10CF
	INVALIDINPUTPDUMOUSE = 0x10D0
	INVALIDREFRESHRECTPDU = 0x10D1
	CREATEUSERDATAFAILED = 0x10D2
	CONNECTFAILED = 0x10D3
	CONFIRMACTIVEWRONGSHAREID = 0x10D4
	CONFIRMACTIVEWRONGORIGINATOR = 0x10D5
	PERSISTENTKEYPDUBADLENGTH = 0x10DA
	PERSISTENTKEYPDUILLEGALFIRST = 0x10DB
	PERSISTENTKEYPDUTOOMANYTOTALKEYS = 0x10DC
	PERSISTENTKEYPDUTOOMANYCACHEKEYS = 0x10DD
	INPUTPDUBADLENGTH = 0x10DE
	BITMAPCACHEERRORPDUBADLENGTH = 0x10DF
	SECURITYDATATOOSHORT = 0x10E0
	VCHANNELDATATOOSHORT = 0x10E1
	SHAREDATATOOSHORT = 0x10E2
	BADSUPRESSOUTPUTPDU = 0x10E3
	CONFIRMACTIVEPDUTOOSHORT = 0x10E5
	CAPABILITYSETTOOSMALL = 0x10E7
	CAPABILITYSETTOOLARGE = 0x10E8
	NOCURSORCACHE = 0x10E9
	BADCAPABILITIES = 0x10EA
	VIRTUALCHANNELDECOMPRESSIONERR = 0x10EC
	INVALIDVCCOMPRESSIONTYPE = 0x10ED
	INVALIDCHANNELID = 0x10EF
	VCHANNELSTOOMANY = 0x10F0
	REMOTEAPPSNOTENABLED = 0x10F3
	CACHECAPNOTSET = 0x10F4
	BITMAPCACHEERRORPDUBADLENGTH2 = 0x10F5
	OFFSCRCACHEERRORPDUBADLENGTH = 0x10F6
	DNGCACHEERRORPDUBADLENGTH = 0x10F7
	GDIPLUSPDUBADLENGTH = 0x10F8
	SECURITYDATATOOSHORT2 = 0x1111
	SECURITYDATATOOSHORT3 = 0x1112
	SECURITYDATATOOSHORT4 = 0x1113
	SECURITYDATATOOSHORT5 = 0x1114
	SECURITYDATATOOSHORT6 = 0x1115
	SECURITYDATATOOSHORT7 = 0x1116
	SECURITYDATATOOSHORT8 = 0x1117
	SECURITYDATATOOSHORT9 = 0x1118
	SECURITYDATATOOSHORT10 = 0x1119
	SECURITYDATATOOSHORT11 = 0x111A
	SECURITYDATATOOSHORT12 = 0x111B
	SECURITYDATATOOSHORT13 = 0x111C
	SECURITYDATATOOSHORT14 = 0x111D
	SECURITYDATATOOSHORT15 = 0x111E
	SECURITYDATATOOSHORT16 = 0x111F
	SECURITYDATATOOSHORT17 = 0x1120
	SECURITYDATATOOSHORT18 = 0x1121
	SECURITYDATATOOSHORT19 = 0x1122
	SECURITYDATATOOSHORT20 = 0x1123
	SECURITYDATATOOSHORT21 = 0x1124
	SECURITYDATATOOSHORT22 = 0x1125
	SECURITYDATATOOSHORT23 = 0x1126
	BADMONITORDATA = 0x1129
	UPDATESESSIONKEYFAILED = 0x1191
	DECRYPTFAILED = 0x1192
	ENCRYPTFAILED = 0x1193
	ENCPKGMISMATCH = 0x1194
	DECRYPTFAILED2 = 0x1195

