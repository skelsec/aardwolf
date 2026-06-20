import os
import ntpath
from abc import ABC, abstractmethod
from os import lstat
from typing import Dict


class FileProvider(ABC):
	"""
	File access for the clipboard
	"""

	@abstractmethod
	def get_file_data(self, name:str, start:int, count:int) -> bytes:
		"""
		Read data from the file with the given name
		
		Args:
			name: Name of the file from which to read
			start: Offset from the beginning of the file, in bytes
			count: Maximum number of bytes to read
		Returns:
			The file data
		"""
		pass

	@abstractmethod
	def get_file_size(self, name:str) -> int:
		"""
		Get the size of the file with the given name

		Args:
			name: Name of the file
		Returns:
			The file size, in bytes
		"""
		pass


class FilesystemFileProvider(FileProvider):
	"""
	Provides file data to the clipboard
	"""

	def get_file_data(self, name:str, start:int, count:int) -> bytes:
		with open(name, 'rb') as f:
			f.seek(start)
			return f.read(count)
		
	def get_file_size(self, name:str) -> int:
		stat = lstat(name)
		return stat.st_size


class FileSink(ABC):
	"""
	Destination for files downloaded from the server via the clipboard.

	The interface is async so implementations can be backed by network or
	streaming storage. Server-supplied file names are untrusted, so each
	implementation is responsible for sanitizing the `name` it receives.
	"""

	@abstractmethod
	async def prepare(self, name:str, size:int) -> None:
		"""
		Called once before any data is written for the given file.

		Args:
			name: Server-supplied name of the file
			size: Total size of the file, in bytes
		"""
		pass

	@abstractmethod
	async def write_file_data(self, name:str, start:int, data:bytes) -> None:
		"""
		Write a chunk of data to the file with the given name.

		Args:
			name: Server-supplied name of the file
			start: Offset from the beginning of the file, in bytes
			data: The chunk of data to write
		"""
		pass

	@abstractmethod
	async def finalize(self, name:str) -> None:
		"""
		Called once after all data has been written for the given file.

		Args:
			name: Server-supplied name of the file
		"""
		pass

	async def abort(self, name:str) -> None:
		"""
		Called when a download is cancelled or fails partway through. The
		default just delegates to finalize(); filesystem-backed sinks override
		this to discard the partial file. Implementing it is optional.

		Args:
			name: Server-supplied name of the file
		"""
		await self.finalize(name)


class FilesystemFileSink(FileSink):
	"""
	Writes downloaded files to the local filesystem, confined to base_dir.

	Server-supplied names are sanitized and the resolved target is required to
	stay inside base_dir, defeating path traversal (`..`, absolute paths and
	Windows drive/UNC prefixes).
	"""

	def __init__(self, base_dir:str):
		self._base = os.path.realpath(base_dir)
		# open file handles kept alive between prepare() and finalize()/abort()
		# so large transfers don't reopen the file on every chunk
		self._handles:Dict[str, object] = {}

	def _safe_path(self, name:str) -> str:
		# RDP descriptors use Windows separators even on POSIX hosts; normalize
		# them so a server's "subdir\\file" becomes a nested path under base_dir.
		rel = name.replace('\\', '/')
		# strip drive letters (C:) and UNC (\\host\share) prefixes
		rel = ntpath.splitdrive(rel)[1]
		rel = rel.replace('\\', '/').lstrip('/')
		target = os.path.realpath(os.path.join(self._base, rel))
		if target != self._base and not target.startswith(self._base + os.sep):
			raise ValueError('Refusing path traversal outside base_dir: %r' % name)
		parent = os.path.dirname(target)
		if parent:
			os.makedirs(parent, exist_ok=True)
		return target

	async def prepare(self, name:str, size:int) -> None:
		# create/truncate the file and keep the handle open for the transfer.
		# we deliberately do NOT pre-truncate to `size` to avoid allocating a
		# huge (possibly sparse) file up front for very large downloads.
		path = self._safe_path(name)
		self._handles[name] = open(path, 'wb')

	async def write_file_data(self, name:str, start:int, data:bytes) -> None:
		f = self._handles.get(name)
		if f is None:
			# allow random-access writes without a prior prepare()
			f = open(self._safe_path(name), 'r+b')
			self._handles[name] = f
		f.seek(start)
		f.write(data)

	async def finalize(self, name:str) -> None:
		f = self._handles.pop(name, None)
		if f is not None:
			f.close()

	async def abort(self, name:str) -> None:
		f = self._handles.pop(name, None)
		if f is not None:
			path = f.name
			f.close()
			try:
				os.remove(path)
			except OSError:
				pass
