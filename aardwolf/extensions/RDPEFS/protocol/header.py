import enum
import io


class RDPDR_CTYP(enum.IntEnum):
	CORE = 0x4472
	PRN = 0x5052


class PAKID(enum.IntEnum):
	CORE_SERVER_ANNOUNCE = 0x496E
	CORE_CLIENTID_CONFIRM = 0x4343
	CORE_CLIENT_NAME = 0x434E
	CORE_DEVICELIST_ANNOUNCE = 0x4441
	CORE_DEVICE_REPLY = 0x6472
	CORE_DEVICE_IOREQUEST = 0x4952
	CORE_DEVICE_IOCOMPLETION = 0x4943
	CORE_SERVER_CAPABILITY = 0x5350
	CORE_CLIENT_CAPABILITY = 0x4350
	CORE_DEVICELIST_REMOVE = 0x444D
	CORE_USER_LOGGEDON = 0x554C


class RDPDR_HEADER:
	def __init__(self, component=RDPDR_CTYP.CORE, packet_id=PAKID.CORE_SERVER_ANNOUNCE):
		self.Component = RDPDR_CTYP(component)
		self.PacketId = PAKID(packet_id)

	def to_bytes(self) -> bytes:
		return int(self.Component).to_bytes(2, 'little', signed=False) + int(self.PacketId).to_bytes(2, 'little', signed=False)

	@staticmethod
	def from_bytes(data: bytes) -> 'RDPDR_HEADER':
		return RDPDR_HEADER.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO) -> 'RDPDR_HEADER':
		component = int.from_bytes(buff.read(2), 'little', signed=False)
		packet_id = int.from_bytes(buff.read(2), 'little', signed=False)
		return RDPDR_HEADER(component, packet_id)
