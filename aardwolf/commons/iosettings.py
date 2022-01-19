


class RDPIOSettings:
	def __init__(self):
		self.video_width = 1024
		self.video_height = 768
		self.video_bpp_min = 16 #minimum supported bpp
		self.video_bpp_max = 16 #max supported bpp
		self.video_bpp_supported = [15, 16, 24, 32]
		self.video_out_format = 'qt' # the recatngle image format which will be sent via the queue

		self.keyboard_layout = 1033
		self.keyboard_type = 4
		self.keyboard_subtype = 0
		self.keyboard_functionkey = 12

		self.clipboard_use_pyperclip = True