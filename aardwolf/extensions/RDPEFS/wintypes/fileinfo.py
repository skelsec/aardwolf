import datetime
from typing import List, Optional

from aardwolf.extensions.RDPEFS.wintypes.attributes import FileAttributes
from aardwolf.extensions.RDPEFS.wintypes.filetime import FILETIME


def _align8(data: bytes) -> bytes:
	pad = (8 - (len(data) % 8)) % 8
	return data + (b'\x00' * pad)


def _ft(dt: Optional[datetime.datetime]) -> bytes:
	if dt is None:
		return b'\x00' * 8
	return FILETIME.from_datetime(dt).to_bytes()


class FileBasicInformation:
	def __init__(
			self,
			creation_time=None,
			last_access_time=None,
			last_write_time=None,
			change_time=None,
			attributes: FileAttributes = FileAttributes.FILE_ATTRIBUTE_NORMAL):
		self.creation_time = creation_time
		self.last_access_time = last_access_time
		self.last_write_time = last_write_time
		self.change_time = change_time
		self.attributes = attributes

	def to_bytes(self) -> bytes:
		t = _ft(self.creation_time)
		t += _ft(self.last_access_time)
		t += _ft(self.last_write_time)
		t += _ft(self.change_time)
		t += int(self.attributes).to_bytes(4, 'little', signed=False)
		t += b'\x00' * 4
		return t


class FileStandardInformation:
	def __init__(self, allocation_size=0, end_of_file=0, number_of_links=1, delete_pending=False, directory=False):
		self.allocation_size = allocation_size
		self.end_of_file = end_of_file
		self.number_of_links = number_of_links
		self.delete_pending = delete_pending
		self.directory = directory

	def to_bytes(self) -> bytes:
		t = int(self.allocation_size).to_bytes(8, 'little', signed=True)
		t += int(self.end_of_file).to_bytes(8, 'little', signed=True)
		t += int(self.number_of_links).to_bytes(4, 'little', signed=False)
		t += bytes([1 if self.delete_pending else 0, 1 if self.directory else 0, 0, 0])
		return t


class FileEndOfFileInformation:
	def __init__(self, end_of_file=0):
		self.end_of_file = end_of_file

	@staticmethod
	def from_bytes(data: bytes) -> 'FileEndOfFileInformation':
		return FileEndOfFileInformation(int.from_bytes(data[:8], 'little', signed=True))

	def to_bytes(self) -> bytes:
		return int(self.end_of_file).to_bytes(8, 'little', signed=True)


class FileDispositionInformation:
	def __init__(self, delete_pending=False):
		self.delete_pending = delete_pending

	@staticmethod
	def from_bytes(data: bytes) -> 'FileDispositionInformation':
		return FileDispositionInformation(bool(data[0]) if data else False)

	def to_bytes(self) -> bytes:
		return bytes([1 if self.delete_pending else 0])


class FileRenameInformation:
	def __init__(self, replace_if_exists=False, file_name=''):
		self.replace_if_exists = replace_if_exists
		self.file_name = file_name

	@staticmethod
	def from_bytes(data: bytes) -> 'FileRenameInformation':
		replace = bool(data[0]) if data else False
		# MS-FSCC FileRenameInformation: ReplaceIfExists(1) Reserved(7) RootDirectory(8) FileNameLength(4) FileName
		if len(data) >= 20:
			name_len = int.from_bytes(data[16:20], 'little', signed=False)
			name = data[20:20 + name_len].decode('utf-16-le')
			return FileRenameInformation(replace, name)
		# shorter RDPDR variant seen in the wild: ReplaceIfExists(1) RootDirectory(4) FileNameLength(4) FileName
		if len(data) >= 9:
			name_len = int.from_bytes(data[5:9], 'little', signed=False)
			name = data[9:9 + name_len].decode('utf-16-le')
			return FileRenameInformation(replace, name)
		return FileRenameInformation(replace, '')

	def to_bytes(self) -> bytes:
		name = self.file_name.encode('utf-16-le')
		t = bytes([1 if self.replace_if_exists else 0])
		t += b'\x00' * 7
		t += b'\x00' * 8
		t += len(name).to_bytes(4, 'little', signed=False)
		t += name
		return t


