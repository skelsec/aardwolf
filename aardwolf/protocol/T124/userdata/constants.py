import enum

class TS_UD_TYPE(enum.Enum):
	CS_CORE = 0xC001 #The data block that follows contains Client Core Data (section 2.2.1.3.2).
	CS_SECURITY = 0xC002 #The data block that follows contains Client Security Data (section 2.2.1.3.3).
	CS_NET = 0xC003 #The data block that follows contains Client Network Data (section 2.2.1.3.4).
	CS_CLUSTER = 0xC004 #The data block that follows contains Client Cluster Data (section 2.2.1.3.5).
	CS_MONITOR = 0xC005 #The data block that follows contains Client Monitor Data (section 2.2.1.3.6).
	CS_MCS_MSGCHANNEL = 0xC006 #The data block that follows contains Client Message Channel Data (section 2.2.1.3.7).
	CS_MONITOR_EX = 0xC008 #The data block that follows contains Client Monitor Extended Data (section 2.2.1.3.9).
	CS_MULTITRANSPORT = 0xC00A #The data block that follows contains Client Multitransport Channel Data (section 2.2.1.3.8).
	SC_CORE = 0x0C01 #The data block that follows contains Server Core Data (section 2.2.1.4.2).
	SC_SECURITY = 0x0C02 #The data block that follows contains Server Security Data (section 2.2.1.4.3).
	SC_NET = 0x0C03 #The data block that follows contains Server Network Data (section 2.2.1.4.4).
	SC_MCS_MSGCHANNEL = 0x0C04 #The data block that follows contains Server Message Channel Data (section 2.2.1.4.5).
	SC_MULTITRANSPORT = 0x0C08 #The data block that follows contains Server Multitransport Channel Data (section 2.2.1.4.6).

class COLOR_DEPTH(enum.Enum):
	COLOR_4BPP = 0xCA00 #4 bits-per-pixel (bpp)
	COLOR_8BPP = 0xCA01 #8 bpp
	COLOR_16BPP_555 = 0xCA02 #15-bit 555 RGB mask (5 bits for red, 5 bits for green, and 5 bits for blue)
	COLOR_16BPP_565 = 0xCA03 #16-bit 565 RGB mask (5 bits for red, 6 bits for green, and 5 bits for blue)
	COLOR_24BPP = 0xCA04 #24-bit RGB mask (8 bits for red, 8 bits for green, and 8 bits for blue)

class HIGH_COLOR_DEPTH(enum.Enum):
	HIGH_COLOR_4BPP= 0x0004 #4 bpp
	HIGH_COLOR_8BPP = 0x0008 #8 bpp
	HIGH_COLOR_15BPP = 0x000F #15-bit 555 RGB mask (5 bits for red, 5 bits for green, and 5 bits for blue)
	HIGH_COLOR_16BPP = 0x0010 #16-bit 565 RGB mask (5 bits for red, 6 bits for green, and 5 bits for blue)
	HIGH_COLOR_24BPP = 0x0018 #24-bit RGB mask (8 bits for red, 8 bits for green, and 8 bits for blue)

class SUPPORTED_COLOR_DEPTH(enum.IntFlag):
	RNS_UD_24BPP_SUPPORT = 0x0001 #24-bit RGB mask (8 bits for red, 8 bits for green, and 8 bits for blue)
	RNS_UD_16BPP_SUPPORT = 0x0002 #16-bit 565 RGB mask (5 bits for red, 6 bits for green, and 5 bits for blue)
	RNS_UD_15BPP_SUPPORT = 0x0004 #15-bit 555 RGB mask (5 bits for red, 5 bits for green, and 5 bits for blue)
	RNS_UD_32BPP_SUPPORT = 0x0008 #32-bit RGB mask (8 bits for the alpha channel, 8 bits for red, 8 bits for green, and 8 bits for blue)

class RNS_UD_CS(enum.IntFlag):
	SUPPORT_ERRINFO_PDU = 0x0001 #Indicates that the client supports the Set Error Info PDU (section 2.2.5.1).
	WANT_32BPP_SESSION = 0x0002 #Indicates that the client is requesting a session color depth of 32 bpp. This flag is necessary because the highColorDepth field does not support a value of 32. If this flag is set, the highColorDepth field SHOULD be set to 24 to provide an acceptable fallback for the scenario where the server does not support 32 bpp color.
	SUPPORT_STATUSINFO_PDU = 0x0004 #Indicates that the client supports the Server Status Info PDU (section 2.2.5.2).
	STRONG_ASYMMETRIC_KEYS = 0x0008 #Indicates that the client supports asymmetric keys larger than 512 bits for use with the Server Certificate (section 2.2.1.4.3.1) sent in the Server Security Data block (section 2.2.1.4.3).
	UNUSED = 0x0010 #An unused flag that MUST be ignored by the server.
	VALID_CONNECTION_TYPE = 0x0020 #Indicates that the connectionType field contains valid data.
	SUPPORT_MONITOR_LAYOUT_PDU = 0x0040 #Indicates that the client supports the Monitor Layout PDU (section 2.2.12.1).
	SUPPORT_NETCHAR_AUTODETECT = 0x0080 #Indicates that the client supports network characteristics detection using the structures and PDUs described in section 2.2.14.
	SUPPORT_DYNVC_GFX_PROTOCOL = 0x0100 #Indicates that the client supports the Graphics Pipeline Extension Protocol described in [MS-RDPEGFX] sections 1, 2, and 3.
	SUPPORT_DYNAMIC_TIME_ZONE = 0x0200 #Indicates that the client supports Dynamic DST. Dynamic DST information is provided by the client in the cbDynamicDSTTimeZoneKeyName, dynamicDSTTimeZoneKeyName and dynamicDaylightTimeDisabled fields of the Extended Info Packet (section 2.2.1.11.1.1.1).
	SUPPORT_HEARTBEAT_PDU = 0x0400 #Indicates that the client supports the Heartbeat PDU (section 2.2.16.1)

