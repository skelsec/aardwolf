from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT
from aardwolf.commons.queuedata import RDPDATATYPE


class RDP_CLIPBOARD_READY:
	def __init__(self):
		self.type = RDPDATATYPE.CLIPBOARD_READY

class RDP_CLIPBOARD_CONSUMED:
	def __init__(self):
		self.type = RDPDATATYPE.CLIPBOARD_CONSUMED
	
class RDP_CLIPBOARD_NEW_DATA_AVAILABLE:
	def __init__(self):
		self.type = RDPDATATYPE.CLIPBOARD_NEW_DATA_AVAILABLE
	
class RDP_CLIPBOARD_DATA_TXT:
	def __init__(self):
		self.type = RDPDATATYPE.CLIPBOARD_DATA_TXT
		self.data = None
		self.datatype: CLIPBRD_FORMAT = None

	def get_data(self, fmt:CLIPBRD_FORMAT = None):
		if fmt is None:
			fmt = self.datatype
		if fmt == CLIPBRD_FORMAT.CF_UNICODETEXT:
			return self.data.encode('utf-16-le') + b'\x00'*3
		elif fmt == CLIPBRD_FORMAT.CF_TEXT:
			return self.data.encode('ascii', 'ignore') + b'\x00'
		elif fmt == CLIPBRD_FORMAT.CF_OEMTEXT:
			return self.data.encode('cp1252', 'ignore') + b'\x00'*3
		else:
			return self.data
	
	def __eq__(self, obj):
		if isinstance(obj, RDP_CLIPBOARD_DATA_TXT) is False:
			return False
		if self.data != obj.data or self.datatype != obj.datatype:
			return False
		return True
