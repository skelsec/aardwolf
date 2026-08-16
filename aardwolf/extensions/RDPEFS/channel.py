import asyncio
import socket
import traceback
from typing import Dict, Optional

from aardwolf import logger
from aardwolf.channels import Channel
from aardwolf.extensions.RDPEFS.protocol.announce import (
	DR_CORE_CLIENT_NAME,
	DR_CORE_CLIENTID_CONFIRM,
	DR_CORE_SERVER_ANNOUNCE,
)
from aardwolf.extensions.RDPEFS.protocol.capabilities import default_client_capabilities
from aardwolf.extensions.RDPEFS.protocol.device import (
	DEVICE_ANNOUNCE,
	DR_CORE_DEVICE_REPLY,
	DR_CORE_DEVICELIST_ANNOUNCE,
	RDPDR_DTYP_FILESYSTEM,
)
from aardwolf.extensions.RDPEFS.protocol.header import PAKID, RDPDR_HEADER
from aardwolf.extensions.RDPEFS.protocol.io import (
	DR_CREATE_REQ,
	DR_DEVICE_IOCOMPLETION,
	DR_DEVICE_IOREQUEST,
	DR_QUERY_DIRECTORY_REQ,
	DR_QUERY_INFORMATION_REQ,
	DR_QUERY_VOLUME_INFORMATION_REQ,
	DR_READ_REQ,
	DR_SET_INFORMATION_REQ,
	DR_WRITE_REQ,
	IRP_MJ,
	IRP_MN,
	buffer_response_payload,
	create_response_payload,
	write_response_payload,
)
from aardwolf.extensions.RDPEFS.provider import DriveError, DriveHandle, DriveProvider
from aardwolf.extensions.RDPEFS.wintypes.create import CreateAction
from aardwolf.extensions.RDPEFS.wintypes.fileinfo import (
	FileBasicInformation,
	FileDispositionInformation,
	FileEndOfFileInformation,
	FileInternalInformation,
	FileNameInformation,
	FileRenameInformation,
	FileStandardInformation,
	pack_directory_entries,
)
from aardwolf.extensions.RDPEFS.wintypes.fileinfoclass import FileInfoClass, FsInformationClass
from aardwolf.extensions.RDPEFS.wintypes.fsinfo import (
	FileFsAttributeInformation,
	FileFsDeviceInformation,
	FileFsFullSizeInformation,
	FileFsSizeInformation,
	FileFsVolumeInformation,
)
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus
from aardwolf.protocol.T124.userdata.constants import ChannelOption
from aardwolf.protocol.T128.security import SEC_HDR_FLAG, TS_SECURITY_HEADER
from aardwolf.protocol.channelpdu import CHANNEL_FLAG, CHANNEL_PDU_HEADER