class CONNECTION_TYPE(enum.Enum):
	UNK = 0x00 #custom
	MODEM = 0x01 #Modem (56 Kbps)
	BROADBAND_LOW = 0x02 #Low-speed broadband (256 Kbps - 2 Mbps)
	SATELLITE = 0x03 #Satellite (2 Mbps - 16 Mbps with high latency)
	BROADBAND_HIGH = 0x04 #High-speed broadband (2 Mbps - 10 Mbps)
	WAN = 0x05 #WAN (10 Mbps or higher with high latency)
	LAN = 0x06 #LAN (10 Mbps or higher)
	AUTODETECT = 0x07 #The server SHOULD attempt to detect the connection type. If the connection type can be successfully determined then the performance flags, sent by the client in the performanceFlags field of the Extended Info Packet (section 2.2.1.11.1.1.1), SHOULD be ignored and the server SHOULD determine the appropriate set of performance flags to apply to the remote session (based on the detected connection type). If the RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT (0x0080) flag is not set in the earlyCapabilityFlags field, then this value SHOULD be ignored.

class ORIENTATION(enum.Enum):
	LANDSCAPE = 0 #The desktop is not rotated.
	PORTRAIT = 90 #The desktop is rotated clockwise by 90 degrees.
	LANDSCAPE_FLIPPED = 180 #The desktop is rotated clockwise by 180 degrees.
	PORTRAIT_FLIPPED = 270 #The desktop is rotated clockwise by 270 degrees.

class ENCRYPTION_FLAG(enum.Enum):
	FRENCH = 0x00000000
	BIT_40 = 0x00000001 #40-bit session keys MUST be used to encrypt data (with RC4) and generate Message Authentication Codes (MAC).
	BIT_128 = 0x00000002 #128-bit session keys MUST be used to encrypt data (with RC4) and generate MACs.
	BIT_56 = 0x00000008 #56-bit session keys MUST be used to encrypt data (with RC4) and generate MACs.
	FIPS = 0x00000010 #All encryption and Message Authentication Code generation routines MUST be Federal Information Processing Standard (FIPS) 140-1 compliant.

class ENCRYPTION_LEVEL(enum.Enum):
	NONE = 0x00000000
	LOW = 0x00000001
	CLIENT_COMPATIBLE = 0x00000002
	HIGH = 0x00000003
	FIPS = 0x00000004

class ChannelOption(enum.IntFlag):
	INITIALIZED =0x80000000 #This flag is unused and its value MUST be ignored by the server.
	ENCRYPT_RDP = 0x40000000 #This flag is unused and its value MUST be ignored by the server.
	ENCRYPT_SC = 0x20000000 #This flag is unused and its value MUST be ignored by the server.
	ENCRYPT_CS = 0x10000000 #This flag is unused and its value MUST be ignored by the server.
	PRI_HIGH = 0x08000000 #Channel data MUST be sent with high MCS priority.
	PRI_MED = 0x04000000 #Channel data MUST be sent with medium MCS priority.
	PRI_LOW = 0x02000000 #Channel data MUST be sent with low MCS priority.
	COMPRESS_RDP = 0x00800000 #Virtual channel data MUST be compressed if RDP data is being compressed.
	COMPRESS = 0x00400000 #Virtual channel data MUST be compressed, regardless of RDP compression settings.
	SHOW_PROTOCOL = 0x00200000 #The value of this flag MUST be ignored by the server. The visibility of the Channel PDU Header (section 2.2.6.1.1) is determined by the CHANNEL_FLAG_SHOW_PROTOCOL (0x00000010) flag as defined in the flags field (section 2.2.6.1.1).
	REMOTE_CONTROL_PERSISTENT = 0x00100000 #Channel MUST be persistent across remote control transactions.

class ClusterInfo(enum.IntFlag):
	REDIRECTION_SUPPORTED = 0x00000001 #The client can receive server session redirection packets. If this flag is set, the ServerSessionRedirectionVersionMask MUST contain the server session redirection version that the client supports.
	ServerSessionRedirectionVersionMask = 0x0000003C #The server session redirection version that the client supports. See the discussion which follows this table for more information.
	REDIRECTED_SESSIONID_FIELD_VALID = 0x00000002 #The RedirectedSessionID field contains an ID that identifies a session on the server to associate with the connection.
	REDIRECTED_SMARTCARD = 0x00000040 #The client logged on with a smart card.

class MonitorConfig(enum.IntFlag):
	TS_MONITOR_PRIMARY = 0x00000001

class MultitransportFlags(enum.IntFlag):
	TRANSPORTTYPE_UDPFECR = 0x01 #RDP-UDP Forward Error Correction (FEC) reliable transport ([MS-RDPEUDP] sections 1 to 3).
	TRANSPORTTYPE_UDPFECL = 0x04 #RDP-UDP FEC lossy transport ([MS-RDPEUDP] sections 1 to 3).
	TRANSPORTTYPE_UDP_PREFERRED = 0x100 #Indicates that tunneling of static virtual channel traffic over UDP is supported ([MS-RDPEDYC] section 3.1.5.4).
	SOFTSYNC_TCP_TO_UDP = 0x200 #Indicates that switching dynamic virtual channels from the TCP to UDP transport is supported ([MS-RDPEDYC] section 3.1.5.3).

class RNS_UD_SC(enum.IntFlag):
	EDGE_ACTIONS_SUPPORTED_V1 = 0x00000001
	DYNAMIC_DST_SUPPORTED = 0x00000002
	EDGE_ACTIONS_SUPPORTED_V2 = 0x00000004