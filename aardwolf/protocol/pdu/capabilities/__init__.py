import io
import enum
from os import stat

from aardwolf import logger
from aardwolf.protocol.pdu.capabilities.bitmamachachehostsupp import TS_BITMAPCACHE_HOSTSUPPORT_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.bitmap import TS_BITMAP_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.bitmapcache import TS_BITMAPCACHE_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.bitmapcache2 import TS_BITMAPCACHE_CAPABILITYSET_REV2
from aardwolf.protocol.pdu.capabilities.brush import TS_BRUSH_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.bitmapcodecs import TS_BITMAPCODECS_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.colortablecache import TS_COLORTABLE_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.compdesk import TS_COMPDESK_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.control import TS_CONTROL_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.font import TS_FONT_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.frameack import TS_FRAME_ACKNOWLEDGE_CAPABILITYSET
#from aardwolf.protocol.pdu.capabilities.gdiplus import *
from aardwolf.protocol.pdu.capabilities.general import TS_GENERAL_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.glyph import TS_GLYPHCACHE_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.input import TS_INPUT_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.largepointer import TS_LARGE_POINTER_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.multifragmentupdate import TS_MULTIFRAGMENTUPDATE_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.ninegrid import TS_DRAW_NINEGRID_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.offscreen import TS_OFFSCREEN_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.order import TS_ORDER_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.pointer import TS_POINTER_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.remoteprograms import TS_REMOTE_PROGRAMS_CAP_SET
from aardwolf.protocol.pdu.capabilities.share import TS_SHARE_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.sound import TS_SOUND_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.surface import TS_SURFCMDS_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.virtualchannel import TS_VIRTUALCHANNEL_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.windowactivation import TS_WINDOWACTIVATION_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.windowlist import TS_WINDOW_LIST_CAP_SET


class CAPSTYPE(enum.Enum):
	GENERAL = 0x0001 #General Capability Set (section 2.2.7.1.1)
	BITMAP = 0x0002 #Bitmap Capability Set (section 2.2.7.1.2)
	ORDER = 0x0003 #Order Capability Set (section 2.2.7.1.3)
	BITMAPCACHE = 0x0004 #Revision 1 Bitmap Cache Capability Set (section 2.2.7.1.4.1)
	CONTROL = 0x0005 #Control Capability Set (section 2.2.7.2.2)
	ACTIVATION = 0x0007 #Window Activation Capability Set (section 2.2.7.2.3)
	POINTER = 0x0008 #Pointer Capability Set (section 2.2.7.1.5)
	SHARE = 0x0009 #Share Capability Set (section 2.2.7.2.4)
	COLORCACHE = 0x000A #Color Table Cache Capability Set ([MS-RDPEGDI] section 2.2.1.1)
	SOUND = 0x000C #Sound Capability Set (section 2.2.7.1.11)
	INPUT = 0x000D #Input Capability Set (section 2.2.7.1.6)
	FONT = 0x000E #Font Capability Set (section 2.2.7.2.5)
	BRUSH = 0x000F #Brush Capability Set (section 2.2.7.1.7)
	GLYPHCACHE = 0x0010 #Glyph Cache Capability Set (section 2.2.7.1.8)
	OFFSCREENCACHE = 0x0011 #Offscreen Bitmap Cache Capability Set (section 2.2.7.1.9)
	BITMAPCACHE_HOSTSUPPORT = 0x0012 #Bitmap Cache Host Support Capability Set (section 2.2.7.2.1)
	BITMAPCACHE_REV2 = 0x0013 #Revision 2 Bitmap Cache Capability Set (section 2.2.7.1.4.2)
	VIRTUALCHANNEL = 0x0014 #Virtual Channel Capability Set (section 2.2.7.1.10)
	DRAWNINEGRIDCACHE = 0x0015 #DrawNineGrid Cache Capability Set ([MS-RDPEGDI] section 2.2.1.2)
	DRAWGDIPLUS = 0x0016 #Draw GDI+ Cache Capability Set ([MS-RDPEGDI] section 2.2.1.3)
	RAIL = 0x0017 #Remote Programs Capability Set ([MS-RDPERP] section 2.2.1.1.1)
	WINDOW = 0x0018 #Window List Capability Set ([MS-RDPERP] section 2.2.1.1.2)
	COMPDESK = 0x0019 #Desktop Composition Extension Capability Set (section 2.2.7.2.8)
	MULTIFRAGMENTUPDATE = 0x001A #Multifragment Update Capability Set (section 2.2.7.2.6)
	LARGE_POINTER = 0x001B #Large Pointer Capability Set (section 2.2.7.2.7)
	SURFACE_COMMANDS = 0x001C #Surface Commands Capability Set (section 2.2.7.2.9)
	BITMAP_CODECS = 0x001D #Bitmap Codecs Capability Set (section 2.2.7.2.10)
	FRAME_ACKNOWLEDGE = 0x001E #Frame Acknowledge Capability Set ([MS-RDPRFX] section 2.2.1.3)

