import enum
import io
from aardwolf.protocol.T125.extendedinfopacket import TS_EXTENDED_INFO_PACKET

class INFO_FLAG(enum.IntFlag):
	MOUSE = 0x00000001 #Indicates that the client machine has a mouse attached.
	DISABLECTRLALTDEL = 0x00000002 #Indicates that the CTRL+ALT+DEL (or the equivalent) secure access keyboard sequence is not required at the logon prompt
	AUTOLOGON = 0x00000008 #The client requests auto logon using the included user name, password and domain.
	UNICODE = 0x00000010 #Indicates that the character set for strings in the Info Packet and Extended Info Packet (section 2.2.1.11.1.1.1) is Unicode. If this flag is absent, then the ANSI character set that is specified by the ANSI code page descriptor in the CodePage field is used for strings in the Info Packet and Extended Info Packet.
	MAXIMIZESHELL = 0x00000020 #Indicates that the alternate shell (specified in the AlternateShell field of the Info Packet structure) MUST be started in a maximized state.
	LOGONNOTIFY = 0x00000040 #Indicates that the client wants to be informed of the user name and domain used to log on to the server, as well as the ID of the session to which the user connected. The Save Session Info PDU (section 2.2.10.1) is sent from the server to notify the client of this information using a Logon Info Version 1 (section 2.2.10.1.1.1) or Logon Info Version 2 (section 2.2.10.1.1.2) structure.
	COMPRESSION = 0x00000080 #Indicates that the CompressionTypeMask is valid and contains the highest compression package type supported by the client.
	CompressionTypeMask = 0x00001E00 #Indicates the highest compression package type supported. See the discussion which follows this table for more information.
	ENABLEWINDOWSKEY = 0x00000100 #Indicates that the client uses the Windows key on Windows-compatible keyboards.
	REMOTECONSOLEAUDIO = 0x00002000 #Requests that audio played in a session hosted on a remote server be played on the server.
	FORCE_ENCRYPTED_CS_PDU = 0x00004000 #Indicates that all client-to-server traffic is encrypted when encryption is in force. Setting this flag prevents the server from processing unencrypted packets in man-in-the-middle attack scenarios. This flag is not understood by RDP 4.0, 5.0, and 5.1 servers.
	RAIL = 0x00008000 #Indicates that the remote connection being established is for the purpose of launching remote programs using the protocol defined in [MS-RDPERP] sections 2 and 3. This flag is not understood by RDP 4.0, 5.0, 5.1, and 5.2 servers.
	LOGONERRORS = 0x00010000 #Indicates a request for logon error notifications using the Save Session Info PDU. This flag is not understood by RDP 4.0, 5.0, 5.1, and 5.2 servers.
	MOUSE_HAS_WHEEL = 0x00020000 #Indicates that the mouse which is connected to the client machine has a scroll wheel. This flag is not understood by RDP 4.0, 5.0, 5.1, and 5.2 servers.
	PASSWORD_IS_SC_PIN = 0x00040000 #Indicates that the Password field in the Info Packet contains a smart card personal identification number (PIN). This flag is not understood by RDP 4.0, 5.0, 5.1, and 5.2 servers.
	NOAUDIOPLAYBACK = 0x00080000 #Indicates that audio redirection (using the protocol defined in [MS-RDPEA] sections 2 and 3) MUST NOT take place. This flag is not understood by RDP 4.0, 5.0, 5.1, and 5.2 servers. If the INFO_NOAUDIOPLAYBACK flag is not set, then audio redirection SHOULD take place if the INFO_REMOTECONSOLEAUDIO (0x00002000) flag is also not set.
	USING_SAVED_CREDS = 0x00100000 #Any user credentials sent on the wire during the RDP Connection Sequence (sections 1.3.1.1 and 1.3.1.2) have been retrieved from a credential store and were not obtained directly from the user. This flag is not understood by RDP 4.0, 5.0, 5.1, 5.2, and 6.0 servers.
	AUDIOCAPTURE = 0x00200000 #Indicates that the redirection of client-side audio input to a session hosted on a remote server is supported using the protocol defined in [MS-RDPEAI] sections 2 and 3. This flag is not understood by RDP 4.0, 5.0, 5.1, 5.2, 6.0, and 6.1 servers.
	VIDEO_DISABLE = 0x00400000 #Indicates that video redirection or playback (using the protocol defined in [MS-RDPEV] sections 2 and 3) MUST NOT take place. This flag is not understood by RDP 4.0, 5.0, 5.1, 5.2, 6.0, and 6.1 servers.
	RESERVED1 = 0x00800000 #An unused flag that is reserved for future use. This flag MUST NOT be set.
	RESERVED2 = 0x01000000 #An unused flag that is reserved for future use. This flag MUST NOT be set.
	HIDEF_RAIL_SUPPORTED = 0x02000000 #Indicates that the client supports Enhanced RemoteApp ([MS-RDPERP] section 1.3.3). The INFO_HIDEF_RAIL_SUPPORTED flag MUST be ignored if the INFO_RAIL (0x00008000) flag is not specified. Furthermore, a client that specifies the INFO_HIDEF_RAIL_SUPPORTED flag MUST send the Remote Programs Capability Set ([MS-RDPERP] section 2.2.1.1.1) to the server. The INFO_HIDEF_RAIL_SUPPORTED flag is not understood by RDP 4.0, 5.0, 5.1, 5.2, 6.0, 6.1, 7.0, 7.1, and 8.0 servers

