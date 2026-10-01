import enum
import io

from aardwolf.extensions.RDPEFS.protocol.header import PAKID, RDPDR_CTYP, RDPDR_HEADER
from aardwolf.extensions.RDPEFS.wintypes.create import CreateDisposition, CreateOptions, ShareAccess
from aardwolf.extensions.RDPEFS.wintypes.fileinfoclass import FileInfoClass, FsInformationClass
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


class IRP_MJ(enum.IntEnum):
	CREATE = 0x00000000
	CLOSE = 0x00000002
	READ = 0x00000003
	WRITE = 0x00000004
	QUERY_INFORMATION = 0x00000005
	SET_INFORMATION = 0x00000006
	QUERY_VOLUME_INFORMATION = 0x0000000A
	DIRECTORY_CONTROL = 0x0000000C
	DEVICE_CONTROL = 0x0000000E
	LOCK_CONTROL = 0x00000011
	CLEANUP = 0x00000012
	QUERY_SECURITY = 0x00000014
	SET_SECURITY = 0x00000015


class IRP_MN(enum.IntEnum):
	QUERY_DIRECTORY = 0x00000001
	NOTIFY_CHANGE_DIRECTORY = 0x00000002


class DR_DEVICE_IOREQUEST:
	def __init__(
			self,
			device_id=0,
			file_id=0,
			completion_id=0,
			major=IRP_MJ.CREATE,
			minor=0):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_DEVICE_IOREQUEST)
		self.DeviceId = device_id
		self.FileId = file_id
		self.CompletionId = completion_id
		try:
			self.MajorFunction = IRP_MJ(major)
		except ValueError:
			self.MajorFunction = major
		self.MinorFunction = minor
		self.payload = b''

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += int(self.DeviceId).to_bytes(4, 'little', signed=False)
		t += int(self.FileId).to_bytes(4, 'little', signed=False)
		t += int(self.CompletionId).to_bytes(4, 'little', signed=False)
		t += int(self.MajorFunction).to_bytes(4, 'little', signed=False)
		t += int(self.MinorFunction).to_bytes(4, 'little', signed=False)
		t += self.payload
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_DEVICE_IOREQUEST':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		msg = DR_DEVICE_IOREQUEST(
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
		)
		msg.header = header
		msg.payload = buff.read()
		return msg


class DR_CREATE_REQ:
	def __init__(self):
		self.DesiredAccess = 0
		self.AllocationSize = 0
		self.FileAttributes = 0
		self.SharedAccess = ShareAccess(0)
		self.Disposition = CreateDisposition.FILE_OPEN
		self.CreateOptions = CreateOptions(0)
		self.Path = ''

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_CREATE_REQ':
		buff = io.BytesIO(data)
		msg = DR_CREATE_REQ()
		msg.DesiredAccess = int.from_bytes(buff.read(4), 'little', signed=False)
		msg.AllocationSize = int.from_bytes(buff.read(8), 'little', signed=True)
		msg.FileAttributes = int.from_bytes(buff.read(4), 'little', signed=False)
		msg.SharedAccess = ShareAccess(int.from_bytes(buff.read(4), 'little', signed=False))
		msg.Disposition = CreateDisposition(int.from_bytes(buff.read(4), 'little', signed=False))
		msg.CreateOptions = CreateOptions(int.from_bytes(buff.read(4), 'little', signed=False))
		path_len = int.from_bytes(buff.read(4), 'little', signed=False)
		msg.Path = buff.read(path_len).decode('utf-16-le').replace('\x00', '')
		return msg

	def to_bytes(self) -> bytes:
		path = (self.Path + '\x00').encode('utf-16-le') if self.Path else b''
		t = int(self.DesiredAccess).to_bytes(4, 'little', signed=False)
		t += int(self.AllocationSize).to_bytes(8, 'little', signed=True)
		t += int(self.FileAttributes).to_bytes(4, 'little', signed=False)
		t += int(self.SharedAccess).to_bytes(4, 'little', signed=False)
		t += int(self.Disposition).to_bytes(4, 'little', signed=False)
		t += int(self.CreateOptions).to_bytes(4, 'little', signed=False)
		t += len(path).to_bytes(4, 'little', signed=False)
		t += path
		return t


class DR_READ_REQ:
	def __init__(self, length=0, offset=0):
		self.Length = length
		self.Offset = offset

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_READ_REQ':
		return DR_READ_REQ(
			int.from_bytes(data[0:4], 'little', signed=False),
			int.from_bytes(data[4:12], 'little', signed=True),
		)

	def to_bytes(self) -> bytes:
		return int(self.Length).to_bytes(4, 'little', signed=False) + int(self.Offset).to_bytes(8, 'little', signed=True) + (b'\x00' * 20)