class FileNameInformation:
	def __init__(self, file_name=''):
		self.file_name = file_name

	def to_bytes(self) -> bytes:
		name = self.file_name.encode('utf-16-le')
		return len(name).to_bytes(4, 'little', signed=False) + name


class FileInternalInformation:
	def __init__(self, index_number=0):
		self.index_number = index_number

	def to_bytes(self) -> bytes:
		return int(self.index_number).to_bytes(8, 'little', signed=True)


def pack_directory_entries(entries: List['DirectoryEntry'], info_class) -> bytes:
	from aardwolf.extensions.RDPEFS.wintypes.fileinfoclass import FileInfoClass

	blobs = [entry.to_bytes(info_class) for entry in entries]
	if not blobs:
		return b''
	out = b''
	for i, blob in enumerate(blobs):
		if i + 1 < len(blobs):
			aligned = _align8(blob)
			aligned = len(aligned).to_bytes(4, 'little', signed=False) + aligned[4:]
			out += aligned
		else:
			out += b'\x00\x00\x00\x00' + blob[4:]
	return out


class DirectoryEntry:
	def __init__(
			self,
			name: str,
			is_dir: bool,
			size: int = 0,
			allocation_size: int = 0,
			attributes: FileAttributes = FileAttributes.FILE_ATTRIBUTE_NORMAL,
			creation_time=None,
			last_access_time=None,
			last_write_time=None,
			change_time=None,
			file_id: int = 0):
		self.name = name
		self.is_dir = is_dir
		self.size = size
		self.allocation_size = allocation_size or size
		self.attributes = attributes
		self.creation_time = creation_time
		self.last_access_time = last_access_time
		self.last_write_time = last_write_time
		self.change_time = change_time
		self.file_id = file_id

	def to_bytes(self, info_class) -> bytes:
		from aardwolf.extensions.RDPEFS.wintypes.fileinfoclass import FileInfoClass

		name = self.name.encode('utf-16-le')
		fixed = b'\x00' * 4  # NextEntryOffset placeholder
		fixed += b'\x00' * 4  # FileIndex
		if info_class == FileInfoClass.FileNamesInformation:
			fixed += len(name).to_bytes(4, 'little', signed=False)
			return fixed + name

		fixed += _ft(self.creation_time)
		fixed += _ft(self.last_access_time)
		fixed += _ft(self.last_write_time)
		fixed += _ft(self.change_time)
		fixed += int(self.size).to_bytes(8, 'little', signed=True)
		fixed += int(self.allocation_size).to_bytes(8, 'little', signed=True)
		fixed += int(self.attributes).to_bytes(4, 'little', signed=False)
		fixed += len(name).to_bytes(4, 'little', signed=False)

		if info_class == FileInfoClass.FileDirectoryInformation:
			return fixed + name
		if info_class == FileInfoClass.FileFullDirectoryInformation:
			return fixed + (0).to_bytes(4, 'little', signed=False) + name
		if info_class == FileInfoClass.FileBothDirectoryInformation:
			return fixed + (0).to_bytes(4, 'little', signed=False) + bytes([0, 0]) + (b'\x00' * 24) + name
		if info_class == FileInfoClass.FileIdFullDirectoryInformation:
			return fixed + (0).to_bytes(4, 'little', signed=False) + int(self.file_id).to_bytes(8, 'little', signed=False) + name
		if info_class == FileInfoClass.FileIdBothDirectoryInformation:
			return (
				fixed
				+ (0).to_bytes(4, 'little', signed=False)
				+ bytes([0, 0])
				+ (b'\x00' * 24)
				+ b'\x00\x00'
				+ int(self.file_id).to_bytes(8, 'little', signed=False)
				+ name
			)
		return fixed + name
