
import io
import enum

# https://docs.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats?redirectedfrom=MSDN
class CLIPBRD_FORMAT(enum.Enum):
	UNKNOWN = 0xFFFF
	CF_BITMAP = 2 #A handle to a bitmap (HBITMAP).
	CF_DIB = 8 #	A memory object containing a BITMAPINFO structure followed by the bitmap bits.
	CF_DIBV5 = 17 #A memory object containing a BITMAPV5HEADER structure followed by the bitmap color space information and the bitmap bits.
	CF_DIF = 5 #Software Arts' Data Interchange Format.
	CF_DSPBITMAP = 0x0082 #Bitmap display format associated with a private format. The hMem parameter must be a handle to data that can be displayed in bitmap format in lieu of the privately formatted data.
	CF_DSPENHMETAFILE = 0x008E #Enhanced metafile display format associated with a private format. The hMem parameter must be a handle to data that can be displayed in enhanced metafile format in lieu of the privately formatted data.
	CF_DSPMETAFILEPICT = 0x0083 #Metafile-picture display format associated with a private format. The hMem parameter must be a handle to data that can be displayed in metafile-picture format in lieu of the privately formatted data.
	CF_DSPTEXT = 0x0081 # Text display format associated with a private format. The hMem parameter must be a handle to data that can be displayed in text format in lieu of the privately formatted data.
	CF_ENHMETAFILE = 14 #A handle to an enhanced metafile (HENHMETAFILE).
	CF_GDIOBJFIRST = 0x0300 #Start of a range of integer values for application-defined GDI object clipboard formats. The end of the range is CF_GDIOBJLAST.
							#Handles associated with clipboard formats in this range are not automatically deleted using the GlobalFree function when the clipboard is emptied. Also, when using values in this range, the hMem parameter is not a handle to a GDI object, but is a handle allocated by the GlobalAlloc function with the GMEM_MOVEABLE flag.
	CF_GDIOBJLAST = 0x03FF #See CF_GDIOBJFIRST.
	CF_HDROP = 15 #A handle to type HDROP that identifies a list of files. An application can retrieve information about the files by passing the handle to the DragQueryFile function.
	CF_LOCALE = 16  #The data is a handle (HGLOBAL) to the locale identifier (LCID) associated with text in the clipboard. When you close the clipboard, if it contains CF_TEXT data but no CF_LOCALE data, the system automatically sets the CF_LOCALE format to the current input language. You can use the CF_LOCALE format to associate a different locale with the clipboard text.
					#An application that pastes text from the clipboard can retrieve this format to determine which character set was used to generate the text.
					#Note that the clipboard does not support plain text in multiple character sets. To achieve this, use a formatted text data type such as RTF instead.
					#The system uses the code page associated with CF_LOCALE to implicitly convert from CF_TEXT to CF_UNICODETEXT. Therefore, the correct code page table is used for the conversion.
	CF_METAFILEPICT = 3 #Handle to a metafile picture format as defined by the METAFILEPICT structure. When passing a CF_METAFILEPICT handle by means of DDE, the application responsible for deleting hMem should also free the metafile referred to by the CF_METAFILEPICT handle.
	CF_OEMTEXT = 7 #Text format containing characters in the OEM character set. Each line ends with a carriage return/linefeed (CR-LF) combination. A null character signals the end of the data.
	CF_OWNERDISPLAY = 0x0080 #Owner-display format. The clipboard owner must display and update the clipboard viewer window, and receive the WM_ASKCBFORMATNAME, WM_HSCROLLCLIPBOARD, WM_PAINTCLIPBOARD, WM_SIZECLIPBOARD, and WM_VSCROLLCLIPBOARD messages. The hMem parameter must be NULL.
	CF_PALETTE = 9 #Handle to a color palette. Whenever an application places data in the clipboard that depends on or assumes a color palette, it should place the palette on the clipboard as well.
					# If the clipboard contains data in the CF_PALETTE (logical color palette) format, the application should use the SelectPalette and RealizePalette functions to realize (compare) any other data in the clipboard against that logical palette.
					# When displaying clipboard data, the clipboard always uses as its current palette any object on the clipboard that is in the CF_PALETTE format.
	CF_PENDATA = 10 #Data for the pen extensions to the Microsoft Windows for Pen Computing.
	CF_PRIVATEFIRST = 0x0200 #Start of a range of integer values for private clipboard formats. The range ends with CF_PRIVATELAST. Handles associated with private clipboard formats are not freed automatically; the clipboard owner must free such handles, typically in response to the WM_DESTROYCLIPBOARD message.
	CF_PRIVATELAST = 0x02FF #	See CF_PRIVATEFIRST.
	CF_RIFF = 11 #Represents audio data more complex than can be represented in a CF_WAVE standard wave format.
	CF_SYLK = 4 #	Microsoft Symbolic Link (SYLK) format.
	CF_TEXT = 1 #Text format. Each line ends with a carriage return/linefeed (CR-LF) combination. A null character signals the end of the data. Use this format for ANSI text.
	CF_TIFF = 6 #	Tagged-image file format.
	CF_UNICODETEXT = 13 #Unicode text format. Each line ends with a carriage return/linefeed (CR-LF) combination. A null character signals the end of the data.
	CF_WAVE = 12 #Represents audio data in one of the standard wave formats, such as 11 kHz or 22 kHz PCM.
	
	# this was found over the interwebs and kinda important to have...
	CF_FILENAME = 0xc006
	CF_FILENAMEW = 0xc007

