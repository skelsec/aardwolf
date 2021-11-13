import io
import enum

class INPUT_FLAG(enum.IntFlag):
	SCANCODES = 0x0001 #Indicates support for using scancodes in the Keyboard Event notifications (sections 2.2.8.1.1.3.1.1.1 and 2.2.8.1.2.2.1).
	MOUSEX = 0x0004 #Indicates support for Extended Mouse Event notifications (sections 2.2.8.1.1.3.1.1.4 and 2.2.8.1.2.2.4).
	FASTPATH_INPUT = 0x0008 #Advertised by RDP 5.0 and 5.1 servers to indicate support for fast-path input.
	UNICODE = 0x0010 #Indicates support for Unicode Keyboard Event notifications (sections 2.2.8.1.1.3.1.1.2 and 2.2.8.1.2.2.2).
	FASTPATH_INPUT2 = 0x0020 #Advertised by all RDP servers, except for RDP 4.0, 5.0, and 5.1 servers, to indicate support for fast-path input. Clients that do not support this flag will not be able to use fast-path input when connecting to RDP 5.2, 6.0, 6.1, 7.0, 7.1, 8.0, 8.1, 10.0, 10.1, 10.2, 10.3, 10.4, and 10.5 servers.
	UNUSED1 = 0x0040 #An unused flag that MUST be ignored by the client if it is present in the server-to-client Input Capability Set.
	UNUSED2 = 0x0080 #An unused flag that MUST be ignored by the server if it is present in the client-to-server Input Capability Set.
	MOUSE_HWHEEL = 0x0100 #Indicates support for horizontal Mouse Wheel Event notifications (sections 2.2.8.1.1.3.1.1.3 and 2.2.8.1.2.2.3).
	QOE_TIMESTAMPS = 0x0200 #Indicates support for Quality of Experience (QoE) Timestamp Event notifications (section 2.2.8.1.2.2.6). There is no slow-path support for Quality of Experience (QoE) timestamps.

class TS_INPUT_CAPABILITYSET:
	def __init__(self):
		self.inputFlags:INPUT_FLAG = INPUT_FLAG.SCANCODES
		self.pad2octets:bytes = b'\x00'*2
		self.keyboardLayout:int = 0x00000409 #US
		self.keyboardType: int = 0x00000004
		self.keyboardSubType: int = 0
		self.keyboardFunctionKey: int = 12
		self.imeFileName: str = ''

	def to_bytes(self):
		imeFileName = self.imeFileName.encode('utf-16-le').ljust(64, b'\x00')

		t = self.inputFlags.to_bytes(2, byteorder='little', signed = False)
		t += self.pad2octets
		t += self.keyboardLayout.to_bytes(4, byteorder='little', signed = False)
		t += self.keyboardType.to_bytes(4, byteorder='little', signed = False)
		t += self.keyboardSubType.to_bytes(4, byteorder='little', signed = False)
		t += self.keyboardFunctionKey.to_bytes(4, byteorder='little', signed = False)
		t += imeFileName
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_INPUT_CAPABILITYSET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_INPUT_CAPABILITYSET()
		msg.inputFlags = INPUT_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.pad2octets = buff.read(2)
		msg.keyboardLayout = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.keyboardType = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.keyboardSubType = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		msg.keyboardFunctionKey = int.from_bytes(buff.read(4), byteorder='little', signed = False)
		try:
			msg.imeFileName = buff.read(64).decode('utf-16-le').replace('\x00', '')
		except:
			#TODO: FIX THIS (on windows XP it is some werid garbage here)
			msg.imeFileName = ''
		
		return msg

	def __repr__(self):
		t = '==== TS_INPUT_CAPABILITYSET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t