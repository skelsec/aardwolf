import io
import enum

class TS_RAIL_LEVEL(enum.IntFlag):
	SUPPORTED = 0x1 #Set to 1 if the client/server is capable of supporting Remote Programs; set to 0 otherwise.
	DOCKED_LANGBAR_SUPPORTED = 0x2 #Set to 1 if the client/server is capable of supporting Docked Language Bar for Remote Programs; set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.
	SHELL_INTEGRATION_SUPPORTED = 0x4 #Set to 1 if the client/server is capable of supporting extended shell integration like tabbed windows and overlay icons for Remote Programs; set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.
	LANGUAGE_IME_SYNC_SUPPORTED = 0x8 #Set to 1 if the client/server is capable of supporting syncing language/IME changes for Remote Programs; set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.
	SERVER_TO_CLIENT_IME_SYNC_SUPPORTED = 0x10 #Set to 1 if the client/server is capable of supporting syncing IME changes originating at the server for Remote Programs; set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.
	HIDE_MINIMIZED_APPS_SUPPORTED = 0x20 #Set to 1 if the client/server supports hiding minimized windows of Remote Programs on the server; set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.
	WINDOW_CLOAKING_SUPPORTED = 0x40 #Set to 1 if the client/server supports syncing per-window cloak state changes originating on the client for Remote Programs; set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.
	HANDSHAKE_EX_SUPPORTED = 0x80 #Set to 1 if the client/server supports the HandshakeEx PDU (section 2.2.2.2.3); set to 0 otherwise. This flag MUST be set to 0 if TS_RAIL_LEVEL_SUPPORTED is 0.

class TS_REMOTE_PROGRAMS_CAP_SET:
	def __init__(self):
		self.RailSupportLevel:TS_RAIL_LEVEL = None

	def to_bytes(self):
		t = self.RailSupportLevel.to_bytes(4, byteorder='little', signed = False)
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_REMOTE_PROGRAMS_CAP_SET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_REMOTE_PROGRAMS_CAP_SET()
		msg.RailSupportLevel = TS_RAIL_LEVEL(int.from_bytes(buff.read(4), byteorder='little', signed = False))
		return msg

	def __repr__(self):
		t = '==== TS_REMOTE_PROGRAMS_CAP_SET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t