class RDPDRChannel(Channel):
	name = 'rdpdr'

	def __init__(self, iosettings):
		Channel.__init__(
			self,
			self.name,
			ChannelOption.INITIALIZED | ChannelOption.ENCRYPT_RDP | ChannelOption.COMPRESS_RDP | ChannelOption.SHOW_PROTOCOL,
		)
		self.iosettings = iosettings
		self.drives = list(getattr(iosettings, 'drives', None) or [])
		self._devices: Dict[int, DriveProvider] = {}
		self._handles: Dict[int, DriveHandle] = {}
		self._next_file_id = 1
		self._client_id = 1
		self._version_major = 1
		self._version_minor = 13
		self._devices_announced = False
		self._fragment = b''
		self._writer_lock = asyncio.Lock()
		self._assign_device_ids()

	def _assign_device_ids(self) -> None:
		names = [drive.name.upper() for drive in self.drives]
		if len(names) != len(set(names)):
			raise ValueError('RDPDR drive DosNames must be unique')
		for index, drive in enumerate(self.drives, start=1):
			self._devices[index] = drive
			drive.device_id = index

	async def start(self):
		return True, None

	async def stop(self):
		for handle in list(self._handles.values()):
			provider = self._devices.get(getattr(handle, 'device_id', None))
			if provider is not None:
				try:
					await provider.close(handle)
				except DriveError:
					pass
		self._handles.clear()
		return True, None

	async def process_channel_data(self, data):
		channeldata = CHANNEL_PDU_HEADER.from_bytes(data)
		payload = data[8:]
		if CHANNEL_FLAG.CHANNEL_FLAG_FIRST in channeldata.flags:
			self._fragment = b''
		self._fragment += payload
		if CHANNEL_FLAG.CHANNEL_FLAG_LAST in channeldata.flags:
			message = self._fragment
			self._fragment = b''
			await self.handle_message(message)

	async def handle_message(self, data: bytes) -> None:
		header = RDPDR_HEADER.from_bytes(data)
		if header.PacketId == PAKID.CORE_SERVER_ANNOUNCE:
			await self._on_server_announce(DR_CORE_SERVER_ANNOUNCE.from_bytes(data))
		elif header.PacketId == PAKID.CORE_CLIENTID_CONFIRM:
			return
		elif header.PacketId == PAKID.CORE_SERVER_CAPABILITY:
			await self._on_server_capability()
		elif header.PacketId == PAKID.CORE_USER_LOGGEDON:
			await self._announce_devices()
		elif header.PacketId == PAKID.CORE_DEVICE_REPLY:
			reply = DR_CORE_DEVICE_REPLY.from_bytes(data)
			logger.debug('RDPDR device %s result %s', reply.DeviceId, hex(reply.ResultCode))
		elif header.PacketId == PAKID.CORE_DEVICE_IOREQUEST:
			await self._on_io_request(DR_DEVICE_IOREQUEST.from_bytes(data))
		else:
			logger.debug('Ignoring RDPDR packet %s', header.PacketId)

	async def _on_server_announce(self, announce: DR_CORE_SERVER_ANNOUNCE) -> None:
		self._client_id = announce.ClientId
		self._version_major = min(announce.VersionMajor, 1)
		self._version_minor = min(announce.VersionMinor, 13)
		await self.fragment_and_send(DR_CORE_CLIENTID_CONFIRM(
			self._version_major, self._version_minor, self._client_id
		).to_bytes())
		try:
			computer = socket.gethostname() or 'AARDWOLF'
		except OSError:
			computer = 'AARDWOLF'
		await self.fragment_and_send(DR_CORE_CLIENT_NAME(computer).to_bytes())

	async def _on_server_capability(self) -> None:
		await self.fragment_and_send(default_client_capabilities().to_bytes())
		await self._announce_devices()

	async def _announce_devices(self) -> None:
		if self._devices_announced:
			return
		devices = [
			DEVICE_ANNOUNCE(RDPDR_DTYP_FILESYSTEM, device_id, provider.name, provider.label)
			for device_id, provider in self._devices.items()
		]
		await self.fragment_and_send(DR_CORE_DEVICELIST_ANNOUNCE(devices).to_bytes())
		self._devices_announced = True

	def _alloc_file_id(self) -> int:
		file_id = self._next_file_id
		self._next_file_id += 1
		return file_id

	async def _on_io_request(self, request: DR_DEVICE_IOREQUEST) -> None:
		try:
			status, payload = await self._dispatch_io(request)
		except DriveError as exc:
			status, payload = exc.status, b''
		except Exception:
			logger.error('RDPDR I/O failed\n%s', traceback.format_exc())
			status, payload = NTStatus.UNSUCCESSFUL, b''
		await self.fragment_and_send(DR_DEVICE_IOCOMPLETION(
			request.DeviceId, request.CompletionId, status, payload
		).to_bytes())

	async def _dispatch_io(self, request: DR_DEVICE_IOREQUEST):
		provider = self._devices.get(request.DeviceId)
		if provider is None:
			return NTStatus.NO_SUCH_FILE, b''
		major = request.MajorFunction
		if major == IRP_MJ.CREATE:
			return await self._irp_create(provider, request)
		if major == IRP_MJ.CLOSE:
			return await self._irp_close(request)
		if major == IRP_MJ.CLEANUP:
			return NTStatus.SUCCESS, b''
		if major == IRP_MJ.READ:
			return await self._irp_read(request)
		if major == IRP_MJ.WRITE:
			return await self._irp_write(request)
		if major == IRP_MJ.QUERY_INFORMATION:
			return await self._irp_query_information(request)
		if major == IRP_MJ.SET_INFORMATION:
			return await self._irp_set_information(request)
		if major == IRP_MJ.QUERY_VOLUME_INFORMATION:
			return await self._irp_query_volume(provider, request)
		if major == IRP_MJ.DIRECTORY_CONTROL:
			if request.MinorFunction == IRP_MN.NOTIFY_CHANGE_DIRECTORY:
				return NTStatus.NOT_SUPPORTED, b''
			return await self._irp_query_directory(request)
		if major == IRP_MJ.LOCK_CONTROL:
			return NTStatus.SUCCESS, b''
		return NTStatus.NOT_SUPPORTED, b''

	async def _irp_create(self, provider: DriveProvider, request: DR_DEVICE_IOREQUEST):
		body = DR_CREATE_REQ.from_bytes(request.payload)
		handle = await provider.create(body.Path, body.DesiredAccess, body.Disposition, body.CreateOptions)
		file_id = self._alloc_file_id()
		handle.device_id = request.DeviceId
		handle.file_id = file_id
		self._handles[file_id] = handle
		action = getattr(handle, 'action', CreateAction.FILE_OPENED)
		return NTStatus.SUCCESS, create_response_payload(file_id, int(action))

	def _handle(self, request: DR_DEVICE_IOREQUEST) -> DriveHandle:
		handle = self._handles.get(request.FileId)
		if handle is None or getattr(handle, 'device_id', None) != request.DeviceId:
			raise DriveError(NTStatus.NO_SUCH_FILE)
		return handle

	async def _irp_close(self, request: DR_DEVICE_IOREQUEST):
		handle = self._handles.pop(request.FileId, None)
		if handle is None:
			return NTStatus.SUCCESS, b''
		provider = self._devices.get(handle.device_id)
		if provider is not None:
			await provider.close(handle)
		return NTStatus.SUCCESS, b''

	async def _irp_read(self, request: DR_DEVICE_IOREQUEST):
		handle = self._handle(request)
		body = DR_READ_REQ.from_bytes(request.payload)
		provider = self._devices[handle.device_id]
		data = await provider.read(handle, body.Offset, body.Length)
		return NTStatus.SUCCESS, buffer_response_payload(data)

	async def _irp_write(self, request: DR_DEVICE_IOREQUEST):
		handle = self._handle(request)
		body = DR_WRITE_REQ.from_bytes(request.payload)
		provider = self._devices[handle.device_id]
		written = await provider.write(handle, body.Offset, body.WriteData)
		return NTStatus.SUCCESS, write_response_payload(written)

	async def _irp_query_information(self, request: DR_DEVICE_IOREQUEST):
		handle = self._handle(request)
		body = DR_QUERY_INFORMATION_REQ.from_bytes(request.payload)
		provider = self._devices[handle.device_id]
		stat = await provider.query_info(handle)
		info_class = body.FsInformationClass
		if info_class == FileInfoClass.FileBasicInformation:
			data = FileBasicInformation(
				stat.creation_time, stat.last_access_time, stat.last_write_time, stat.change_time, stat.attributes
			).to_bytes()
		elif info_class == FileInfoClass.FileStandardInformation:
			data = FileStandardInformation(
				stat.allocation_size or stat.size,
				stat.size,
				1,
				stat.delete_pending,
				stat.is_dir,
			).to_bytes()
		elif info_class == FileInfoClass.FileInternalInformation:
			data = FileInternalInformation(stat.file_id).to_bytes()
		elif info_class == FileInfoClass.FileNameInformation:
			data = FileNameInformation(handle.path).to_bytes()
		elif info_class == FileInfoClass.FileAttributeTagInformation:
			data = int(stat.attributes).to_bytes(4, 'little', signed=False) + b'\x00' * 4
		else:
			return NTStatus.NOT_SUPPORTED, b''
		return NTStatus.SUCCESS, buffer_response_payload(data)

	async def _irp_set_information(self, request: DR_DEVICE_IOREQUEST):
		handle = self._handle(request)
		body = DR_SET_INFORMATION_REQ.from_bytes(request.payload)
		provider = self._devices[handle.device_id]
		info_class = body.FsInformationClass
		if info_class == FileInfoClass.FileEndOfFileInformation:
			info = FileEndOfFileInformation.from_bytes(body.SetBuffer)
			await provider.set_end_of_file(handle, info.end_of_file)
		elif info_class == FileInfoClass.FileDispositionInformation:
			info = FileDispositionInformation.from_bytes(body.SetBuffer)
			await provider.set_disposition(handle, info.delete_pending)
		elif info_class == FileInfoClass.FileRenameInformation:
			info = FileRenameInformation.from_bytes(body.SetBuffer)
			await provider.rename(handle, info.file_name, info.replace_if_exists)
		elif info_class == FileInfoClass.FileBasicInformation:
			pass
		else:
			return NTStatus.NOT_SUPPORTED, b''
		return NTStatus.SUCCESS, b''

	async def _irp_query_volume(self, provider: DriveProvider, request: DR_DEVICE_IOREQUEST):
		body = DR_QUERY_VOLUME_INFORMATION_REQ.from_bytes(request.payload)
		volume = await provider.volume()
		info_class = body.FsInformationClass
		if info_class == FsInformationClass.FileFsVolumeInformation:
			data = FileFsVolumeInformation(volume.label, volume.serial).to_bytes()
		elif info_class == FsInformationClass.FileFsSizeInformation:
			data = FileFsSizeInformation(
				volume.total_units, volume.available_units, volume.sectors_per_unit, volume.bytes_per_sector
			).to_bytes()
		elif info_class == FsInformationClass.FileFsFullSizeInformation:
			data = FileFsFullSizeInformation(
				volume.total_units, volume.available_units, volume.sectors_per_unit, volume.bytes_per_sector
			).to_bytes()
		elif info_class == FsInformationClass.FileFsAttributeInformation:
			data = FileFsAttributeInformation(volume.fs_name).to_bytes()
		elif info_class == FsInformationClass.FileFsDeviceInformation:
			data = FileFsDeviceInformation().to_bytes()
		else:
			return NTStatus.NOT_SUPPORTED, b''
		return NTStatus.SUCCESS, buffer_response_payload(data)

	async def _irp_query_directory(self, request: DR_DEVICE_IOREQUEST):
		handle = self._handle(request)
		body = DR_QUERY_DIRECTORY_REQ.from_bytes(request.payload)
		provider = self._devices[handle.device_id]
		if body.InitialQuery or handle.cursor is None:
			handle.cursor = await provider.query_directory(handle, body.Path or '*')
		entries = handle.cursor.next()
		if not entries:
			return NTStatus.NO_MORE_FILES, buffer_response_payload(b'')
		data = pack_directory_entries([entry.to_directory_entry() for entry in entries], body.FsInformationClass)
		return NTStatus.SUCCESS, buffer_response_payload(data)

	async def fragment_and_send(self, data: bytes):
		async with self._writer_lock:
			i = 0
			while i <= len(data):
				flags = CHANNEL_FLAG.CHANNEL_FLAG_SHOW_PROTOCOL
				chunk = data[i:i + 1400]
				if i == 0:
					flags |= CHANNEL_FLAG.CHANNEL_FLAG_FIRST
					length = len(data)
				else:
					length = None
				i += 1400
				if i >= len(data):
					flags |= CHANNEL_FLAG.CHANNEL_FLAG_LAST
				packet = CHANNEL_PDU_HEADER.serialize_packet(flags, chunk, length=length)
				sec_hdr = None
				if self.connection is not None and getattr(self.connection, 'cryptolayer', None) is not None:
					sec_hdr = TS_SECURITY_HEADER()
					sec_hdr.flags = SEC_HDR_FLAG.ENCRYPT
					sec_hdr.flagsHi = 0
				await self.send_channel_data(packet, sec_hdr, None, None, False)
				if not data:
					break
			return True, None
