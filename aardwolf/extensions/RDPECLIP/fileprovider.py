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
