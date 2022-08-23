

import asyncio
import traceback
from typing import List

from aardwolf import logger
from aardwolf.keyboard.layoutmanager import KeyboardLayoutManager
from aardwolf.keyboard import KeyboardLayout, VK_MODIFIERS

class DuckyExecutorBase:
	def __init__(self, keyboard_layout:KeyboardLayout, key_sender, send_as_char = False):
		self.keyboard_layout = keyboard_layout
		self.key_sender = key_sender
		self.send_as_char = send_as_char
		self.default_delay = 100
		self.default_chardelay = 50/1000
		self.aliases = {
			'do_default_delay' : 'do_defaultdelay',
			'do_windows' : 'do_gui',
			'do_app' : 'do_menu',
			'do_ctrl' : 'do_control',
			'do_uparrow' : 'do_up',
			'do_leftarrow' : 'do_left',
			'do_rightarrow' : 'do_right',
			'do_break' : 'do_pause',
			'do_delete' : 'do_del',
			'do_escape' : 'do_esc',
			'do_downarrow' : 'do_down',
			'do_delete' : 'do_del',
		}

		self.cmd_to_vk = {
			'backspace' : 'VK_BACK',
			'tab' : 'VK_TAB',
			'space' : 'VK_SPACE',
			'scrollock' : 'VK_SCROLL',
			'printscreen' : 'VK_SNAPSHOT',
			'pagedown' : 'VK_NEXT',
			'pageup' : 'VK_PRIOR',
			'numlock' : 'VK_NUMLOCK',
			'insert' : 'VK_INSERT',
			'home' : 'VK_HOME',
			'esc' : 'VK_ESCAPE',
			'escape' : 'VK_ESCAPE',
			'end' : 'VK_END',
			'del' : 'VK_DELETE',
			'delete' : 'VK_DELETE',
			'capslock' : 'VK_CAPITAL',
			'pause' : 'VK_PAUSE',
			'break' : 'VK_PAUSE',
			'right' : 'VK_RIGHT',
			'rightarrow' : 'VK_RIGHT',
			'left' : 'VK_LEFT',
			'leftarrow' : 'VK_LEFT',
			'down' : 'VK_DOWN',
			'downarrow' : 'VK_DOWN',
			'up' : 'VK_UP',
			'uparrow' : 'VK_UP',
			'gui': 'VK_LWIN',
			'windows': 'VK_LWIN',
			'enter' : 'VK_RETURN',
			'shift' : 'VK_LSHIFT',
			'alt' : 'VK_LMENU',
			'f1' : 'VK_F1',
			'f2' : 'VK_F2',
			'f3' : 'VK_F3',
			'f4' : 'VK_F4',
			'f5' : 'VK_F5',
			'f6' : 'VK_F6',
			'f7' : 'VK_F7',
			'f8' : 'VK_F8',
			'f9' : 'VK_F9',
			'f10' : 'VK_F10',
			'f11' : 'VK_F11',
			'f12' : 'VK_F12',

		}
	
	def get_function(self, cmdname):
		if cmdname.startswith('do_') is False:
			cmdname = 'do_' + cmdname
		
		if cmdname in self.aliases:
			cmdname = self.aliases[cmdname]
		
		return getattr(self, cmdname)

	async def do_enter(self):
		await self.keydispatch('VK_RETURN')
		#await asyncio.sleep(self.default_delay)

	async def do_function(self, data):
		await self.keydispatch('VK_F%s' % data[0])
	
	async def do_rem(self, data:List[str]):
		data = ' '.join(data)
		logger.debug(data)

	async def do_defaultdelay(self, delay:int):
		delay = ' '.join(delay)
		self.default_delay = int(delay) / 1000 #protocol allows delay to be set in 10 miliseconds interval
	
	async def do_defaultchardelay(self, delay:int):
		delay = ' '.join(delay)
		self.default_chardelay = int(delay) / 1000
	
	async def do_delay(self, delay:int):
		pass
		delay = ' '.join(delay)
		delay = int(delay) / 1000
		if delay > 1:
			return
		await asyncio.sleep(delay)

	async def do_string(self, data:str):
		data = ' '.join(data)
		if self.send_as_char is True:
			for c in data:
				await self.key_sender(c, True, True)
				await asyncio.sleep(self.default_chardelay)
		else:
			for c in data:
				await self.keydispatch(c)

	async def do_gui(self, data = []):
		if len(data) > 0:
			data.insert(0, 'VK_LWIN')
			await self.multi_key_press(data)
		else:
			await self.keydispatch('VK_LWIN')
		#await asyncio.sleep(self.default_delay)

	async def do_menu(self):
		await self.keydispatch('VK_RMENU')
		#await asyncio.sleep(self.default_delay)

	async def do_shift(self, data = []):
		print('SHIFT + %s' % repr(data))
		if len(data) > 0:
			data.insert(0, 'VK_LSHIFT')
			await self.multi_key_press(data)
		else:
			await self.keydispatch('VK_LSHIFT')

	async def do_control(self, data = []):
		print('CTRL + %s' % repr(data))
		if len(data) > 0:
			data.insert(0, 'VK_LCONTROL')
			await self.multi_key_press(data)
		else:
			await self.keydispatch('VK_LCONTROL')

	async def do_alt(self, data = []):
		print('ALT + %s' % repr(data))
		if len(data) > 0:
			data.insert(0, 'VK_LMENU')
			await self.multi_key_press(data)
		else:
			await self.keydispatch('VK_LMENU')

	async def do_up(self):
		await self.keydispatch('VK_UP')
		#await asyncio.sleep(self.default_delay)

	async def do_down(self):
		await self.keydispatch('VK_DOWN')
		#await asyncio.sleep(self.default_delay)

	async def do_left(self):
		await self.keydispatch('VK_LEFT')
		#await asyncio.sleep(self.default_delay)

	async def do_right(self):
		await self.keydispatch('VK_RIGHT')
		#await asyncio.sleep(self.default_delay)
	
	async def do_pause(self):
		await self.keydispatch('VK_PAUSE')
		#await asyncio.sleep(self.default_delay)
	
	async def do_capslock(self):
		await self.keydispatch('VK_CAPITAL')
		#await asyncio.sleep(self.default_delay)
	
	async def do_del(self):
		await self.keydispatch('VK_DELETE')
		#await asyncio.sleep(self.default_delay)

	async def do_end(self):
		await self.keydispatch('VK_END')
		#await asyncio.sleep(self.default_delay)
	
	async def do_esc(self):
		await self.keydispatch('VK_ESCAPE')
		#await asyncio.sleep(self.default_delay)

	async def do_home(self):
		await self.keydispatch('VK_HOME')
		#await asyncio.sleep(self.default_delay)
	
	async def do_insert(self):
		await self.keydispatch('VK_INSERT')
		#await asyncio.sleep(self.default_delay)
	
	async def do_numlock(self):
		await self.keydispatch('VK_NUMLOCK')
		#await asyncio.sleep(self.default_delay)
	
	async def do_pageup(self):
		await self.keydispatch('VK_PRIOR')
		#await asyncio.sleep(self.default_delay)
	
	async def do_pagedown(self):
		await self.keydispatch('VK_NEXT')
		#await asyncio.sleep(self.default_delay)
	
	async def do_printscreen(self):
		await self.keydispatch('VK_SNAPSHOT')
		#await asyncio.sleep(self.default_delay)
	
	async def do_scrollock(self):
		await self.keydispatch('VK_SCROLL')
		#await asyncio.sleep(self.default_delay)
	
	async def do_space(self):
		await self.keydispatch('VK_SPACE')
		#await asyncio.sleep(self.default_delay)
	
	async def do_tab(self):
		await self.keydispatch('VK_TAB')
		#await asyncio.sleep(self.default_delay)
	
	async def do_backspace(self):
		await self.keydispatch('VK_BACK')
		#await asyncio.sleep(self.default_delay)
	
	async def multi_key_press(self, keys):
		codes = []
		#print(keys)
		for x in keys:
			#print(x)
			if len(x) == 1:
				scancode, mo = self.keyboard_layout.char_to_scancode(x.lower())
				if mo != VK_MODIFIERS(0) and mo != VK_MODIFIERS.VK_CAPITAL|VK_MODIFIERS.VK_SHIFT:
					print(mo)
					raise Exception('This is not supported!!!!')
				codes.append(scancode)
			else:
				if x.lower() in self.cmd_to_vk:
					codes.append(self.keyboard_layout.vk_to_scancode(self.cmd_to_vk[x.lower()]))
				else:
					codes.append(self.keyboard_layout.vk_to_scancode(x))
		
		for code in codes:
			await asyncio.sleep(self.default_chardelay)
			await self.key_sender(code, True)
		
		for code in codes[::-1]:
			await asyncio.sleep(self.default_chardelay)
			await self.key_sender(code, False)
	
	async def keydispatch(self, key, modifiers = VK_MODIFIERS(0)):
		if key in '0123456789':
			key = 'VK_%s' % key
		if len(key) == 1:
			try:
				scancode, mo = self.keyboard_layout.char_to_scancode(key)
				#print('key     : %s' % key)
				#print('scancode: %s' % scancode)
				#print('mo      : %s' % mo)

			except KeyError:
				# this is bad...
				await asyncio.sleep(self.default_chardelay)
				await self.key_sender(key, True, True)
				return

			if mo == VK_MODIFIERS(0):
				await asyncio.sleep(self.default_chardelay)
				await self.key_sender(scancode, True)
				await asyncio.sleep(self.default_chardelay)
				await self.key_sender(scancode, False)
			else:
				#print('key: %s' % key)
				#print('sc : %s' % scancode)
				#print('mo : %s' % repr(mo))
				#input()
				modcodes = []
				afs = [flag for flag in VK_MODIFIERS if flag in mo]
				for af in afs:
					if af == VK_MODIFIERS.VK_CAPITAL:
						af = VK_MODIFIERS.VK_SHIFT
					modname = af.name
					if modname in ['VK_SHIFT', 'VK_CONTROL', 'VK_MENU']:
						modname = modname[:3] + 'L' + modname[3:]
					sc = self.keyboard_layout.vk_to_scancode(modname)
					modcodes.append(sc)
				for mod in modcodes:
					await asyncio.sleep(self.default_chardelay)
					await self.key_sender(mod, True)

				await asyncio.sleep(self.default_chardelay)
				await self.key_sender(scancode, True)
				await asyncio.sleep(self.default_chardelay)
				await self.key_sender(scancode, False)
				for mod in modcodes[::-1]:
					await asyncio.sleep(self.default_chardelay)
					await self.key_sender(mod, False)
				
		else:
			scancode = self.keyboard_layout.vk_to_scancode(key)
			await asyncio.sleep(self.default_chardelay)
			await self.key_sender(scancode, True)
			await asyncio.sleep(self.default_chardelay)
			await self.key_sender(scancode, False)
	

