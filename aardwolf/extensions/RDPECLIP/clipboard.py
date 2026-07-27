import os
import asyncio
import inspect
from pathlib import Path, PurePath
from typing import Callable, Dict, Iterable, Optional, List, Protocol

from aardwolf.commons.queuedata.clipboard import RDP_CLIPBOARD_DATA, RDP_CLIPBOARD_DATA_FILELIST, RDP_CLIPBOARD_DATA_TXT
from aardwolf.extensions.RDPECLIP.fileprovider import FileProvider, FilesystemFileProvider, FileSink, FilesystemFileSink
from aardwolf.extensions.RDPECLIP.protocol.filecontentsrequest import FILECONTENTS_FLAG
from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT
from aardwolf.extensions.RDPECLIP.protocol.formatdataresponse import CLIPRDR_FILELIST, CLIPRDR_FILEDESCRIPTOR, FILE_ATTRIBUTE, FD_FLAGS

# default chunk size for FILECONTENTS_RANGE requests; kept conservative since
# some servers cap cbRequested
DOWNLOAD_CHUNK_SIZE = 64 * 1024


class ClipboardHandler(Protocol):
	async def on_copy(self, data:RDP_CLIPBOARD_DATA):
		pass

	async def request_file_contents(self, lindex:int, dwFlags:FILECONTENTS_FLAG, nPosition:int = 0, cbRequested:int = 0):
		pass


class Clipboard:
	def __init__(self, file_provider:FileProvider = None, file_sink:FileSink = None):
		self._file_provider = FilesystemFileProvider() if file_provider is None else file_provider
		self._file_sink = FilesystemFileSink(os.getcwd()) if file_sink is None else file_sink
		self._formats:Dict[int, str] = {f.value : '' for f in CLIPBRD_FORMAT if f != CLIPBRD_FORMAT.UNKNOWN}
		self.data:Optional[RDP_CLIPBOARD_DATA] = None
		self._next_format_id = 0xC000
		self._handlers:List[ClipboardHandler] = []
		self.file_copy_id = self.register_format('FileGroupDescriptorW')
		self._file_paths: List[PurePath] = []
		# files advertised by the server, available to download on demand
		self._remote_file_list: List[CLIPRDR_FILEDESCRIPTOR] = []

	@property
	def formats(self) -> Dict[int, str]:
		return self._formats

	def clone_for_connection(self):
		clipboard = Clipboard(
			file_provider=self._file_provider,
			file_sink=self._file_sink,
		)
		clipboard._formats = dict(self._formats)
		clipboard._next_format_id = self._next_format_id
		clipboard.file_copy_id = self.file_copy_id
		return clipboard

	def register_format(self, format_name:str) -> int:
		for k, v in self._formats.items():
			if v == format_name:
				return k

		format_id = self._get_format_id()
		self._formats[format_id] = format_name
		return format_id

	def register_handler(self, handler:ClipboardHandler):
		self._handlers.append(handler)

	def unregister_handler(self, handler:ClipboardHandler):
		if handler in self._handlers:
			self._handlers.remove(handler)

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

	def set_remote_file_list(self, filelist:CLIPRDR_FILELIST):
		# Download: store the file descriptor list advertised by the server.
		# The array index doubles as the lindex used in CB_FILECONTENTS_REQUEST.
		self._remote_file_list = list(filelist.fileDescriptorArray)

	def get_remote_file_list(self) -> List[CLIPRDR_FILEDESCRIPTOR]:
		# Download: descriptors (names + sizes) the caller can choose to download
		return self._remote_file_list

	def set_file_sink(self, file_sink:FileSink):
		# Download: replace the destination that download_file() streams into
		self._file_sink = file_sink

	def set_download_directory(self, path:str):
		# Download: convenience wrapper that points downloads at a local folder
		self._file_sink = FilesystemFileSink(path)

	def _get_file_request_handler(self) -> Optional[ClipboardHandler]:
		for handler in self._handlers:
			if hasattr(handler, 'request_file_contents'):
				return handler
		return None

	def _is_directory(self, descriptor:CLIPRDR_FILEDESCRIPTOR) -> bool:
		# only trust fileAttributes if the descriptor says they are valid
		if FD_FLAGS.ATTRIBUTES not in descriptor.flags:
			return False
		return FILE_ATTRIBUTE.DIRECTORY in descriptor.fileAttributes

	async def _emit_progress(self, progress_callback, downloaded:int, total:int):
		result = progress_callback(downloaded, total)
		if inspect.isawaitable(result):
			await result

	async def download_file(self, index:int, dest:str = None, progress_callback:Callable[[int, int], None] = None,
							cancel_event:asyncio.Event = None, max_size:int = None) -> int:
		# Download: fetch a single remote file (by its index in the remote file
		# list) from the server, streaming it to the configured FileSink.
		#
		# When dest is None the server-supplied file name is used (the sink
		# sanitizes it). Returns the number of bytes written.
		#
		# progress_callback: optional sync/async callable invoked as
		#   (downloaded_bytes, total_bytes) before the first chunk and after
		#   each chunk so the caller can render progress.
		# cancel_event: optional asyncio.Event; when set, the download stops at
		#   the next chunk boundary, the partial file is discarded and
		#   asyncio.CancelledError is raised.
		# max_size: optional cap; if the server reports a larger size the
		#   download is refused before any data is fetched.
		if index < 0 or index >= len(self._remote_file_list):
			raise IndexError('No remote file at index %s' % index)

		descriptor = self._remote_file_list[index]
		name = dest if dest is not None else descriptor.fileName

		if self._is_directory(descriptor):
			# directories are created implicitly when their child files are
			# written, so there is nothing to fetch here
			return 0

		handler = self._get_file_request_handler()
		if handler is None:
			raise RuntimeError('No clipboard channel available to request file contents')

		size = await handler.request_file_contents(index, FILECONTENTS_FLAG.FILECONTENTS_SIZE)
		if max_size is not None and size > max_size:
			raise ValueError('Remote file size %d exceeds max_size %d' % (size, max_size))

		await self._file_sink.prepare(name, size)
		pos = 0
		try:
			if progress_callback is not None:
				await self._emit_progress(progress_callback, pos, size)
			while pos < size:
				if cancel_event is not None and cancel_event.is_set():
					raise asyncio.CancelledError()
				chunk = min(DOWNLOAD_CHUNK_SIZE, size - pos)
				data = await handler.request_file_contents(index, FILECONTENTS_FLAG.FILECONTENTS_RANGE, pos, chunk)
				if not data:
					# server returned no data; avoid an infinite loop
					break
				await self._file_sink.write_file_data(name, pos, data)
				pos += len(data)
				if progress_callback is not None:
					await self._emit_progress(progress_callback, pos, size)
			await self._file_sink.finalize(name)
			return pos
		except BaseException:
			# covers cancellation (asyncio.CancelledError) and any transport
			# error: discard the partial file and propagate
			await self._file_sink.abort(name)
			raise

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
		for handler in list(self._handlers):
			await handler.on_copy(data)
