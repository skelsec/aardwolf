import datetime
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
	require_write,
	split_rdp_path,
)
from aardwolf.extensions.RDPEFS.wintypes.attributes import FileAttributes
from aardwolf.extensions.RDPEFS.wintypes.create import CreateAction, CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


class _Node:
	def __init__(self, name: str, is_dir: bool, data: bytes = b''):
		self.name = name
		self.is_dir = is_dir
		self.data = bytearray(data)
		self.children: Dict[str, '_Node'] = {}
		now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
		self.creation_time = now
		self.last_access_time = now
		self.last_write_time = now
		self.change_time = now
		self.file_id = id(self) & 0x7FFFFFFFFFFFFFFF

	def touch(self) -> None:
		now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
		self.last_write_time = now
		self.change_time = now

	def stat(self) -> FileStat:
		attrs = FileAttributes.FILE_ATTRIBUTE_DIRECTORY if self.is_dir else FileAttributes.FILE_ATTRIBUTE_NORMAL
		return FileStat(
			name=self.name,
			is_dir=self.is_dir,
			size=0 if self.is_dir else len(self.data),
			allocation_size=0 if self.is_dir else len(self.data),
			attributes=attrs,
			creation_time=self.creation_time,
			last_access_time=self.last_access_time,
			last_write_time=self.last_write_time,
			change_time=self.change_time,
			file_id=self.file_id,
		)


