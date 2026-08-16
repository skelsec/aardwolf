import io
from typing import List

from aardwolf.extensions.RDPEFS.protocol.header import PAKID, RDPDR_CTYP, RDPDR_HEADER


RDPDR_DTYP_SERIAL = 0x00000001
RDPDR_DTYP_PARALLEL = 0x00000002
RDPDR_DTYP_PRINT = 0x00000004
RDPDR_DTYP_FILESYSTEM = 0x00000008
RDPDR_DTYP_SMARTCARD = 0x00000020


class DEVICE_ANNOUNCE:
	def __init__(self, device_type=RDPDR_DTYP_FILESYSTEM, device_id=1, dos_name='HOME', device_name=''):
		self.DeviceType = device_type
		self.DeviceId = device_id
		self.PreferredDosName = dos_name
		self.DeviceName = device_name or dos_name

	def to_bytes(self) -> bytes:
		dos = self.PreferredDosName.encode('ascii')[:8].ljust(8, b'\x00')
		data = (self.DeviceName + '\x00').encode('utf-16-le')
		t = int(self.DeviceType).to_bytes(4, 'little', signed=False)
		t += int(self.DeviceId).to_bytes(4, 'little', signed=False)
		t += dos
		t += len(data).to_bytes(4, 'little', signed=False)
		t += data
		return t

	@staticmethod
	def from_buffer(buff: io.BytesIO) -> 'DEVICE_ANNOUNCE':
		device_type = int.from_bytes(buff.read(4), 'little', signed=False)
		device_id = int.from_bytes(buff.read(4), 'little', signed=False)
		dos = buff.read(8).split(b'\x00', 1)[0].decode('ascii', errors='replace')
		data_len = int.from_bytes(buff.read(4), 'little', signed=False)
		raw = buff.read(data_len)
		name = raw.decode('utf-16-le').replace('\x00', '') if raw else dos
		return DEVICE_ANNOUNCE(device_type, device_id, dos, name)


class DR_CORE_DEVICELIST_ANNOUNCE:
	def __init__(self, devices: List[DEVICE_ANNOUNCE] = None):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_DEVICELIST_ANNOUNCE)
		self.devices = devices or []

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += len(self.devices).to_bytes(4, 'little', signed=False)
		for device in self.devices:
			t += device.to_bytes()
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CORE_DEVICELIST_ANNOUNCE':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		count = int.from_bytes(buff.read(4), 'little', signed=False)
		devices = [DEVICE_ANNOUNCE.from_buffer(buff) for _ in range(count)]
		msg = DR_CORE_DEVICELIST_ANNOUNCE(devices)
		msg.header = header
		return msg


class DR_CORE_DEVICE_REPLY:
	def __init__(self, device_id=0, result_code=0):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_DEVICE_REPLY)
		self.DeviceId = device_id
		self.ResultCode = result_code

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += int(self.DeviceId).to_bytes(4, 'little', signed=False)
		t += int(self.ResultCode).to_bytes(4, 'little', signed=False)
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CORE_DEVICE_REPLY':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		msg = DR_CORE_DEVICE_REPLY(
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
		)
		msg.header = header
		return msg
