import enum
import io
from aardwolf.protocol.T128.share import TS_SHAREDATAHEADER

class ERRINFO(enum.Enum):
	UNK = 'blabla' # error not found
	NONE = 0x00000000 # No error has occurred. This code SHOULD be ignored.
	RPC_INITIATED_DISCONNECT = 0x00000001 # The disconnection was initiated by an administrative tool on the server in another session.
	RPC_INITIATED_LOGOFF = 0x00000002 # The disconnection was due to a forced logoff initiated by an administrative tool on the server in another session.
	IDLE_TIMEOUT = 0x00000003 # The idle session limit timer on the server has elapsed.
	LOGON_TIMEOUT = 0x00000004 # The active session limit timer on the server has elapsed.
	DISCONNECTED_BY_OTHERCONNECTION = 0x00000005 # Another user connected to the server, forcing the disconnection of the current connection.
	OUT_OF_MEMORY = 0x00000006 # The server ran out of available memory resources. 
	SERVER_DENIED_CONNECTION = 0x00000007 # The server denied the connection.
	SERVER_INSUFFICIENT_PRIVILEGES = 0x00000009 # The user cannot connect to the server due to insufficient access privileges.
	SERVER_FRESH_CREDENTIALS_REQUIRED = 0x0000000A # The server does not accept saved user credentials and requires that the user enter their credentials for each connection.
	RPC_INITIATED_DISCONNECT_BYUSER = 0x0000000B # The disconnection was initiated by an administrative tool on the server running in the user’s session.
	LOGOFF_BY_USER = 0x0000000C # The disconnection was initiated by the user logging off his or her session on the server.
	CLOSE_STACK_ON_DRIVER_NOT_READY = 0x0000000F # The display driver in the remote session did not report any status within the time allotted for startup.
	SERVER_DWM_CRASH = 0x00000010 # The DWM process running in the remote session terminated unexpectedly.
	CLOSE_STACK_ON_DRIVER_FAILURE = 0x00000011 # The display driver in the remote session was unable to complete all the tasks required for startup.
	CLOSE_STACK_ON_DRIVER_IFACE_FAILURE = 0x00000012 # The display driver in the remote session started up successfully, but due to internal failures was not usable by the remoting stack.
	SERVER_WINLOGON_CRASH = 0x00000017 # The Winlogon process running in the remote session terminated unexpectedly.
	SERVER_CSRSS_CRASH = 0x00000018 # The CSRSS process running in the remote session terminated unexpectedly.
	SERVER_SHUTDOWN = 0x00000019 # The remote server is busy shutting down.
	SERVER_REBOOT = 0x0000001A # The remote server is busy rebooting.
	LICENSE_INTERNAL = 0x00000100 # An internal error has occurred in the Terminal Services licensing component.
	LICENSE_NO_LICENSE_SERVER = 0x00000101 # A Remote Desktop License Server ([MS-RDPELE] section 1.1) could not be found to provide a license.
	LICENSE_NO_LICENSE = 0x00000102 # There are no Client Access Licenses ([MS-RDPELE] section 1.1) available for the target remote computer.
	LICENSE_BAD_CLIENT_MSG = 0x00000103 # The remote computer received an invalid licensing message from the client.
	LICENSE_HWID_DOESNT_MATCH_LICENSE = 0x00000104 # The Client Access License ([MS-RDPELE] section 1.1) stored by the client has been modified.
	LICENSE_BAD_CLIENT_LICENSE = 0x00000105 # The Client Access License ([MS-RDPELE] section 1.1) stored by the client is in an invalid format
	LICENSE_CANT_FINISH_PROTOCOL = 0x00000106 # Network problems have caused the licensing protocol ([MS-RDPELE] section 1.3.3) to be terminated.
	LICENSE_CLIENT_ENDED_PROTOCOL = 0x00000107 #The client prematurely ended the licensing protocol ([MS-RDPELE] section 1.3.3).
	LICENSE_BAD_CLIENT_ENCRYPTION = 0x00000108 #A licensing message ([MS-RDPELE] sections 2.2 and 5.1) was incorrectly encrypted.
	LICENSE_CANT_UPGRADE_LICENSE = 0x00000109 # The Client Access License ([MS-RDPELE] section 1.1) stored by the client could not be upgraded or renewed.
	LICENSE_NO_REMOTE_CONNECTIONS = 0x0000010A # The remote computer is not licensed to accept remote connections.
	CB_DESTINATION_NOT_FOUND = 0x00000400 #The target endpoint could not be found.
	CB_LOADING_DESTINATION = 0x00000402 #The target endpoint to which the client is being redirected is disconnecting from the Connection Broker.
	CB_REDIRECTING_TO_DESTINATION = 0x00000404 #An error occurred while the connection was being redirected to the target endpoint.
	CB_SESSION_ONLINE_VM_WAKE = 0x00000405 #An error occurred while the target endpoint (a virtual machine) was being awakened.
	CB_SESSION_ONLINE_VM_BOOT = 0x00000406 #An error occurred while the target endpoint (a virtual machine) was being started.
	CB_SESSION_ONLINE_VM_NO_DNS = 0x00000407 #The IP address of the target endpoint (a virtual machine) cannot be determined.
	CB_DESTINATION_POOL_NOT_FREE = 0x00000408 #There are no available endpoints in the pool managed by the Connection Broker.
	CB_CONNECTION_CANCELLED = 0x00000409 #Processing of the connection has been canceled.
	CB_CONNECTION_ERROR_INVALID_SETTINGS = 0x00000410 #The settings contained in the routingToken field of the X.224 Connection Request PDU (section 2.2.1.1) cannot be validated.
	CB_SESSION_ONLINE_VM_BOOT_TIMEOUT = 0x00000411 #A time-out occurred while the target endpoint (a virtual machine) was being started.
	CB_SESSION_ONLINE_VM_SESSMON_FAILED = 0x00000412 #A session monitoring error occurred while the target endpoint (a virtual machine) was being started.
	UNKNOWNPDUTYPE2 = 0x000010C9 #Unknown pduType2 field in a received Share Data Header (section 2.2.8.1.1.1.2). 
	UNKNOWNPDUTYPE = 0x000010CA #Unknown pduType field in a received Share Control Header (section 2.2.8.1.1.1.1).
	DATAPDUSEQUENCE = 0x000010CB #An out-of-sequence Slow-Path Data PDU (section 2.2.8.1.1.1.1) has been received.
	CONTROLPDUSEQUENCE = 0x000010CD #An out-of-sequence Demand Active PDU (section 2.2.1.13.1), Confirm Active PDU (section 2.2.1.13.2), Deactivate All PDU (section 2.2.3.1) or Enhanced Security Server Redirection PDU (section 2.2.13.3.1) has been received.
	INVALIDCONTROLPDUACTION = 0x000010CE #A Control PDU (sections 2.2.1.15 and 2.2.1.16) has been received with an invalid action field.
	INVALIDINPUTPDUTYPE = 0x000010CF #One of two possible errors #    A Slow-Path Input Event (section 2.2.8.1.1.3.1.1) has been received with an invalid messageType field. #A Fast-Path Input Event (section 2.2.8.1.2.2) has been received with an invalid eventCode field.
	INVALIDINPUTPDUMOUSE = 0x000010D0 #One of two possible errors: #    A Slow-Path Mouse Event (section 2.2.8.1.1.3.1.1.3) or Extended Mouse Event (section 2.2.8.1.1.3.1.1.4) has been received with an invalid pointerFlags field #A Fast-Path Mouse Event (section 2.2.8.1.2.2.3) or Fast-Path Extended Mouse Event (section 2.2.8.1.2.2.4) has been received with an invalid pointerFlags field.
	INVALIDREFRESHRECTPDU = 0x000010D1 #An invalid Refresh Rect PDU (section 2.2.11.2) has been received.
	CREATEUSERDATAFAILED = 0x000010D2 #The server failed to construct the GCC Conference Create Response user data (section 2.2.1.4).
	CONNECTFAILED = 0x000010D3 #Processing during the Channel Connection phase of the RDP Connection Sequence (see section 1.3.1.1 for an overview of the RDP Connection Sequence phases) has failed.
	CONFIRMACTIVEWRONGSHAREID = 0x000010D4 #A Confirm Active PDU (section 2.2.1.13.2) was received from the client with an invalid shareID field.
	CONFIRMACTIVEWRONGORIGINATOR = 0x000010D5 #A Confirm Active PDU (section 2.2.1.13.2) was received from the client with an invalid originatorID field.
	PERSISTENTKEYPDUBADLENGTH = 0x000010DA #There is not enough data to process a Persistent Key List PDU (section 2.2.1.17).
	PERSISTENTKEYPDUILLEGALFIRST = 0x000010DB #A Persistent Key List PDU (section 2.2.1.17) marked as PERSIST_PDU_FIRST (0x01) was received after the reception of a prior Persistent Key List PDU also marked as PERSIST_PDU_FIRST.
	PERSISTENTKEYPDUTOOMANYTOTALKEYS = 0x000010DC #A Persistent Key List PDU (section 2.2.1.17) was received which specified a total number of bitmap cache entries larger than 262144.
	PERSISTENTKEYPDUTOOMANYCACHEKEYS = 0x000010DD #A Persistent Key List PDU (section 2.2.1.17) was received which specified an invalid total number of keys for a bitmap cache (the number of entries that can be stored within each bitmap cache is specified in the Revision 1 or 2 Bitmap Cache Capability Set (section 2.2.7.1.4) that is sent from client to server).
	INPUTPDUBADLENGTH = 0x000010DE #There is not enough data to process Input Event PDU Data (section 2.2.8.1.1.3.1) or a Fast-Path Input Event PDU (section 2.2.8.1.2).
	BITMAPCACHEERRORPDUBADLENGTH = 0x000010DF #There is not enough data to process the shareDataHeader, NumInfoBlocks, Pad1, and Pad2 fields of the Bitmap Cache Error PDU Data ([MS-RDPEGDI] section 2.2.2.3.1.1).
	SECURITYDATATOOSHORT = 0x000010E0 #One of two possible errors: #    The dataSignature field of the Fast-Path Input Event PDU (section 2.2.8.1.2) does not contain enough data #The fipsInformation and dataSignature fields of the Fast-Path Input Event PDU (section 2.2.8.1.2) do not contain enough data.
	VCHANNELDATATOOSHORT = 0x000010E1 #One of two possible errors #    There is not enough data in the Client Network Data (section 2.2.1.3.4) to read the virtual channel configuration data. #There is not enough data to read a complete Channel PDU Header (section 2.2.6.1.1).
	SHAREDATATOOSHORT = 0x000010E2 #One of four possible errors: #There is not enough data to process Control PDU Data (section 2.2.1.15.1). #There is not enough data to read a complete Share Control Header (section 2.2.8.1.1.1.1). #There is not enough data to read a complete Share Data Header (section 2.2.8.1.1.1.2) of a Slow-Path Data PDU (section 2.2.8.1.1.1.1). #There is not enough data to process Font List PDU Data (section 2.2.1.18.1).
	BADSUPRESSOUTPUTPDU = 0x000010E3 #One of two possible errors: #    There is not enough data to process Suppress Output PDU Data (section 2.2.11.3.1).#    The allowDisplayUpdates field of the Suppress Output PDU Data (section 2.2.11.3.1) is invalid.
	CONFIRMACTIVEPDUTOOSHORT = 0x000010E5 #One of two possible errors: #    There is not enough data to read the shareControlHeader, shareID, originatorID, lengthSourceDescriptor, and lengthCombinedCapabilities fields of the Confirm Active PDU Data (section 2.2.1.13.2.1).# There is not enough data to read the sourceDescriptor, numberCapabilities, pad2Octets, and capabilitySets fields of the Confirm Active PDU Data (section 2.2.1.13.2.1).
	CAPABILITYSETTOOSMALL = 0x000010E7 #There is not enough data to read the capabilitySetType and the lengthCapability fields in a received Capability Set (section 2.2.1.13.1.1.1).
	CAPABILITYSETTOOLARGE = 0x000010E8 #A Capability Set (section 2.2.1.13.1.1.1) has been received with a lengthCapability field that contains a value greater than the total length of the data received.
	NOCURSORCACHE = 0x000010E9 #One of two possible errors: #    Both the colorPointerCacheSize and pointerCacheSize fields in the Pointer Capability Set (section 2.2.7.1.5) are set to zero. #The pointerCacheSize field in the Pointer Capability Set (section 2.2.7.1.5) is not present, and the colorPointerCacheSize field is set to zero.
	BADCAPABILITIES = 0x000010EA #The capabilities received from the client in the Confirm Active PDU (section 2.2.1.13.2) were not accepted by the server.
	VIRTUALCHANNELDECOMPRESSIONERR = 0x000010EC #An error occurred while using the bulk compressor (section 3.1.8 and [MS-RDPEGDI] section 3.1.8) to decompress a Virtual Channel PDU (section 2.2.6.1)
	INVALIDVCCOMPRESSIONTYPE = 0x000010ED #An invalid bulk compression package was specified in the flags field of the Channel PDU Header (section 2.2.6.1.1).
	INVALIDCHANNELID = 0x000010EF #An invalid MCS channel ID was specified in the mcsPdu field of the Virtual Channel PDU (section 2.2.6.1).
	VCHANNELSTOOMANY = 0x000010F0 #The client requested more than the maximum allowed 31 static virtual channels in the Client Network Data (section 2.2.1.3.4).
	REMOTEAPPSNOTENABLED = 0x000010F3 #The INFO_RAIL flag (0x00008000) MUST be set in the flags field of the Info Packet (section 2.2.1.11.1.1) as the session on the remote server can only host remote applications.
	CACHECAPNOTSET = 0x000010F4 #The client sent a Persistent Key List PDU (section 2.2.1.17) without including the prerequisite Revision 2 Bitmap Cache Capability Set (section 2.2.7.1.4.2) in the Confirm Active PDU (section 2.2.1.13.2).
	BITMAPCACHEERRORPDUBADLENGTH2 = 0x000010F5 #The NumInfoBlocks field in the Bitmap Cache Error PDU Data is inconsistent with the amount of data in the Info field ([MS-RDPEGDI] section 2.2.2.3.1.1).
	OFFSCRCACHEERRORPDUBADLENGTH = 0x000010F6 #There is not enough data to process an Offscreen Bitmap Cache Error PDU ([MS-RDPEGDI] section 2.2.2.3.2).
	DNGCACHEERRORPDUBADLENGTH = 0x000010F7 #There is not enough data to process a DrawNineGrid Cache Error PDU ([MS-RDPEGDI] section 2.2.2.3.3).
	GDIPLUSPDUBADLENGTH = 0x000010F8 #There is not enough data to process a GDI+ Error PDU ([MS-RDPEGDI] section 2.2.2.3.4).
	SECURITYDATATOOSHORT2 = 0x00001111 #There is not enough data to read a Basic Security Header (section 2.2.8.1.1.2.1).
	SECURITYDATATOOSHORT3 = 0x00001112 #There is not enough data to read a Non-FIPS Security Header (section 2.2.8.1.1.2.2) or FIPS Security Header (section 2.2.8.1.1.2.3).
	SECURITYDATATOOSHORT4 = 0x00001113 #There is not enough data to read the basicSecurityHeader and length fields of the Security Exchange PDU Data (section 2.2.1.10.1).
	SECURITYDATATOOSHORT5 = 0x00001114 #There is not enough data to read the CodePage, flags, cbDomain, cbUserName, cbPassword, cbAlternateShell, cbWorkingDir, Domain, UserName, Password, AlternateShell, and WorkingDir fields in the Info Packet (section 2.2.1.11.1.1).
	SECURITYDATATOOSHORT6 = 0x00001115 #There is not enough data to read the CodePage, flags, cbDomain, cbUserName, cbPassword, cbAlternateShell, and cbWorkingDir fields in the Info Packet (section 2.2.1.11.1.1).
	SECURITYDATATOOSHORT7 = 0x00001116 #There is not enough data to read the clientAddressFamily and cbClientAddress fields in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT8 = 0x00001117 #There is not enough data to read the clientAddress field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT9 = 0x00001118 #There is not enough data to read the cbClientDir field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT10 = 0x00001119 #There is not enough data to read the clientDir field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT11 = 0x0000111A #There is not enough data to read the clientTimeZone field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT12 = 0x0000111B #There is not enough data to read the clientSessionId field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT13 = 0x0000111C #There is not enough data to read the performanceFlags field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT14 = 0x0000111D #There is not enough data to read the cbAutoReconnectCookie field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT15 = 0x0000111E #There is not enough data to read the autoReconnectCookie field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT16 = 0x0000111F #The cbAutoReconnectCookie field in the Extended Info Packet (section 2.2.1.11.1.1.1) contains a value which is larger than the maximum allowed length of 128 bytes.
	SECURITYDATATOOSHORT17 = 0x00001120 #There is not enough data to read the clientAddressFamily and cbClientAddress fields in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT18 = 0x00001121 #There is not enough data to read the clientAddress field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT19 = 0x00001122 #There is not enough data to read the cbClientDir field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT20 = 0x00001123 #There is not enough data to read the clientDir field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT21 = 0x00001124 #There is not enough data to read the clientTimeZone field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT22 = 0x00001125 #There is not enough data to read the clientSessionId field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	SECURITYDATATOOSHORT23 = 0x00001126 #There is not enough data to read the Client Info PDU Data (section 2.2.1.11.1).
	BADMONITORDATA = 0x00001129 #The number of TS_MONITOR_DEF (section 2.2.1.3.6.1) structures present in the monitorDefArray field of the Client Monitor Data (section 2.2.1.3.6) is less than the value specified in monitorCount field.
	VCDECOMPRESSEDREASSEMBLEFAILED = 0x0000112A #The server-side decompression buffer is invalid, or the size of the decompressed VC data exceeds the chunking size specified in the Virtual Channel Capability Set (section 2.2.7.1.10).
	VCDATATOOLONG = 0x0000112B #The size of a received Virtual Channel PDU (section 2.2.6.1) exceeds the chunking size specified in the Virtual Channel Capability Set (section 2.2.7.1.10).
	BAD_FRAME_ACK_DATA = 0x0000112C #There is not enough data to read a TS_FRAME_ACKNOWLEDGE_PDU ([MS-RDPRFX] section 2.2.3.1).
	GRAPHICSMODENOTSUPPORTED = 0x0000112D #The graphics mode requested by the client is not supported by the server.
	GRAPHICSSUBSYSTEMRESETFAILED = 0x0000112E #The server-side graphics subsystem failed to reset.
	GRAPHICSSUBSYSTEMFAILED = 0x0000112F #The server-side graphics subsystem is in an error state and unable to continue graphics encoding.
	TIMEZONEKEYNAMELENGTHTOOSHORT = 0x00001130 #There is not enough data to read the cbDynamicDSTTimeZoneKeyName field in the Extended Info Packet (section 2.2.1.11.1.1.1).
	TIMEZONEKEYNAMELENGTHTOOLONG = 0x00001131 #The length reported in the cbDynamicDSTTimeZoneKeyName field of the Extended Info Packet (section 2.2.1.11.1.1.1) is too long.
	DYNAMICDSTDISABLEDFIELDMISSING = 0x00001132 #The dynamicDaylightTimeDisabled field is not present in the Extended Info Packet (section 2.2.1.11.1.1.1).
	VCDECODINGERROR = 0x00001133 #An error occurred when processing dynamic virtual channel data ([MS-RDPEDYC] section 3.3.5).
	VIRTUALDESKTOPTOOLARGE = 0x00001134 #The width or height of the virtual desktop defined by the monitor layout in the Client Monitor Data (section 2.2.1.3.6) is larger than the maximum allowed value of 32,766.
	MONITORGEOMETRYVALIDATIONFAILED = 0x00001135 #The monitor geometry defined by the Client Monitor Data (section 2.2.1.3.6) is invalid.
	INVALIDMONITORCOUNT = 0x00001136 #The monitorCount field in the Client Monitor Data (section 2.2.1.3.6) is too large.
	UPDATESESSIONKEYFAILED = 0x00001191 #An attempt to update the session keys while using Standard RDP Security mechanisms (section 5.3.7) failed.
	DECRYPTFAILED = 0x00001192 #One of two possible error conditions: Decryption using Standard RDP Security mechanisms (section 5.3.6) failed. #Session key creation using Standard RDP Security mechanisms (section 5.3.5) failed.
	ENCRYPTFAILED = 0x00001193 #Encryption using Standard RDP Security mechanisms (section 5.3.6) failed.
	ENCPKGMISMATCH = 0x00001194 #Failed to find a usable Encryption Method (section 5.3.2) in the encryptionMethods field of the Client Security Data (section 2.2.1.4.3).
	DECRYPTFAILED2 = 0x00001195 #Unencrypted data was encountered in a protocol stream which is meant to be encrypted with Standard RDP Security mechanisms (section 5.3.6).