"""
[3748] Dialog HWND is 202CC
[3748] Clipboard format is 0xc0b7, Name is Shell IDList Array
[3748] Clipboard format is 0xc0c1, Name is Preferred DropEffect
[3748] Clipboard format is 0xc27c, Name is UsingDefaultDragImage
[3748] Clipboard format is 0xc27d, Name is DragImageBits
[3748] Clipboard format is 0xc0c7, Name is DragContext
[3748] Clipboard format is 0xc0c6, Name is InShellDragLoop
[3748] Clipboard format is 0x0f, Name is Predefined Clipboard format
[3748] Clipboard format is 0xc006, Name is FileName
[3748] Clipboard format is 0xc007, Name is FileNameW
[3748] Clipboard format is 0xc134, Name is IsShowingLayered
[3748] Clipboard format is 0xc133, Name is DragWindow
[3748] Clipboard format is 0xc281, Name is IsComputingImage
[3748] Clipboard format is 0xc0d0, Name is DropDescription
[3748] Clipboard format is 0xc0d1, Name is DisableDragText
[3748] Clipboard format is 0xc280, Name is IsShowingText
[3748] Clipboard format is 0xc284, Name is ComputedDragImage
"""



class CLIPRDR_FORMAT_LIST:
	def __init__(self, longnames:bool = False, encoding:str = 'utf-16-le'):
		self.templist:list = []

	def to_bytes(self):
		t = b''
		for fm in self.templist:
			t += fm.to_bytes()
		return t

	@staticmethod
	def from_bytes(bbuff: bytes, longnames:bool = False, encoding:str = 'utf-16-le'):
		return CLIPRDR_FORMAT_LIST.from_buffer(io.BytesIO(bbuff), longnames = longnames, encoding = encoding)

	@staticmethod
	def from_buffer(buff: io.BytesIO, longnames:bool = False, encoding:str = 'utf-16-le'):
		obj = CLIPRDR_SHORT_FORMAT_NAME
		if longnames is True:
			obj = CLIPRDR_LONG_FORMAT_NAME

		msg = CLIPRDR_FORMAT_LIST(longnames, encoding)
		# this is because of the terrible protocol design...
		for _ in range(255):
			if buff.read(1) == b'':
				break
			buff.seek(-1,1)
			msg.templist.append(obj.from_buffer(buff))
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_FORMAT_LIST ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


class CLIPRDR_SHORT_FORMAT_NAME:
	def __init__(self, encoding = 'utf-16-le'):
		self.formatId:CLIPBRD_FORMAT = None
		self.formatName:str = '' #always 32 bytes total, truncated if need be
		self.encoding = encoding
		self.clpfmt = None #stored for unknown data formats

	def to_bytes(self):
		t = self.formatId.value.to_bytes(4, byteorder='little', signed=False)
		if self.encoding == 'ascii':
			fn = self.formatName[:32]
		else:
			fn = self.formatName[:16]
		t += fn.encode(self.encoding).ljust(32, b'\x00')
		return t

	@staticmethod
	def from_bytes(bbuff: bytes, encoding:str = 'utf-16-le'):
		return CLIPRDR_SHORT_FORMAT_NAME.from_buffer(io.BytesIO(bbuff), encoding = encoding)

	@staticmethod
	def from_buffer(buff: io.BytesIO, encoding:str='utf-16-le'):
		msg = CLIPRDR_SHORT_FORMAT_NAME(encoding)
		msg.clpfmt = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		try:
			msg.formatId = CLIPBRD_FORMAT(msg.clpfmt)
		except:
			msg.formatId = CLIPBRD_FORMAT.UNKNOWN
		msg.formatName = buff.read(32).decode(encoding).replace('\x00', '')
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_SHORT_FORMAT_NAME ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t


class CLIPRDR_LONG_FORMAT_NAME:
	def __init__(self, encoding = 'utf-16-le'):
		self.formatId:CLIPBRD_FORMAT = None
		self.wszFormatName:str = None #variable, if none or '' then one single b'\x00'
		self.clpfmt = None

	def to_bytes(self):
		if self.wszFormatName is None or self.wszFormatName == '':
			fn = b'\x00'
		else:
			fn = self.wszFormatName.encode('utf-16-le')
		if isinstance(self.formatId, int):
			t = self.formatId.to_bytes(4, byteorder='little', signed=False)
		else:
			t = self.formatId.value.to_bytes(4, byteorder='little', signed=False)
		t += fn
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return CLIPRDR_LONG_FORMAT_NAME.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = CLIPRDR_LONG_FORMAT_NAME()
		msg.clpfmt = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		try:
			msg.formatId = CLIPBRD_FORMAT(msg.clpfmt)
		except:
			msg.formatId = CLIPBRD_FORMAT.UNKNOWN
		
		t = buff.read(1)
		if t == b'\x00':
			msg.wszFormatName = ''
		else:
			# this is arbitrary, thank you documentation...
			for _ in range(255):
				t += buff.read(1)
				if t.find(b'\x00\x00\x00'):
					break	
			msg.wszFormatName = t.decode('utf-16-le').replace('\x00', '')
		return msg

	def __repr__(self):
		t = '==== CLIPRDR_LONG_FORMAT_NAME ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t