class TS_CAPS_SET:
	def __init__(self):
		self.capabilitySetType:CAPSTYPE = None
		self.lengthCapability:int = None
		self.capabilityData:bytes = None

		# high level
		self.capability = None
	
	@staticmethod
	def from_capability(cap):
		t = TS_CAPS_SET()
		t.capabilitySetType = obj2otype[type(cap)]
		t.capability = cap
		return t

	def to_bytes(self):
		cd = self.capability.to_bytes()
		t = self.capabilitySetType.value.to_bytes(2, byteorder='little', signed = False)
		t += (len(cd)+4).to_bytes(2, byteorder='little', signed = False)
		t += cd
		return t

	@staticmethod
	def from_bytes(bbuff: bytes):
		return TS_CAPS_SET.from_buffer(io.BytesIO(bbuff))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_CAPS_SET()
		msg.capabilitySetType = CAPSTYPE(int.from_bytes(buff.read(2), byteorder='little', signed = False))
		msg.lengthCapability = int.from_bytes(buff.read(2), byteorder='little', signed = False)
		msg.capabilityData = buff.read(msg.lengthCapability-4)
		
		ot = otype2obj[msg.capabilitySetType]
		if ot is not None:
			msg.capability = ot.from_bytes(msg.capabilityData)
			#if msg.capabilityData != msg.capability.to_bytes():
			#	raise Exception('mismatch!')
		else:
			logger.debug('Not implemented parser! %s' % msg.capabilitySetType)
		return msg

	def __repr__(self):
		t = '==== TS_CAPS_SET ====\r\n'
		for k in self.__dict__:
			if isinstance(self.__dict__[k], enum.IntFlag):
				value = self.__dict__[k]
			elif isinstance(self.__dict__[k], enum.Enum):
				value = self.__dict__[k].name
			else:
				value = self.__dict__[k]
			t += '%s: %s\r\n' % (k, value)
		return t

otype2obj = {
	CAPSTYPE.GENERAL : TS_GENERAL_CAPABILITYSET,
	CAPSTYPE.BITMAP : TS_BITMAP_CAPABILITYSET,
	CAPSTYPE.ORDER : TS_ORDER_CAPABILITYSET,
	CAPSTYPE.BITMAPCACHE : TS_BITMAPCACHE_CAPABILITYSET,
	CAPSTYPE.CONTROL : TS_CONTROL_CAPABILITYSET,
	CAPSTYPE.ACTIVATION : TS_WINDOWACTIVATION_CAPABILITYSET,
	CAPSTYPE.POINTER : TS_POINTER_CAPABILITYSET,
	CAPSTYPE.SHARE : TS_SHARE_CAPABILITYSET,
	CAPSTYPE.COLORCACHE : TS_COLORTABLE_CAPABILITYSET,
	CAPSTYPE.SOUND : TS_SOUND_CAPABILITYSET,
	CAPSTYPE.INPUT : TS_INPUT_CAPABILITYSET,
	CAPSTYPE.FONT : TS_FONT_CAPABILITYSET,
	CAPSTYPE.BRUSH : TS_BRUSH_CAPABILITYSET,
	CAPSTYPE.GLYPHCACHE : TS_GLYPHCACHE_CAPABILITYSET,
	CAPSTYPE.OFFSCREENCACHE : TS_OFFSCREEN_CAPABILITYSET,
	CAPSTYPE.BITMAPCACHE_HOSTSUPPORT : TS_BITMAPCACHE_HOSTSUPPORT_CAPABILITYSET,
	CAPSTYPE.BITMAPCACHE_REV2 : TS_BITMAPCACHE_CAPABILITYSET_REV2, 
	CAPSTYPE.VIRTUALCHANNEL : TS_VIRTUALCHANNEL_CAPABILITYSET,
	CAPSTYPE.DRAWNINEGRIDCACHE : TS_DRAW_NINEGRID_CAPABILITYSET,
	CAPSTYPE.DRAWGDIPLUS : None,
	CAPSTYPE.RAIL : TS_REMOTE_PROGRAMS_CAP_SET,
	CAPSTYPE.WINDOW : TS_WINDOW_LIST_CAP_SET,
	CAPSTYPE.COMPDESK : TS_COMPDESK_CAPABILITYSET,
	CAPSTYPE.MULTIFRAGMENTUPDATE : TS_MULTIFRAGMENTUPDATE_CAPABILITYSET,
	CAPSTYPE.LARGE_POINTER : TS_LARGE_POINTER_CAPABILITYSET,
	CAPSTYPE.SURFACE_COMMANDS : TS_SURFCMDS_CAPABILITYSET,
	CAPSTYPE.BITMAP_CODECS : TS_BITMAPCODECS_CAPABILITYSET,
	CAPSTYPE.FRAME_ACKNOWLEDGE : TS_FRAME_ACKNOWLEDGE_CAPABILITYSET,

}

obj2otype = {v: k for k, v in otype2obj.items()}