class TS_SET_ERROR_INFO_PDU:
	def __init__(self):
		self.shareDataHeader:TS_SHAREDATAHEADER = None
		self.errorInfoRaw:int = None
		self.errorInfo:ERRINFO = None

	def to_bytes(self):
		t = self.shareID.to_bytes(4, byteorder='little', signed = False)
		t += len(self.sourceDescriptor).to_bytes(2, byteorder='little', signed = False)
		t += (len(capdata) + 2 + 2).to_bytes(2, byteorder='little', signed = False)
		t += self.sourceDescriptor
		t += len(self.capabilitySets).to_bytes(2, byteorder='little', signed = False)
		t += self.pad2Octets.to_bytes(2, byteorder='little', signed = False)
		t += capdata
		t += self.sessionId.to_bytes(4, byteorder='little', signed = False)
		#self.shareControlHeader.totalLength = 6 + len(t)
		#t = self.shareControlHeader.to_bytes() + t
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_SET_ERROR_INFO_PDU.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SET_ERROR_INFO_PDU()
		msg.shareDataHeader = TS_SHAREDATAHEADER.from_buffer(buff)
		msg.errorInfoRaw = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		try:
			msg.errorInfo = ERRINFO(msg.errorInfoRaw)
		except:
			msg.errorInfo = ERRINFO.UNK
		return msg

	def __repr__(self):
		t = '==== TS_SET_ERROR_INFO_PDU ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t