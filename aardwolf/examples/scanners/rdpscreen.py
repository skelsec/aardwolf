import asyncio
import io
import base64
import datetime
from asysocks.unicomm.common.scanner.common import *
from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS
from aardwolf.commons.queuedata.constants import MOUSEBUTTON, VIDEO_FORMAT
from aardwolf.commons.iosettings import RDPIOSettings


class RDPScreenshotRes:
	def __init__(self, target, screendata):
		self.target = target
		self.screendata = screendata

	def get_fname(self):
		return 'rdpscreen_%s_%s.png' % (self.target, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

	def get_fdata(self):
		return self.screendata

	def get_header(self):
		return ['screendata']

	def to_line(self, separator = '\t'):
		return base64.b64encode(self.screendata).decode()

class RDPScreenshotScanner:
	def __init__(self, factory:RDPConnectionFactory):
		self.factory:RDPConnectionFactory = factory
		self.screentime = 5
		self.iosettings = RDPIOSettings()
		self.iosettings.channels = []
		self.iosettings.video_width = 1024
		self.iosettings.video_height = 768
		self.iosettings.video_bpp_min = 15 #servers dont support 8 any more :/
		self.iosettings.video_bpp_max = 32
		self.iosettings.video_out_format = VIDEO_FORMAT.PNG #PIL produces incorrect picture for some reason?! TODO: check bug
		self.iosettings.clipboard_use_pyperclip = False


	async def run(self, targetid, target, out_queue):
		connection = None
		try:
			connection = self.factory.create_connection_newtarget(target, self.iosettings)
			_, err = await connection.connect()
			if err is not None:
				raise err
			
			await asyncio.sleep(self.screentime)

		except asyncio.CancelledError:
			return
		except Exception as e:
			raise
		finally:
			if connection is not None and connection.desktop_buffer_has_data is True:
				buffer = connection.get_desktop_buffer(VIDEO_FORMAT.PIL)
				data = io.BytesIO()
				buffer.save(data,'png')
				data.seek(0,0)
				await out_queue.put(ScannerData(target, RDPScreenshotRes(target, data.read())))
			if connection is not None:
				await connection.terminate()