class DR_WRITE_REQ:
	def __init__(self, offset=0, data=b''):
		self.Offset = offset
		self.WriteData = data

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_WRITE_REQ':
		length = int.from_bytes(data[0:4], 'little', signed=False)
		offset = int.from_bytes(data[4:12], 'little', signed=True)
		# 20 bytes padding after offset
		payload = data[32:32 + length]
		return DR_WRITE_REQ(offset, payload)

	def to_bytes(self) -> bytes:
		t = len(self.WriteData).to_bytes(4, 'little', signed=False)
		t += int(self.Offset).to_bytes(8, 'little', signed=True)
		t += b'\x00' * 20
		t += self.WriteData
		return t


class DR_QUERY_INFORMATION_REQ:
	def __init__(self, info_class=FileInfoClass.FileBasicInformation, buffer=b''):
		self.FsInformationClass = info_class
		self.QueryBuffer = buffer

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_QUERY_INFORMATION_REQ':
		info_class = int.from_bytes(data[0:4], 'little', signed=False)
		length = int.from_bytes(data[4:8], 'little', signed=False)
		buffer = data[32:32 + length]
		try:
			info_class = FileInfoClass(info_class)
		except ValueError:
			pass
		return DR_QUERY_INFORMATION_REQ(info_class, buffer)

	def to_bytes(self) -> bytes:
		t = int(self.FsInformationClass).to_bytes(4, 'little', signed=False)
		t += len(self.QueryBuffer).to_bytes(4, 'little', signed=False)
		t += b'\x00' * 24
		t += self.QueryBuffer
		return t


class DR_SET_INFORMATION_REQ(DR_QUERY_INFORMATION_REQ):
	@property
	def SetBuffer(self):
		return self.QueryBuffer


class DR_QUERY_DIRECTORY_REQ:
	def __init__(self, info_class=FileInfoClass.FileBothDirectoryInformation, initial=True, path='*'):
		self.FsInformationClass = info_class
		self.InitialQuery = 1 if initial else 0
		self.Path = path

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_QUERY_DIRECTORY_REQ':
		info_class = int.from_bytes(data[0:4], 'little', signed=False)
		initial = data[4]
		path_len = int.from_bytes(data[5:9], 'little', signed=False)
		path = data[32:32 + path_len].decode('utf-16-le').replace('\x00', '')
		try:
			info_class = FileInfoClass(info_class)
		except ValueError:
			pass
		return DR_QUERY_DIRECTORY_REQ(info_class, bool(initial), path)

	def to_bytes(self) -> bytes:
		path = (self.Path + '\x00').encode('utf-16-le') if self.Path else b''
		t = int(self.FsInformationClass).to_bytes(4, 'little', signed=False)
		t += bytes([self.InitialQuery])
		t += len(path).to_bytes(4, 'little', signed=False)
		t += b'\x00' * 23
		t += path
		return t


class DR_QUERY_VOLUME_INFORMATION_REQ:
	def __init__(self, info_class=FsInformationClass.FileFsVolumeInformation):
		self.FsInformationClass = info_class

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_QUERY_VOLUME_INFORMATION_REQ':
		info_class = int.from_bytes(data[0:4], 'little', signed=False)
		try:
			info_class = FsInformationClass(info_class)
		except ValueError:
			pass
		return DR_QUERY_VOLUME_INFORMATION_REQ(info_class)

	def to_bytes(self) -> bytes:
		return int(self.FsInformationClass).to_bytes(4, 'little', signed=False) + (0).to_bytes(4, 'little', signed=False) + (b'\x00' * 24)


class DR_DEVICE_IOCOMPLETION:
	def __init__(self, device_id=0, completion_id=0, io_status=NTStatus.SUCCESS, payload=b''):
		self.header = RDPDR_HEADER(RDPDR_CTYP.CORE, PAKID.CORE_DEVICE_IOCOMPLETION)
		self.DeviceId = device_id
		self.CompletionId = completion_id
		self.IoStatus = int(io_status)
		self.payload = payload

	def to_bytes(self) -> bytes:
		t = self.header.to_bytes()
		t += int(self.DeviceId).to_bytes(4, 'little', signed=False)
		t += int(self.CompletionId).to_bytes(4, 'little', signed=False)
		t += int(self.IoStatus).to_bytes(4, 'little', signed=False)
		t += self.payload
		return t

	@staticmethod
	def from_bytes(data: bytes) -> 'DR_DEVICE_IOCOMPLETION':
		buff = io.BytesIO(data)
		header = RDPDR_HEADER.from_buffer(buff)
		msg = DR_DEVICE_IOCOMPLETION(
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
			int.from_bytes(buff.read(4), 'little', signed=False),
			buff.read(),
		)
		msg.header = header
		return msg


def create_response_payload(file_id: int, information: int) -> bytes:
	return int(file_id).to_bytes(4, 'little', signed=False) + bytes([information & 0xFF])


def buffer_response_payload(data: bytes) -> bytes:
	return len(data).to_bytes(4, 'little', signed=False) + data


def write_response_payload(length: int) -> bytes:
	return int(length).to_bytes(4, 'little', signed=False) + b'\x00'
