from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT
from aardwolf.commons.queuedata.clipboard import RDP_CLIPBOARD_DATA_TXT
import sys
import asyncio
import traceback
import queue
from threading import Thread

from aardwolf import logger
from aardwolf.commons.url import RDPConnectionURL
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.queuedata import RDPDATATYPE
from aardwolf.commons.queuedata.keyboard import RDP_KEYBOARD_SCANCODE
from aardwolf.commons.queuedata.mouse import RDP_MOUSE

import PySimpleGUI as sg
from PIL import Image, ImageTk
import pyperclip


# with the help of
# https://gist.github.com/jazzycamel/8abd37bf2d60cce6e01d

class RDPClientConsoleSettings:
	def __init__(self, url:str, iosettings:RDPIOSettings):
		self.mhover:int = True
		self.keyboard:int = True
		self.url:str = url
		self.iosettings:RDPIOSettings = iosettings

class RDPImage:
	def __init__(self,x,y,image,width,height):
		self.x = x
		self.y = y
		self.image = image
		self.width = width
		self.height = height
"""
try:
			rdpurl = RDPConnectionURL(self.settings.url)
			self.conn = rdpurl.get_connection(self.settings.iosettings)
			_, err = await self.conn.connect()
			if err is not None:
				raise err

			asyncio.create_task(self.inputhandler())
			self.loop_started_evt.set()
			while True:
				data = await self.conn.ext_out_queue.get()
				if data is None:
					return
				if data.type == RDPDATATYPE.VIDEO:
					ri = RDPImage(data.x, data.y, data.data, data.height, data.width)
					self.result.emit(ri)
				elif data.type == RDPDATATYPE.CLIPBOARD_READY:
					continue
				else:
					print('Unknown incoming data: %s'% data)


		except Exception as e:
			traceback.print_exc()
		finally:
			self.connection_terminated.emit()
"""

async def rdp_run(settings:RDPClientConsoleSettings, video_in_q, rdp_out_q):
	# the loop running this should be in a separate thread than the windows manager
	pass

def asyncloop(loop, settings:RDPClientConsoleSettings, video_in_q, rdp_out_q):
	# Set loop as the active event loop for this thread
	asyncio.set_event_loop(loop)
	# We will get our tasks from the main thread so just run an empty loop
	loop.run_until_complete(rdp_run(settings, video_in_q, rdp_out_q))


async def window_read(window):
	while True:
		event, res = window.read(timeout=1)
		if event == sg.TIMEOUT_EVENT:
			continue
		return ('window', event, res)

async def video_read(q):
	data = await q.get()
	if data.type == RDPDATATYPE.VIDEO:
		return 'video', data
	else:
		return 'notvideo', data

async def main():
	print('This is not yet implemented!!!')
	return



	import logging
	import argparse
	parser = argparse.ArgumentParser(description='Async RDP Client')
	parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbosity, can be stacked')
	parser.add_argument('--no-mouse-hover', action='store_false', help='Disables sending mouse hovering data. (saves bandwith)')
	parser.add_argument('--no-keyboard', action='store_false', help='Disables keyboard input. (whatever)')
	parser.add_argument('--res', default = '1024x768', help='Resolution in "WIDTHxHEIGHT" format. Default: "1024x768"')
	parser.add_argument('--bpp', choices = [15, 16, 24, 32], default = 32, type=int, help='Bits per pixel.')
	parser.add_argument('url', help="RDP connection url")

	args = parser.parse_args()

	if args.verbose == 1:
		logger.setLevel(logging.INFO)
	elif args.verbose == 2:
		logger.setLevel(logging.DEBUG)
	elif args.verbose > 2:
		logger.setLevel(1)

	width, height = args.res.upper().split('X')
	height = int(height)
	width = int(width)

	iosettings = RDPIOSettings()
	iosettings.video_width = width
	iosettings.video_height = height
	iosettings.video_bpp_min = 15 #servers dont support 8 any more :/
	iosettings.video_bpp_max = args.bpp
	iosettings.video_out_format = VIDEO_FORMAT.PNG
	
	settings = RDPClientConsoleSettings(args.url, iosettings)
	settings.mhover = args.no_mouse_hover
	settings.keyboard = args.no_keyboard

	loop = asyncio.new_event_loop()
	video_in_q = queue.Queue()
	rdp_out_q = queue.Queue()
	#t = Thread(target=asyncloop, args=(loop, settings, video_in_q, rdp_out_q))
	#t.start()

	elements = [
		[sg.Graph(key="image", canvas_size=(width, height), graph_bottom_left=(0, 0), graph_top_right=(width, height), drag_submits=True, enable_events=True)],
		#[sg.Text("", size=(1, 1), key='text')],
	]
	window = sg.Window("AARDWOLF RDP", elements, size=(width, height))
	
	try:
		rdpurl = RDPConnectionURL(settings.url)
		conn = rdpurl.get_connection(settings.iosettings)
		_, err = await conn.connect()
		if err is not None:
			raise err
	except Exception as e:
		traceback.print_exc()
		return
	
	#await conn.
	
	desktop_image = Image.new("RGBA", [settings.iosettings.video_width, settings.iosettings.video_height])
	terminated = False
	while not terminated:
		window_read_task = window_read(window)
		video_q_read = video_read(conn.ext_out_queue)
		tasks = [window_read_task, video_q_read]
		finished, unfinished = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
		for x in finished:
			result = x.result()
			if result[0] == 'window':
				event = result[1]
				values = result[2]
				if event == sg.TIMEOUT_EVENT:
					continue
				print(event)
				if event == "Exit" or event == sg.WIN_CLOSED:
					terminated = True
					break
			elif result[0] == 'video':
				#desktop_image.paste(result[1].data, (result[1].x, result[1].y))
				#window["image"].draw_image(data=ImageTk.PhotoImage(desktop_image))
				window["image"].draw_image(data=result[1].data, location=(result[1].x, settings.iosettings.video_height - result[1].y + result[1].height))
				
				print('video')
				#print(result)

			# cancel the other tasks, we have a result. We need to wait for the cancellations
			# to propagate.
			for task in unfinished:
				task.cancel()
			if len(unfinished) > 0:
				await asyncio.wait(unfinished)
		
		#if event == sg.TIMEOUT_EVENT:
		#	continue
		#if event == "Exit" or event == sg.WIN_CLOSED:
		#	break
	

if __name__ == '__main__':
	asyncio.run(main())