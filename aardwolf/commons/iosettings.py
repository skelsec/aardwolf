from aardwolf.extensions.RDPECLIP.channel import RDPECLIPChannel
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS, NEG_FLAGS
from aardwolf.commons.queuedata.constants import VIDEO_FORMAT
from aardwolf.protocol.T125.extendedinfopacket import PERF
from aardwolf.extensions.RDPEDYC.channel import RDPEDYCChannel

from aardwolf.extensions.RDPEDYC.vchannels.echo import VchannelECHO
#from aardwolf.extensions.RDPEDYC.vchannels.test import VchannelTEST

class RDPIOSettings:
	def __init__(self):
		# RDP only settings
		# Which channels should be enabled
		self.channels = [RDPECLIPChannel, RDPEDYCChannel]
		self.vchannels = {
			'ECHO' : VchannelECHO(),
			#'DATATEST1' : VchannelTEST(),
		}
		# Authentication protocols supported
		self.supported_protocols = None # supported_protocols if None: it will be determined automatically. otherwise  select one or more from these SUPP_PROTOCOLS.RDP | SUPP_PROTOCOLS.SSL |SUPP_PROTOCOLS.HYBRID_EX

		# Video settings used by both RDP and VNC
		self.video_width = 1024
		self.video_height = 768
		self.video_out_format = VIDEO_FORMAT.QT5 # the recatngle image format which will be sent via the queue
		
		# Video settings used only by RDP
		# minimum supported BPP
		self.video_bpp_min = 16 
		# maximum supported BPP
		self.video_bpp_max = 16 #max supported bpp
		# all supported BPPs
		self.video_bpp_supported = [15, 16, 24, 32]

		#Performance booster flags
		self.performance_flags = PERF.DISABLE_WALLPAPER | PERF.DISABLE_THEMING | PERF.DISABLE_CURSORSETTINGS | PERF.DISABLE_MENUANIMATIONS | PERF.DISABLE_FULLWINDOWDRAG
		
		# Keyboard settings
		# Keyborad settings used by both RDP and VNC		
		# clinet_keyboard is used by VNC where the keyboard state must be virtualized client-side
		self.client_keyboard = 'enus'

		# Keyboard setting used only by RDP
		# TODO: this should be cleaned up
		self.keyboard_layout = 1033
		self.keyboard_type = 4
		self.keyboard_subtype = 0
		self.keyboard_functionkey = 12

		# Clipboard settings

		# pyperclip is currently the only somewhat working cross-platform clipboard manager
		# disabling it means that clipboard messages will only be dispatched via the external queue
		# but the client's clipboard will not be updated
		self.clipboard_use_pyperclip = True

		# store all incloing clipboard data recieved from server. Text only
		# set it to true to have a file created, or to a string with a file path
		# 
		self.clipboard_store_data = None

		# determines how often the client polls for desktop changes
		self.vnc_fps = 10

		# determines what type of encoding the client supports.
		# Feel free to change the order of these but not the value. 
		# Each value corresponds to an encoding type and only these three anre implemented currently.
		# The order signifies the preference to the server but the server can decide to ignore it
		self.vnc_encodings = [2, 1, 0]
		