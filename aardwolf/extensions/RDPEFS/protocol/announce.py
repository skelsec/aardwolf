import io

from aardwolf.extensions.RDPEFS.protocol.header import PAKID, RDPDR_CTYP, RDPDR_HEADER


class DR_CORE_SERVER_ANNOUNCE:
	def __init__(self, version_major=1, version_minor=13, client_id=1):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_SERVER_ANNOUNCE)
		self.VersionMajor = version_major
		self.VersionMinor = version_minor
		self.ClientId = client_id

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += int(self.VersionMajor).to_bytes(2, 'little', signed=False)
		t += int(self.VersionMinor).to_bytes(2, 'little', signed=False)
		t += int(self.ClientId).to_bytes(4, 'little', signed=False)
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CORE_SERVER_ANNOUNCE':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		msg = DR_CORE_SERVER_ANNOUNCE(
			int.from_bytes(buff.read(2), 'little', signed=False),
			int.from_bytes(buff.read(2), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
		)
		msg.header = header
		return msg


class DR_CORE_CLIENTID_CONFIRM:
	def __init__(self, version_major=1, version_minor=13, client_id=1):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_CLIENTID_CONFIRM)
		self.VersionMajor = version_major
		self.VersionMinor = version_minor
		self.ClientId = client_id

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += int(self.VersionMajor).to_bytes(2, 'little', signed=False)
		t += int(self.VersionMinor).to_bytes(2, 'little', signed=False)
		t += int(self.ClientId).to_bytes(4, 'little', signed=False)
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CORE_CLIENTID_CONFIRM':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		msg = DR_CORE_CLIENTID_CONFIRM(
			int.from_bytes(buff.read(2), 'little', signed=False),
			int.from_bytes(buff.read(2), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
		)
		msg.header = header
		return msg


class DR_CORE_CLIENT_NAME:
	def __init__(self, computer_name='AARDWOLF', unicode=True):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_CLIENT_NAME)
		self.UnicodeFlag = 1 if unicode else 0
		self.CodePage = 0
		self.ComputerName = computer_name

	def to_bytes(self) -> bytes:
		name = (self.ComputerName + '\x00').encode('utf-16-le' if self.UnicodeFlag else 'ascii')
		t = self.header.to_bytes()
		t += int(self.UnicodeFlag).to_bytes(4, 'little', signed=False)
		t += int(self.CodePage).to_bytes(4, 'little', signed=False)
		t += len(name).to_bytes(4, 'little', signed=False)
		t += name
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CORE_CLIENT_NAME':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		unicode_flag = int.from_bytes(buff.read(4), 'little', signed=False)
		codepage = int.from_bytes(buff.read(4), 'little', signed=False)
		name_len = int.from_bytes(buff.read(4), 'little', signed=False)
		raw = buff.read(name_len)
		name = raw.decode('utf-16-le' if unicode_flag else 'ascii').replace('\x00', '')
		msg = DR_CORE_CLIENT_NAME(name, bool(unicode_flag))
		msg.header = header
		msg.CodePage = codepage
		return msg
