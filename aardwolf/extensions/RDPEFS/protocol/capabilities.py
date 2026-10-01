import enum
import io
from typing import List

from aardwolf.extensions.RDPEFS.protocol.header import PAKID, RDPDR_CTYP, RDPDR_HEADER


class CAPABILITY_TYPE(enum.IntEnum):
	GENERAL = 1
	PRINTER = 2
	PORT = 3
	DRIVE = 4
	SMARTCARD = 5


RDPDR_IRP_MJ_ALL = 0x0000FFFF
RDPDR_DEVICE_REMOVE_PDUS = 0x0001
RDPDR_CLIENT_DISPLAY_NAME_PDU = 0x0002
RDPDR_USER_LOGGEDON_PDU = 0x0004
ENABLE_ASYNCIO = 0x00000001


class CAPABILITY_HEADER:
	def __init__(self, cap_type=CAPABILITY_TYPE.GENERAL, version=2, payload=b''):
		self.CapabilityType = CAPABILITY_TYPE(cap_type)
		self.Version = version
		self.payload = payload

	def to_bytes(self) -> bytes:
		body = self.payload
		length = 8 + len(body)
		t = int(self.CapabilityType).to_bytes(2, 'little', signed=False)
		t += length.to_bytes(2, 'little', signed=False)
		t += int(self.Version).to_bytes(4, 'little', signed=False)
		t += body
		return t

	@staticmethod
	def from_buffer(buff: io.BytesIO) -> 'CAPABILITY_HEADER':
		cap_type = int.from_bytes(buff.read(2), 'little', signed=False)
		length = int.from_bytes(buff.read(2), 'little', signed=False)
		version = int.from_bytes(buff.read(4), 'little', signed=False)
		payload = buff.read(max(length - 8, 0))
		return CAPABILITY_HEADER(cap_type, version, payload)


class GENERAL_CAPABILITY:
	def __init__(self):
		self.osType = 0
		self.osVersion = 0
		self.protocolMajorVersion = 1
		self.protocolMinorVersion = 13
		self.ioCode1 = RDPDR_IRP_MJ_ALL
		self.ioCode2 = 0
		self.extendedPDU = RDPDR_DEVICE_REMOVE_PDUS | RDPDR_USER_LOGGEDON_PDU
		self.extraFlags1 = ENABLE_ASYNCIO
		self.extraFlags2 = 0
		self.SpecialTypeDeviceCap = 0

	def to_bytes(self) -> bytes:
		t = int(self.osType).to_bytes(4, 'little', signed=False)
		t += int(self.osVersion).to_bytes(4, 'little', signed=False)
		t += int(self.protocolMajorVersion).to_bytes(2, 'little', signed=False)
		t += int(self.protocolMinorVersion).to_bytes(2, 'little', signed=False)
		t += int(self.ioCode1).to_bytes(4, 'little', signed=False)
		t += int(self.ioCode2).to_bytes(4, 'little', signed=False)
		t += int(self.extendedPDU).to_bytes(4, 'little', signed=False)
		t += int(self.extraFlags1).to_bytes(4, 'little', signed=False)
		t += int(self.extraFlags2).to_bytes(4, 'little', signed=False)
		t += int(self.SpecialTypeDeviceCap).to_bytes(4, 'little', signed=False)
		return t


class DR_CORE_CAPABILITY:
	def __init__(self, client=True, capabilities: List[CAPABILITY_HEADER] = None):
		packet = PAKID.CORE_CLIENT_CAPABILITY if client else PAKID.CORE_SERVER_CAPABILITY
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, packet)
		self.capabilities = capabilities or []

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += len(self.capabilities).to_bytes(2, 'little', signed=False)
		t += b'\x00\x00'
		for cap in self.capabilities:
			t += cap.to_bytes()
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CORE_CAPABILITY':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		count = int.from_bytes(buff.read(2), 'little', signed=False)
		buff.read(2)
		caps = [CAPABILITY_HEADER.from_buffer(buff) for _ in range(count)]
		msg = DR_CORE_CAPABILITY(client=header.PacketId == PAKID.CORE_CLIENT_CAPABILITY, capabilities=caps)
		msg.header = header
		return msg


def default_client_capabilities() -> DR_CORE_CAPABILITY:
	general = GENERAL_CAPABILITY()
	return DR_CORE_CAPABILITY(client=True, capabilities=[
		CAPABILITY_HEADER(CAPABILITY_TYPE.GENERAL, 2, general.to_bytes()),
		CAPABILITY_HEADER(CAPABILITY_TYPE.DRIVE, 2, b''),
	])