class DuckyReaderBase:
	def __init__(self, executor):
		self.executor = executor

	async def execute_line(self, line):
		try:
			line = line.strip()
			if line == '':
				return
			if line.find(' ') == -1:
				keyword = line.lower()
				data = []
			else:
				keyword, *data = line.split(' ')
				keyword = keyword.lower()
			
			if keyword.startswith('#') is True:
				return
			
			if keyword.startswith('rem'):
				if keyword[3:] != '':
					data.insert(0, keyword[3:])
				keyword = 'rem'
			
			if keyword.find('-') != -1:
				keyword, *temp = keyword.split('-')
				keyword = keyword.lower()
				data = temp + data
			
			if keyword.startswith('f') is True and (len(keyword) == 2 or len(keyword) == 3):
				keyid = int(keyword[1:])
				keyword = 'function'
				data.insert(0, str(keyid))
			fnct = self.executor.get_function(keyword)
			if len(data) > 0:
				await fnct(data)
			else:
				await fnct()
		
		except Exception as e:
			print('ERROR! Line: %s' % repr(line))
			raise e

	@staticmethod
	def from_file(filepath, executor):
		reader = DuckyReaderFile(filepath, executor)
		return reader

class DuckyReaderFile(DuckyReaderBase):
	def __init__(self, filepath, executor):
		DuckyReaderBase.__init__(self, executor)
		self.filepath = filepath
		self.file = open(filepath, 'r')

	async def parse(self):
		for line in self.file:
			line = line.strip()
			if len(line) == 0:
				continue
			await self.execute_line(line)


async def key_sender(scancode, is_pressed, as_char = False):
	#print(scancode)
	#print(is_pressed)
	return

async def amain():
	layout = KeyboardLayoutManager().get_layout_by_shortname('enus')
	from pathlib import Path
	try:
		for path in Path('/home/webdev/Desktop/usbrubberducky-payloads/payloads/').rglob('*'):
			print('Now processing %s' % path)
			if path.is_dir():
				continue
			if path.name.endswith('.md') is True or path.name.endswith('.bat') is True:
				continue
			executor = DuckyExecutorBase(layout, key_sender)
			reader = DuckyReaderFile.from_file(path, executor)
			await reader.parse()
	except Exception as e:
		traceback.print_exc()


def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()