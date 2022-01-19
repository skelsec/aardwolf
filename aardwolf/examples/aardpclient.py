from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT
from aardwolf.commons.queuedata.clipboard import RDP_CLIPBOARD_DATA_TXT
import sys
import asyncio
import traceback
import queue
import threading

from aardwolf import logger
from aardwolf.commons.url import RDPConnectionURL
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.queuedata import RDPDATATYPE
from aardwolf.commons.queuedata.keyboard import RDP_KEYBOARD_SCANCODE
from aardwolf.commons.queuedata.mouse import RDP_MOUSE

from PyQt5.QtWidgets import QApplication, QMainWindow, qApp, QLabel
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, Qt
from PyQt5.QtGui import QPainter, QImage, QPixmap

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

class RDPInterfaceThread(QObject):
	result=pyqtSignal(RDPImage)
	connection_terminated=pyqtSignal()
	
	def __init__(self, parent=None, **kwargs):
		super().__init__(parent, **kwargs)
		self.settings = None
		self.conn = None
		self.input_evt = None
		self.in_q = None
		self.loop_started_evt = threading.Event()
	
	def set_settings(self, settings, in_q):
		self.settings = settings
		self.in_q = in_q

	async def inputhandler(self):
		# This is super-ugly but I could not find a better solution
		# Problem is that pyqt5 is not async, and QT internally is using its own event loop
		# which makes everythign a mess.
		# If you know better (that doesn't require a noname unmaintained lib install) lemme know!
		try:
			while True:
				try:
					data = self.in_q.get(False)
				except queue.Empty:
					await asyncio.sleep(0.01)
					continue
				await self.conn.ext_in_queue.put(data)
		except:
			traceback.print_exc()
	
	async def rdpconnection(self):
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

	def starter(self):
		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)
		self.loop.run_until_complete(self.rdpconnection())
		self.loop.close()
	
	@pyqtSlot()
	def start(self):
		# creating separate thread for async otherwise this will not return
		# and then there will be no events sent back from application
		asyncthread = threading.Thread(target=self.starter, args=())
		asyncthread.start()
	

class RDPClientQTGUI(QMainWindow):
	#inputevent=pyqtSignal()

	def __init__(self, settings:RDPClientConsoleSettings):
		super().__init__()
		self.settings = settings

		# enabling this will singificantly increase the bandwith
		self.mhover = settings.mhover
		# enabling keyboard tracking
		self.keyboard = settings.keyboard

		# setting up the main window with the requested resolution
		self.setGeometry(0,0, self.settings.iosettings.video_width, self.settings.iosettings.video_height)
		# this buffer will hold the current frame and will be contantly updated
		# as new rectangle info comes in from the server
		self._buffer = QImage(self.settings.iosettings.video_width, self.settings.iosettings.video_height, QImage.Format_RGB32)
		
		
		# setting up worker thread in a qthread
		# the worker recieves the video updates from the connection object
		# and then dispatches it to updateImage
		# this is needed as the RDPConnection class uses async queues
		# and QT is not async so an interface between the two worlds
		# had to be created
		self.in_q = queue.Queue()
		self._thread=QThread()
		self._threaded=RDPInterfaceThread(result=self.updateImage, connection_terminated=self.connectionClosed)
		self._threaded.set_settings(self.settings, self.in_q)
		self._thread.started.connect(self._threaded.start)
		self._threaded.moveToThread(self._thread)
		qApp.aboutToQuit.connect(self._thread.quit)
		self._thread.start()

		# setting up the canvas (qlabel) which will display the image data
		self._label_imageDisplay = QLabel()
		self.setCentralWidget(self._label_imageDisplay)
		
		# enabling mouse tracking
		self.setMouseTracking(True)
		self._label_imageDisplay.setMouseTracking(True)
	
	def closeEvent(self, event):
		self._thread.quit()
		event.accept()
	
	def connectionClosed(self):
		print('its over!')
	
	def updateImage(self, event):
		with QPainter(self._buffer) as qp:
			qp.drawImage(event.x, event.y, event.image, 0, 0, event.width, event.height)
		pixmap01 = QPixmap.fromImage(self._buffer)
		pixmap_image = QPixmap(pixmap01)
		self._label_imageDisplay.setPixmap(pixmap_image)
		self._label_imageDisplay.setAlignment(Qt.AlignCenter)
		self._label_imageDisplay.setScaledContents(True)
		self._label_imageDisplay.setMinimumSize(1,1)
		self._label_imageDisplay.show()
	
	def keyPressEvent(self, e):
		if self.keyboard is False:
			return
		
		if e.key()==(Qt.Key_Control and Qt.Key_V):
			ki = RDP_CLIPBOARD_DATA_TXT()
			ki.datatype = CLIPBRD_FORMAT.CF_UNICODETEXT
			ki.data = pyperclip.paste()
			self.in_q.put(ki)



		ki = RDP_KEYBOARD_SCANCODE()
		ki.keyCode = e.nativeScanCode()
		ki.is_pressed = True
		if sys.platform == "linux":
			#why tho?
			ki.keyCode -= 8
		self.in_q.put(ki)

	def keyReleaseEvent(self, e):
		if self.keyboard is False:
			return
		ki = RDP_KEYBOARD_SCANCODE()
		ki.keyCode = e.nativeScanCode()
		ki.is_pressed = False
		if sys.platform == "linux":
			ki.keyCode -= 8
		self.in_q.put(ki)
	
	def mouseMoveEvent(self, e):
		if self.mhover is False:
			return
		mi = RDP_MOUSE()
		mi.xPos = e.pos().x()
		mi.yPos = e.pos().y()
		mi.button = 0
		mi.pressed = False
		self.in_q.put(mi)

	def mouseReleaseEvent(self, e):
		"""
		mouse button release event
		"""
		button = e.button()
		buttonNumber = 0
		if button == Qt.LeftButton:
			buttonNumber = 1
		elif button == Qt.RightButton:
			buttonNumber = 2
		elif button == Qt.MidButton:
			buttonNumber = 3

		mi = RDP_MOUSE()
		mi.xPos = e.pos().x()
		mi.yPos = e.pos().y()
		mi.button = buttonNumber
		mi.pressed = False

		self.in_q.put(mi)



	def mousePressEvent(self, e):
		button = e.button()
		buttonNumber = 0
		if button == Qt.LeftButton:
			buttonNumber = 1
		elif button == Qt.RightButton:
			buttonNumber = 2
		elif button == Qt.MidButton:
			buttonNumber = 3

		mi = RDP_MOUSE()
		mi.xPos = e.pos().x()
		mi.yPos = e.pos().y()
		mi.button = buttonNumber
		mi.pressed = True

		self.in_q.put(mi)
	




def main():
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
	iosettings.video_out_format = 'qt'
	
	settings = RDPClientConsoleSettings(args.url, iosettings)
	settings.mhover = args.no_mouse_hover
	settings.keyboard = args.no_keyboard


	app = QApplication(sys.argv)
	demo = RDPClientQTGUI(settings)
	demo.show()
	app.exec_()
	qApp.quit()

if __name__ == '__main__':
	main()