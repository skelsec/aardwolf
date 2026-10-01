import datetime
import zipfile
from typing import Dict, Optional

from aardwolf.extensions.RDPEFS.provider import (
	DriveDirCursor,
	DriveError,
	DriveHandle,
	DriveProvider,
	FileStat,
	VolumeInfo,
	join_rdp_path,
	match_pattern,
	split_rdp_path,
)
from aardwolf.extensions.RDPEFS.wintypes.attributes import FileAttributes
from aardwolf.extensions.RDPEFS.wintypes.create import CreateAction, CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


class _ZipNode:
	def __init__(self, name: str, is_dir: bool, member: Optional[str] = None, info: Optional[zipfile.ZipInfo] = None):
		self.name = name
		self.is_dir = is_dir
		self.member = member
		self.info = info
		self.children: Dict[str, '_ZipNode'] = {}

	def stat(self) -> FileStat:
		size = 0
		mtime = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
		if self.info is not None:
			size = self.info.file_size
			try:
				mtime = datetime.datetime(*self.info.date_time)
			except ValueError:
				pass
		attrs = FileAttributes.FILE_ATTRIBUTE_DIRECTORY if self.is_dir else FileAttributes.FILE_ATTRIBUTE_NORMAL
		if not self.is_dir:
			attrs |= FileAttributes.FILE_ATTRIBUTE_READONLY
		return FileStat(
			name=self.name,
			is_dir=self.is_dir,
			size=0 if self.is_dir else size,
			allocation_size=0 if self.is_dir else size,
			attributes=attrs,
			creation_time=mtime,
			last_access_time=mtime,
			last_write_time=mtime,
			change_time=mtime,
			file_id=hash(self.member or self.name) & 0x7FFFFFFFFFFFFFFF,
		)


class ZipDriveProvider(DriveProvider):
	def __init__(self, name: str, archive, label: str = ''):
		super().__init__(name, label=label, readonly=True)
		if isinstance(archive, zipfile.ZipFile):
			self._zip = archive
		else:
			self._zip = zipfile.ZipFile(archive, 'r')
		self._root = _ZipNode('', True)
		self._build_tree()

	def _ensure_dir(self, parts):
		node = self._root
		for part in parts:
			key = part.lower()
			child = node.children.get(key)
			if child is None:
				child = _ZipNode(part, True)
				node.children[key] = child
			node = child
		return node

	def _build_tree(self) -> None:
		for info in self._zip.infolist():
			parts = split_rdp_path(info.filename)
			if not parts:
				continue
			is_dir = info.is_dir() or info.filename.endswith('/')
			if is_dir:
				self._ensure_dir(parts)
				continue
			parent = self._ensure_dir(parts[:-1])
			leaf = _ZipNode(parts[-1], False, member=info.filename, info=info)
			parent.children[parts[-1].lower()] = leaf

	def _lookup(self, parts):
		node = self._root
		for part in parts:
			child = node.children.get(part.lower())
			if child is None:
				return None
			node = child
		return node

	async def volume(self) -> VolumeInfo:
		total = sum(info.file_size for info in self._zip.infolist())
		return VolumeInfo(
			label=self.label,
			serial=0x5A495000,
			total_units=max(total, 1),
			available_units=0,
			sectors_per_unit=1,
			bytes_per_sector=1,
			fs_name='FAT32',
		)

	async def create(self, path, access, disposition, options) -> DriveHandle:
		parts = split_rdp_path(path)
		want_dir = bool(options & CreateOptions.FILE_DIRECTORY_FILE)
		want_file = bool(options & CreateOptions.FILE_NON_DIRECTORY_FILE)
		node = self._lookup(parts)
		if node is None:
			if disposition in (CreateDisposition.FILE_OPEN, CreateDisposition.FILE_OVERWRITE):
				raise DriveError(NTStatus.OBJECT_NAME_NOT_FOUND)
			raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)
		if want_dir and not node.is_dir:
			raise DriveError(NTStatus.NOT_A_DIRECTORY)
		if want_file and node.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		if disposition == CreateDisposition.FILE_CREATE:
			raise DriveError(NTStatus.OBJECT_NAME_COLLISION)
		if disposition in (CreateDisposition.FILE_SUPERSEDE, CreateDisposition.FILE_OVERWRITE, CreateDisposition.FILE_OVERWRITE_IF):
			raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)
		handle = DriveHandle(
			path=join_rdp_path(parts),
			is_dir=node.is_dir,
			stat=node.stat(),
			backend=node,
		)
		handle.action = CreateAction.FILE_OPENED
		return handle

	async def close(self, handle: DriveHandle) -> None:
		return None

	async def read(self, handle: DriveHandle, offset: int, length: int) -> bytes:
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		member = handle.backend.member
		data = self._zip.read(member)
		if offset >= len(data):
			return b''
		return data[offset:offset + length]

	async def write(self, handle: DriveHandle, offset: int, data: bytes) -> int:
		raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)

	async def query_info(self, handle: DriveHandle) -> FileStat:
		handle.stat = handle.backend.stat()
		return handle.stat

	async def set_end_of_file(self, handle: DriveHandle, size: int) -> None:
		raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)

	async def set_disposition(self, handle: DriveHandle, delete_pending: bool) -> None:
		if delete_pending:
			raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)

	async def rename(self, handle: DriveHandle, new_path: str, replace_if_exists: bool) -> None:
		raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)

	async def query_directory(self, handle: DriveHandle, pattern: str) -> DriveDirCursor:
		if not handle.is_dir:
			raise DriveError(NTStatus.NOT_A_DIRECTORY)
		entries = [child.stat() for child in handle.backend.children.values() if match_pattern(child.name, pattern)]
		entries.sort(key=lambda item: item.name.lower())
		return DriveDirCursor(entries)
