from pathlib import Path, PurePath
from typing import Dict, Iterable, Optional, List, Protocol

from aardwolf.commons.queuedata.clipboard import RDP_CLIPBOARD_DATA, RDP_CLIPBOARD_DATA_FILELIST, RDP_CLIPBOARD_DATA_TXT
from aardwolf.extensions.RDPECLIP.fileprovider import FileProvider, FilesystemFileProvider
from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT
from aardwolf.extensions.RDPECLIP.protocol.formatdataresponse import CLIPRDR_FILELIST, CLIPRDR_FILEDESCRIPTOR, FILE_ATTRIBUTE, FD_FLAGS

class ClipboardHandler(Protocol):
	async def on_copy(self, data:RDP_CLIPBOARD_DATA):
		pass


class Clipboard:
	def __init__(self, file_provider:FileProvider = None):
		self._file_provider = FilesystemFileProvider() if file_provider is None else file_provider
		self._formats:Dict[int, str] = {f.value : '' for f in CLIPBRD_FORMAT if f != CLIPBRD_FORMAT.UNKNOWN}
		self.data:Optional[RDP_CLIPBOARD_DATA] = None
		self._next_format_id = 0xC000
		self._handlers:List[ClipboardHandler] = []
		self.file_copy_id = self.register_format('FileGroupDescriptorW')
		self._file_paths: List[PurePath] = []

	@property
	def formats(self) -> Dict[int, str]:
		return self._formats

	def register_format(self, format_name:str) -> int:
		for k, v in self._formats.items():
			if v == format_name:
				return k

		format_id = self._get_format_id()
		self._formats[format_id] = format_name
		return format_id

	def register_handler(self, handler:ClipboardHandler):
		self._handlers.append(handler)

	def get_file_size(self, index:int) -> int:
		file_path = self._get_file_at_index(index)
		if file_path is None:
			return 0

		return self._file_provider.get_file_size(str(file_path))

	def get_file_data(self, index:int, start:int, count:int) -> bytes:
		file_path = self._get_file_at_index(index)
		if file_path is None:
			return b''

		return self._file_provider.get_file_data(str(file_path), start, count)

	def _get_file_at_index(self, index:int) -> Optional[PurePath]:
		if index < len(self._file_paths):
			return self._file_paths[index]
			
		return None

	def _get_format_id(self) -> int:
		format_id = self._next_format_id
		self._next_format_id += 1
		return format_id
	
	async def set_current_clipboard_files(self, files:Iterable[PurePath]):
		file_list = CLIPRDR_FILELIST()
		for f in files:
			self._file_paths.append(f)

			path = Path(f)
			file_descriptor = self._create_filedescriptor(path)
			file_list.fileDescriptorArray.append(file_descriptor)
			self._recurse_path(path, file_list.fileDescriptorArray)

		data = RDP_CLIPBOARD_DATA_FILELIST(data=file_list, datatype=self.file_copy_id)
		await self.set_data(data)

	def _create_filedescriptor(self, path:Path, depth:int = 0) -> CLIPRDR_FILEDESCRIPTOR:
		file = CLIPRDR_FILEDESCRIPTOR()
		file.flags = FD_FLAGS.ATTRIBUTES
		attributes = FILE_ATTRIBUTE.DIRECTORY if path.is_dir() else FILE_ATTRIBUTE.NORMAL
		file.fileAttributes = attributes
		file.fileName = str(Path(*path.parts[-(1 + depth):]))
		return file

	def _recurse_path(self, path:Path, file_descriptors:List[CLIPRDR_FILEDESCRIPTOR], depth:int = 0):
		if not path.is_dir():
			return
		
		for p in path.iterdir():
			self._file_paths.append(p)
			file_descriptor = self._create_filedescriptor(p, depth + 1)
			file_descriptors.append(file_descriptor)
			self._recurse_path(p, file_descriptors, depth + 1)

	async def get_current_clipboard_text(self) -> str:
		if self.data is None or self.data.datatype not in [CLIPBRD_FORMAT.CF_UNICODETEXT]:
			return ''
		return str(self.data.data)

	async def set_current_clipboard_text(self, text:str):
		data = RDP_CLIPBOARD_DATA_TXT(data=text, datatype=CLIPBRD_FORMAT.CF_UNICODETEXT)
		await self.set_data(data)
				
	async def set_data(self, data:RDP_CLIPBOARD_DATA, force_refresh = True):
		if data == self.data and force_refresh is False:
			return

		if data.datatype != self.file_copy_id:
			self._file_paths = []

		self.data = data
		await self.notify_copy(data)

	async def notify_copy(self, data:RDP_CLIPBOARD_DATA):
		# Inform the channel of a copy
		for handler in self._handlers:
			await handler.on_copy(data)
