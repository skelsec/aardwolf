import datetime
import os
from pathlib import Path
from aardwolf.extensions.RDPEFS.provider import (
	DriveDirCursor,
	DriveError,
	DriveHandle,
	DriveProvider,
	FileStat,
	VolumeInfo,
	join_rdp_path,
	match_pattern,
	require_write,
	split_rdp_path,
)
from aardwolf.extensions.RDPEFS.wintypes.attributes import FileAttributes
from aardwolf.extensions.RDPEFS.wintypes.create import CreateAction, CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


def _to_datetime(timestamp: float) -> datetime.datetime:
	try:
		return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).replace(tzinfo=None)
	except (OverflowError, OSError, ValueError):
		return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class FilesystemDriveProvider(DriveProvider):
	def __init__(self, name: str, root, label: str = '', readonly: bool = False):
		super().__init__(name, label=label, readonly=readonly)
		self.root = Path(root).resolve()
		if not self.root.is_dir():
			raise ValueError('Filesystem drive root is not a directory: %s' % self.root)

	def _resolve(self, parts):
		current = self.root
		for part in parts:
			if part in ('', '.', '..'):
				raise DriveError(NTStatus.OBJECT_NAME_INVALID)
			current = current / part
			if current.is_symlink():
				raise DriveError(NTStatus.ACCESS_DENIED)
		try:
			resolved = current.resolve(strict=False)
		except OSError as exc:
			raise DriveError(NTStatus.OBJECT_PATH_NOT_FOUND) from exc
		root = self.root
		if resolved != root and not str(resolved).startswith(str(root) + os.sep):
			raise DriveError(NTStatus.OBJECT_PATH_NOT_FOUND)
		return current

	def _stat_path(self, path: Path, display_name: str) -> FileStat:
		try:
			st = path.lstat()
		except FileNotFoundError as exc:
			raise DriveError(NTStatus.OBJECT_NAME_NOT_FOUND) from exc
		is_dir = path.is_dir() and not path.is_symlink()
		attrs = FileAttributes.FILE_ATTRIBUTE_DIRECTORY if is_dir else FileAttributes.FILE_ATTRIBUTE_NORMAL
		if path.is_symlink():
			attrs |= FileAttributes.FILE_ATTRIBUTE_REPARSE_POINT
		return FileStat(
			name=display_name if display_name else path.name,
			is_dir=is_dir,
			size=0 if is_dir else st.st_size,
			allocation_size=0 if is_dir else st.st_size,
			attributes=attrs,
			creation_time=_to_datetime(getattr(st, 'st_ctime', st.st_mtime)),
			last_access_time=_to_datetime(st.st_atime),
			last_write_time=_to_datetime(st.st_mtime),
			change_time=_to_datetime(st.st_mtime),
			file_id=getattr(st, 'st_ino', 0) & 0x7FFFFFFFFFFFFFFF,
		)

	async def volume(self) -> VolumeInfo:
		try:
			usage = os.statvfs(self.root)
			total = usage.f_blocks * usage.f_frsize
			free = usage.f_bavail * usage.f_frsize
			sector = usage.f_frsize or 512
		except (AttributeError, OSError):
			total = 1024 * 1024 * 1024
			free = total
			sector = 512
		return VolumeInfo(
			label=self.label,
			serial=0x46530000,
			total_units=max(total // sector, 1),
			available_units=max(free // sector, 0),
			sectors_per_unit=1,
			bytes_per_sector=sector,
			fs_name='FAT32',
		)

	async def create(self, path, access, disposition, options) -> DriveHandle:
		parts = split_rdp_path(path)
		target = self._resolve(parts)
		want_dir = bool(options & CreateOptions.FILE_DIRECTORY_FILE)
		want_file = bool(options & CreateOptions.FILE_NON_DIRECTORY_FILE)
		exists = target.exists()
		action = CreateAction.FILE_OPENED

		if not exists:
			if disposition in (CreateDisposition.FILE_OPEN, CreateDisposition.FILE_OVERWRITE):
				raise DriveError(NTStatus.OBJECT_NAME_NOT_FOUND)
			require_write(self)
			if not target.parent.exists():
				raise DriveError(NTStatus.OBJECT_PATH_NOT_FOUND)
			if want_dir or not want_file:
				target.mkdir()
			else:
				flags = os.O_CREAT | os.O_RDWR
				if hasattr(os, 'O_NOFOLLOW'):
					flags |= os.O_NOFOLLOW
				fd = os.open(target, flags, 0o644)
				os.close(fd)
			action = CreateAction.FILE_CREATED
		else:
			if target.is_symlink():
				raise DriveError(NTStatus.ACCESS_DENIED)
			is_dir = target.is_dir()
			if want_dir and not is_dir:
				raise DriveError(NTStatus.NOT_A_DIRECTORY)
			if want_file and is_dir:
				raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
			if disposition == CreateDisposition.FILE_CREATE:
				raise DriveError(NTStatus.OBJECT_NAME_COLLISION)
			if disposition in (CreateDisposition.FILE_SUPERSEDE, CreateDisposition.FILE_OVERWRITE, CreateDisposition.FILE_OVERWRITE_IF):
				if is_dir:
					raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
				require_write(self)
				target.write_bytes(b'')
				action = CreateAction.FILE_OVERWRITTEN if disposition != CreateDisposition.FILE_SUPERSEDE else CreateAction.FILE_SUPERSEDED

		display = parts[-1] if parts else self.name
		stat = self._stat_path(target, display)
		handle = DriveHandle(
			path=join_rdp_path(parts),
			is_dir=stat.is_dir,
			stat=stat,
			delete_on_close=bool(options & CreateOptions.FILE_DELETE_ON_CLOSE),
			backend=target,
		)
		handle.action = action
		return handle

	async def close(self, handle: DriveHandle) -> None:
		if handle.delete_on_close or handle.stat.delete_pending:
			require_write(self)
			path = handle.backend
			try:
				if handle.is_dir:
					path.rmdir()
				else:
					path.unlink()
			except FileNotFoundError:
				pass
			except OSError as exc:
				raise DriveError(NTStatus.DIRECTORY_NOT_EMPTY) from exc

	async def read(self, handle: DriveHandle, offset: int, length: int) -> bytes:
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		path = handle.backend
		if path.is_symlink():
			raise DriveError(NTStatus.ACCESS_DENIED)
		with path.open('rb') as handle_fp:
			handle_fp.seek(offset)
			return handle_fp.read(length)

	async def write(self, handle: DriveHandle, offset: int, data: bytes) -> int:
		require_write(self)
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		path = handle.backend
		if path.is_symlink():
			raise DriveError(NTStatus.ACCESS_DENIED)
		with path.open('r+b') as handle_fp:
			handle_fp.seek(offset)
			handle_fp.write(data)
		handle.stat = self._stat_path(path, handle.stat.name)
		return len(data)

	async def query_info(self, handle: DriveHandle) -> FileStat:
		stat = self._stat_path(handle.backend, handle.stat.name)
		stat.delete_pending = handle.delete_on_close or handle.stat.delete_pending
		handle.stat = stat
		return stat

	async def set_end_of_file(self, handle: DriveHandle, size: int) -> None:
		require_write(self)
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		fd = os.open(handle.backend, os.O_RDWR | (os.O_NOFOLLOW if hasattr(os, 'O_NOFOLLOW') else 0))
		try:
			os.ftruncate(fd, size)
		finally:
			os.close(fd)
		handle.stat = self._stat_path(handle.backend, handle.stat.name)

	async def set_disposition(self, handle: DriveHandle, delete_pending: bool) -> None:
		if delete_pending:
			require_write(self)
		handle.delete_on_close = delete_pending
		handle.stat.delete_pending = delete_pending

	async def rename(self, handle: DriveHandle, new_path: str, replace_if_exists: bool) -> None:
		require_write(self)
		parts = split_rdp_path(new_path)
		dest = self._resolve(parts)
		if dest.exists():
			if not replace_if_exists:
				raise DriveError(NTStatus.OBJECT_NAME_COLLISION)
			if dest.is_dir():
				raise DriveError(NTStatus.OBJECT_NAME_COLLISION)
		if dest.is_symlink():
			raise DriveError(NTStatus.ACCESS_DENIED)
		handle.backend.rename(dest)
		handle.backend = dest
		handle.path = join_rdp_path(parts)
		handle.stat = self._stat_path(dest, parts[-1] if parts else dest.name)

	async def query_directory(self, handle: DriveHandle, pattern: str) -> DriveDirCursor:
		if not handle.is_dir:
			raise DriveError(NTStatus.NOT_A_DIRECTORY)
		entries = []
		try:
			children = list(handle.backend.iterdir())
		except OSError as exc:
			raise DriveError(NTStatus.ACCESS_DENIED) from exc
		for child in children:
			if child.is_symlink():
				continue
			if not match_pattern(child.name, pattern):
				continue
			entries.append(self._stat_path(child, child.name))
		entries.sort(key=lambda item: item.name.lower())
		return DriveDirCursor(entries)