class CompressionTypeFlag:
	TYPE_8K = 0x0 #RDP 4.0 bulk compression (section 3.1.8.4.1).
	TYPE_64K = 0x1 #RDP 5.0 bulk compression (section 3.1.8.4.2).
	TYPE_RDP6 = 0x2 #RDP 6.0 bulk compression ([MS-RDPEGDI] section 3.1.8.1).
	TYPE_RDP61 = 0x3

# https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/732394f5-e2b5-4ac5-8a0a-35345386b0d1
class TS_INFO_PACKET:
	def __init__(self):
		self.CodePage:int = None
		self.flags:INFO_FLAG = None
		self.cbDomain:int = None
		self.cbUserName:int = None
		self.cbPassword:int = None
		self.cbAlternateShell:int = None
		self.cbWorkingDir:int = None
		self.Domain:str = None
		self.UserName:str = None
		self.Password:str = None
		self.AlternateShell:str = None
		self.WorkingDir:str = None
		self.extrainfo:TS_EXTENDED_INFO_PACKET = None

	def to_bytes(self):
		encoding= 'ascii'
		if INFO_FLAG.UNICODE in self.flags:
			encoding = 'utf-16-le'
		domain = (self.Domain+'\x00').encode(encoding)
		username = (self.UserName+'\x00').encode(encoding)
		password = (self.Password+'\x00').encode(encoding)
		altshell = (self.AlternateShell+'\x00').encode(encoding)
		wd = (self.WorkingDir+'\x00').encode(encoding)
		
			
		t = self.CodePage.to_bytes(4, byteorder='little', signed = False)
		t += self.flags.to_bytes(4, byteorder='little', signed = False)
		
		t += (0 if len(self.Domain) == 0 else len(domain)-2).to_bytes(2, byteorder='little', signed = False)
		t += (0 if len(self.UserName) == 0 else len(username)-2).to_bytes(2, byteorder='little', signed = False)
		t += (0 if len(self.Password) == 0 else len(password)-2).to_bytes(2, byteorder='little', signed = False)
		t += (0 if len(self.AlternateShell) == 0 else len(altshell)-2).to_bytes(2, byteorder='little', signed = False)
		t += (0 if len(self.WorkingDir) == 0 else len(wd)-2).to_bytes(2, byteorder='little', signed = False)
		t += domain
		t += username
		t += password
		t += altshell
		t += wd
		
		if self.extrainfo is not None:
			t += self.extrainfo.to_bytes()

		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_INFO_PACKET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_INFO_PACKET()
		msg.CodePage = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.flags = INFO_FLAG(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		# NOTE: the cb.. fields contain the character count NOT the bytes count!!!! excluding the null terminator
		# also the character count depend on the UNICODE FLAG
		msg.cbDomain = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.cbUserName = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.cbPassword = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.cbAlternateShell = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.cbWorkingDir = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		encoding= 'ascii'
		if INFO_FLAG.UNICODE in msg.flags:
			encoding = 'utf-16-le'
		msg.Domain = buff.read(msg.cbDomain + 2).decode(encoding).replace('\x00', '')
		msg.UserName = buff.read(msg.cbUserName + 2).decode(encoding).replace('\x00', '')
		msg.Password = buff.read(msg.cbPassword + 2).decode(encoding).replace('\x00', '')
		msg.AlternateShell = buff.read(msg.cbAlternateShell + 2).decode(encoding).replace('\x00', '')
		msg.WorkingDir = buff.read(msg.cbWorkingDir+2).decode(encoding).replace('\x00', '')
		print(msg)
		print(buff.read(20))
		buff.seek(-20,1)
		msg.extrainfo = TS_EXTENDED_INFO_PACKET.from_buffer(buff)
		return msg

	def __repr__(self):
		t = '==== TS_INFO_PACKET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t