class MemoryDriveProvider(DriveProvider):
	def __init__(self, name: str, tree: Optional[Dict[str, bytes]] = None, label: str = '', readonly: bool = False):
		super().__init__(name, label=label, readonly=readonly)
		self._root = _Node('', True)
		if tree:
			for path, data in tree.items():
				self._seed(path, data)

	def _seed(self, path: str, data: bytes) -> None:
		parts = split_rdp_path(path)
		if not parts:
			return
		node = self._root
		for part in parts[:-1]:
			child = node.children.get(part.lower())
			if child is None:
				child = _Node(part, True)
				node.children[part.lower()] = child
			elif not child.is_dir:
				raise ValueError('Cannot seed file under a file: %s' % path)
			node = child
		leaf = _Node(parts[-1], False, data)
		node.children[parts[-1].lower()] = leaf

	def _lookup(self, parts):
		node = self._root
		for part in parts:
			child = node.children.get(part.lower())
			if child is None:
				return None
			node = child
		return node

	def _parent(self, parts):
		if not parts:
			return None, self._root
		parent = self._lookup(parts[:-1])
		return parts[-1], parent

	async def volume(self) -> VolumeInfo:
		used = 0

		def walk(node: _Node) -> None:
			nonlocal used
			if node.is_dir:
				for child in node.children.values():
					walk(child)
			else:
				used += len(node.data)

		walk(self._root)
		total = max(used + 1024 * 1024, 1024 * 1024)
		return VolumeInfo(
			label=self.label,
			serial=0x4D454D00,
			total_units=total,
			available_units=total - used,
			sectors_per_unit=1,
			bytes_per_sector=1,
			fs_name='FAT32',
		)

	async def create(self, path, access, disposition, options) -> DriveHandle:
		parts = split_rdp_path(path)
		want_dir = bool(options & CreateOptions.FILE_DIRECTORY_FILE)
		want_file = bool(options & CreateOptions.FILE_NON_DIRECTORY_FILE)
		node = self._lookup(parts)
		action = CreateAction.FILE_OPENED

		if node is None:
			if disposition in (CreateDisposition.FILE_OPEN, CreateDisposition.FILE_OVERWRITE):
				raise DriveError(NTStatus.OBJECT_NAME_NOT_FOUND)
			require_write(self)
			name, parent = self._parent(parts)
			if parent is None or not parent.is_dir:
				raise DriveError(NTStatus.OBJECT_PATH_NOT_FOUND)
			if name is None:
				node = self._root
			else:
				node = _Node(name, want_dir or not want_file)
				parent.children[name.lower()] = node
				parent.touch()
			action = CreateAction.FILE_CREATED
		else:
			if want_dir and not node.is_dir:
				raise DriveError(NTStatus.NOT_A_DIRECTORY)
			if want_file and node.is_dir:
				raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
			if disposition == CreateDisposition.FILE_CREATE:
				raise DriveError(NTStatus.OBJECT_NAME_COLLISION)
			if disposition in (CreateDisposition.FILE_SUPERSEDE, CreateDisposition.FILE_OVERWRITE, CreateDisposition.FILE_OVERWRITE_IF):
				if node.is_dir:
					raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
				require_write(self)
				node.data = bytearray()
				node.touch()
				action = CreateAction.FILE_OVERWRITTEN if disposition != CreateDisposition.FILE_SUPERSEDE else CreateAction.FILE_SUPERSEDED

		handle = DriveHandle(
			path=join_rdp_path(parts),
			is_dir=node.is_dir,
			stat=node.stat(),
			delete_on_close=bool(options & CreateOptions.FILE_DELETE_ON_CLOSE),
			backend=node,
		)
		handle.stat.delete_pending = handle.delete_on_close
		handle.action = action
		return handle

	async def close(self, handle: DriveHandle) -> None:
		if handle.delete_on_close or handle.stat.delete_pending:
			await self._delete_node(handle)

	async def _delete_node(self, handle: DriveHandle) -> None:
		require_write(self)
		parts = split_rdp_path(handle.path)
		if not parts:
			raise DriveError(NTStatus.ACCESS_DENIED)
		name, parent = self._parent(parts)
		node = handle.backend
		if node.is_dir and node.children:
			raise DriveError(NTStatus.DIRECTORY_NOT_EMPTY)
		if parent is not None and name is not None:
			parent.children.pop(name.lower(), None)
			parent.touch()

	async def read(self, handle: DriveHandle, offset: int, length: int) -> bytes:
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		data = handle.backend.data
		if offset >= len(data):
			return b''
		return bytes(data[offset:offset + length])

	async def write(self, handle: DriveHandle, offset: int, data: bytes) -> int:
		require_write(self)
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		buf = handle.backend.data
		if offset > len(buf):
			buf.extend(b'\x00' * (offset - len(buf)))
		buf[offset:offset + len(data)] = data
		handle.backend.touch()
		handle.stat = handle.backend.stat()
		return len(data)

	async def query_info(self, handle: DriveHandle) -> FileStat:
		stat = handle.backend.stat()
		stat.delete_pending = handle.delete_on_close or handle.stat.delete_pending
		handle.stat = stat
		return stat

	async def set_end_of_file(self, handle: DriveHandle, size: int) -> None:
		require_write(self)
		if handle.is_dir:
			raise DriveError(NTStatus.FILE_IS_A_DIRECTORY)
		buf = handle.backend.data
		if size < len(buf):
			del buf[size:]
		elif size > len(buf):
			buf.extend(b'\x00' * (size - len(buf)))
		handle.backend.touch()
		handle.stat = handle.backend.stat()

	async def set_disposition(self, handle: DriveHandle, delete_pending: bool) -> None:
		if delete_pending:
			require_write(self)
		handle.delete_on_close = delete_pending
		handle.stat.delete_pending = delete_pending

	async def rename(self, handle: DriveHandle, new_path: str, replace_if_exists: bool) -> None:
		require_write(self)
		parts = split_rdp_path(new_path)
		if not parts:
			raise DriveError(NTStatus.OBJECT_NAME_INVALID)
		existing = self._lookup(parts)
		if existing is not None:
			if not replace_if_exists:
				raise DriveError(NTStatus.OBJECT_NAME_COLLISION)
			if existing.is_dir and existing.children:
				raise DriveError(NTStatus.DIRECTORY_NOT_EMPTY)
		old_parts = split_rdp_path(handle.path)
		old_name, old_parent = self._parent(old_parts)
		new_name, new_parent = self._parent(parts)
		if old_parent is None or new_parent is None or not new_parent.is_dir:
			raise DriveError(NTStatus.OBJECT_PATH_NOT_FOUND)
		node = handle.backend
		if old_name is not None:
			old_parent.children.pop(old_name.lower(), None)
		node.name = new_name
		new_parent.children[new_name.lower()] = node
		handle.path = join_rdp_path(parts)
		old_parent.touch()
		new_parent.touch()

	async def query_directory(self, handle: DriveHandle, pattern: str) -> DriveDirCursor:
		if not handle.is_dir:
			raise DriveError(NTStatus.NOT_A_DIRECTORY)
		entries = [child.stat() for child in handle.backend.children.values() if match_pattern(child.name, pattern)]
		entries.sort(key=lambda item: item.name.lower())
		return DriveDirCursor(entries)
