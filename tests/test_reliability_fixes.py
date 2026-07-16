import asyncio
import unittest
from types import SimpleNamespace

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.connection import RDPConnection
from aardwolf.extensions.RDPECLIP.channel import RDPECLIPChannel
from aardwolf.protocol.pdu.input.keyboard import KBDFLAGS


class ReliabilityFixTests(unittest.TestCase):
	def test_extended_scancode_uses_low_byte_and_extended_flag(self):
		connection = RDPConnection(
			target=None, credentials=None, iosettings=RDPIOSettings()
		)
		connection._RDPConnection__joined_channels['MCS'] = SimpleNamespace(
			channel_id=1001
		)
		captured = {}

		async def capture(dataobj, *_args):
			captured['keyboard'] = dataobj.slowPathInputEvents[0].input

		connection.handle_out_data = capture
		asyncio.run(connection.send_key_scancode(0xE05B, True, False))

		keyboard = captured['keyboard']
		self.assertEqual(keyboard.keyCode, 0x5B)
		self.assertIn(KBDFLAGS.EXTENDED, keyboard.keyboardFlags)

	def test_clipboard_channel_unregisters_on_stop(self):
		iosettings = RDPIOSettings()
		channel = RDPECLIPChannel(iosettings)

		self.assertIn(channel, iosettings.clipboard._handlers)
		asyncio.run(channel.stop())
		self.assertNotIn(channel, iosettings.clipboard._handlers)

	def test_io_settings_clone_uses_fresh_connection_state(self):
		iosettings = RDPIOSettings()
		iosettings.video_width = 1600

		first = iosettings.clone_for_connection()
		second = iosettings.clone_for_connection()

		self.assertEqual(first.video_width, 1600)
		self.assertIsNot(first.clipboard, second.clipboard)
		self.assertIsNot(first.vchannels['ECHO'], second.vchannels['ECHO'])


if __name__ == '__main__':
	unittest.main()
