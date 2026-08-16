import datetime
import fnmatch
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Sequence

from aardwolf.extensions.RDPEFS.wintypes.attributes import FileAttributes
from aardwolf.extensions.RDPEFS.wintypes.create import CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.fileinfo import DirectoryEntry
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


class DriveError(Exception):
	def __init__(self, status: NTStatus, message: str = ''):
		self.status = status
		super().__init__(message or status.name)


@dataclass
class FileStat:
	name: str
	is_dir: bool
	size: int = 0
	allocation_size: int = 0
	attributes: FileAttributes = FileAttributes.FILE_ATTRIBUTE_NORMAL
	creation_time: Optional[datetime.datetime] = None
	last_access_time: Optional[datetime.datetime] = None
	last_write_time: Optional[datetime.datetime] = None
	change_time: Optional[datetime.datetime] = None
	file_id: int = 0
	delete_pending: bool = False

	def to_directory_entry(self) -> DirectoryEntry:
		attrs = self.attributes
		if self.is_dir:
			attrs |= FileAttributes.FILE_ATTRIBUTE_DIRECTORY
		return DirectoryEntry(
			name=self.name,
			is_dir=self.is_dir,
			size=self.size,
			allocation_size=self.allocation_size or self.size,
			attributes=attrs,
			creation_time=self.creation_time,
			last_access_time=self.last_access_time,
			last_write_time=self.last_write_time,
			change_time=self.change_time,
			file_id=self.file_id,
		)


@dataclass
class VolumeInfo:
	label: str = ''
	serial: int = 0
	total_units: int = 1024
	available_units: int = 1024
	sectors_per_unit: int = 1
	bytes_per_sector: int = 512
	fs_name: str = 'FAT32'


@dataclass
class DriveHandle:
	path: str
	is_dir: bool
	stat: FileStat
	delete_on_close: bool = False
	cursor: Optional['DriveDirCursor'] = None
	backend: object = None


class DriveDirCursor:
	def __init__(self, entries: Sequence[FileStat]):
		self._entries = list(entries)
		self._index = 0

	def reset(self, entries: Optional[Sequence[FileStat]] = None) -> None:
		if entries is not None:
			self._entries = list(entries)
		self._index = 0

	def next(self, count: Optional[int] = None) -> List[FileStat]:
		if self._index >= len(self._entries):
			return []
		if count is None or count <= 0:
			chunk = self._entries[self._index:]
			self._index = len(self._entries)
			return chunk
		chunk = self._entries[self._index:self._index + count]
		self._index += len(chunk)
		return chunk


def split_rdp_path(path: str) -> List[str]:
	if path is None:
		return []
	normalized = path.replace('/', '\\')
	parts = [part for part in normalized.split('\\') if part not in ('', '.')]
	if any(part == '..' for part in parts):
		raise DriveError(NTStatus.OBJECT_NAME_INVALID)
	return parts


def join_rdp_path(parts: Sequence[str]) -> str:
	if not parts:
		return '\\'
	return '\\' + '\\'.join(parts)


def match_pattern(name: str, pattern: str) -> bool:
	if not pattern or pattern in ('*', '*.*'):
		return True
	return fnmatch.fnmatch(name.lower(), pattern.lower())


def validate_dos_name(name: str) -> str:
	if not name or len(name) > 8:
		raise ValueError('Drive DosName must be 1-8 ASCII characters, got %r' % name)
	try:
		name.encode('ascii')
	except UnicodeEncodeError as exc:
		raise ValueError('Drive DosName must be ASCII: %r' % name) from exc
	if name.upper() != name and any(ch.islower() for ch in name):
		pass
	return name


class DriveProvider(ABC):
	def __init__(self, name: str, label: str = '', readonly: bool = False):
		self.name = validate_dos_name(name)
		self.label = label or self.name
		self.readonly = readonly

	@abstractmethod
	async def volume(self) -> VolumeInfo:
		raise NotImplementedError()

	@abstractmethod
	async def create(
			self,
			path: str,
			access: int,
			disposition: CreateDisposition,
			options: CreateOptions) -> DriveHandle:
		raise NotImplementedError()

	@abstractmethod
	async def close(self, handle: DriveHandle) -> None:
		raise NotImplementedError()

	@abstractmethod
	async def read(self, handle: DriveHandle, offset: int, length: int) -> bytes:
		raise NotImplementedError()

	@abstractmethod
	async def write(self, handle: DriveHandle, offset: int, data: bytes) -> int:
		raise NotImplementedError()

	@abstractmethod
	async def query_info(self, handle: DriveHandle) -> FileStat:
		raise NotImplementedError()

	@abstractmethod
	async def set_end_of_file(self, handle: DriveHandle, size: int) -> None:
		raise NotImplementedError()

	@abstractmethod
	async def set_disposition(self, handle: DriveHandle, delete_pending: bool) -> None:
		raise NotImplementedError()

	@abstractmethod
	async def rename(self, handle: DriveHandle, new_path: str, replace_if_exists: bool) -> None:
		raise NotImplementedError()

	@abstractmethod
	async def query_directory(self, handle: DriveHandle, pattern: str) -> DriveDirCursor:
		raise NotImplementedError()


def require_write(provider: DriveProvider) -> None:
	if provider.readonly:
		raise DriveError(NTStatus.MEDIA_WRITE_PROTECTED)
