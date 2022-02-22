import traceback
import uuid
import asyncio
import logging

from aardwolf import logger
from aardwolf.commons.url import RDPConnectionURL
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.examples.scancommons.targetgens import *
from aardwolf.examples.scancommons.internal import *
from aardwolf.examples.scancommons.utils import *
from aardwolf.commons.queuedata.constants import MOUSEBUTTON, VIDEO_FORMAT
from tqdm import tqdm

class EnumResultFinal:
	def __init__(self, obj, otype, err, target, target_id):
		self.obj = obj
		self.otype = otype
		self.err = err
		self.target = target
		self.target_id = target_id


	def __str__(self):
		if self.err is not None:
			return '[E] %s | %s | %s' % (self.target, self.err)

		elif self.otype == 'result':
			return '[S] %s ' % (self.target)

		elif self.otype == 'progress':
			return '[P][%s/%s][%s] %s' % (self.obj.total_finished, self.obj.total_targets, str(self.obj.gens_finished), self.obj.current_finished)

		else:
			return '[UNK]'


class RDPScreenGrabberScanner:
	def __init__(self, rdp_url, iosettings, worker_count = 10, out_dir = None, screentime = 5, show_pbar = True, task_q = None, res_q = None, ext_result_q = None):
		self.target_gens = []
		self.rdp_mgr = rdp_url
		if isinstance(rdp_url, RDPConnectionURL) is False:
			self.rdp_mgr = RDPConnectionURL(rdp_url)
		self.worker_count = worker_count
		self.task_q = task_q
		self.res_q = res_q
		self.screentime = screentime
		self.workers = []
		self.result_processing_task = None
		self.out_dir = out_dir
		self.show_pbar = show_pbar
		self.ext_result_q = ext_result_q
		self.enum_url = False

		self.iosettings = iosettings

		self.__gens_finished = False
		self.__total_targets = 0
		self.__total_finished = 0
		self.__total_errors = 0

	async def __executor(self, tid, target):
		connection = None
		try:
			connection = self.rdp_mgr.create_connection_newtarget(target, self.iosettings)
			_, err = await connection.connect()
			if err is not None:
				raise err
			
			await asyncio.sleep(self.screentime)

		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			await self.res_q.put(EnumResult(tid, target, None, error = e, status = EnumResultStatus.ERROR))
		finally:
			if connection is not None and connection.desktop_buffer_has_data is True:
				buffer = connection.get_desktop_buffer(VIDEO_FORMAT.PIL)
				
				if self.ext_result_q is None:
					filename = 'screen_%s_%s.png' % (target, tid)
					buffer.save(filename,'png')
					await self.res_q.put(EnumResult(tid, target, None, status = EnumResultStatus.RESULT))
				else:
					await self.res_q.put(EnumResult(tid, target, buffer, status = EnumResultStatus.RESULT))

			await self.res_q.put(EnumResult(tid, target, None, status = EnumResultStatus.FINISHED))
			

	async def worker(self):
		try:
			while True:
				indata = await self.task_q.get()
				if indata is None:
					return
				
				tid, target = indata
				try:
					await asyncio.wait_for(self.__executor(tid, target), timeout=self.screentime+5)
				except asyncio.CancelledError:
					return
				except asyncio.TimeoutError as e:
					await self.res_q.put(EnumResult(tid, target, None, error = e, status = EnumResultStatus.ERROR))
					await self.res_q.put(EnumResult(tid, target, None, status = EnumResultStatus.FINISHED))
					continue
				except Exception as e:
					logger.exception('worker')
					continue
		except asyncio.CancelledError:
			return
				
		except Exception as e:
			return e

	async def result_processing(self):
		try:
			pbar = None
			if self.show_pbar is True:
				pbar = {}
				pbar['targets']    = tqdm(desc='Targets     ', unit='', position=0)
				pbar['screencaps'] = tqdm(desc='Screencaps  ', unit='', position=1)
				pbar['errors']     = tqdm(desc='Conn Errors ', unit='', position=2)

			out_buffer = []
			final_iter = False
			while True:
				try:
					if self.__gens_finished is True and self.show_pbar is True and pbar['targets'].total is None:
						pbar['targets'].total = self.__total_targets
						for key in pbar:
							pbar[key].refresh()

					if self.ext_result_q is not None:
						out_buffer = []

					if len(out_buffer) >= 10 or final_iter and self.ext_result_q is None:
						out_data = ''
						if self.show_pbar is False:
							out_data = '\r\n'.join([str(x) for x in out_buffer])
							print(out_data)
						else:
							for key in pbar:
								pbar[key].refresh()
						
						out_buffer = []
						out_data = ''

					if final_iter:
						asyncio.create_task(self.terminate())
						return
					try:
						er = await asyncio.wait_for(self.res_q.get(), timeout = 5)
					except asyncio.TimeoutError:
						if self.show_pbar is True:
							for key in pbar:
								pbar[key].refresh()

						if self.__total_finished == self.__total_targets and self.__gens_finished is True:
							final_iter = True
						continue
					
					if er.status == EnumResultStatus.FINISHED:
						self.__total_finished += 1
						if self.show_pbar is True:
							pbar['finished'].update(1)

						obj = EnumProgress(self.__total_targets, self.__total_finished, self.__gens_finished, er.target)
						if self.ext_result_q is not None:
							await self.ext_result_q.put(EnumResultFinal(obj, 'progress', None, er.target, er.target_id))
						out_buffer.append(EnumResultFinal(obj, 'progress', None, er.target, er.target_id))
						if self.__total_finished == self.__total_targets and self.__gens_finished is True:
							final_iter = True
							continue
							
					if er.status == EnumResultStatus.RESULT:
						if self.ext_result_q is not None:
							await self.ext_result_q.put(EnumResultFinal(er.result, 'result', None, er.target, er.target_id))
						out_buffer.append(EnumResultFinal(er.result, 'result', None, er.target, er.target_id))
						if self.show_pbar is True:
							pbar['screencaps'].update(1)

					if er.status == EnumResultStatus.ERROR:
						self.__total_errors += 1
						if self.show_pbar is True:
							pbar['errors'].update(1)


				except asyncio.CancelledError:
					return
				except Exception as e:
					logger.exception('result_processing inner')
					asyncio.create_task(self.terminate())
					return
		except asyncio.CancelledError:
			return
		except Exception as e:
			logger.exception('result_processing')
			asyncio.create_task(self.terminate())
		finally:
			if self.ext_result_q is not None:
				await self.ext_result_q.put(EnumResultFinal(None, 'finished', None, None, None))

	async def terminate(self):
		for worker in self.workers:
			worker.cancel()
		if self.result_processing_task is not None:
			self.result_processing_task.cancel()		

	async def setup(self):
		try:
			if self.res_q is None:
				self.res_q = asyncio.Queue(self.worker_count)
				self.result_processing_task = asyncio.create_task(self.result_processing())
			if self.task_q is None:
				self.task_q = asyncio.Queue(self.worker_count)

			for _ in range(self.worker_count):
				self.workers.append(asyncio.create_task(self.worker()))

			return True, None
		except Exception as e:
			return None, e

	async def __generate_targets(self):
		if self.enum_url is True:
			self.__total_targets += 1
			await self.task_q.put((str(uuid.uuid4()), self.rdp_mgr.get_target().get_hostname_or_ip()))
			
		for target_gen in self.target_gens:
			async for uid, target, err in target_gen.generate():
				if err is not None:
					print('Target gen error! %s' % err)
					break
				
				self.__total_targets += 1
				await self.task_q.put((uid, target))
				await asyncio.sleep(0)

		self.__gens_finished = True
	
	async def run(self):
		try:
			_, err = await self.setup()
			if err is not None:
				raise err
			
			gen_task = asyncio.create_task(self.__generate_targets())
			
			await asyncio.gather(*self.workers)
			await self.result_processing_task
			return True, None
		except Exception as e:
			logger.exception('run')
			return None, e

async def amain():
	import argparse
	import sys

	parser = argparse.ArgumentParser(description='RDP/VNC Screen grabber', formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('--screentime', type=int, default=5, help='Time to wait for desktop image')
	parser.add_argument('-w', '--worker-count', type=int, default=50, help='Parallell count')
	parser.add_argument('-o', '--out-dir', help='Output directory path.')
	parser.add_argument('--progress', action='store_true', help='Show progress bar')
	parser.add_argument('-s', '--stdin', action='store_true', help='Read targets from stdin')
	parser.add_argument('--res', default = '1024x768', help='Resolution in "WIDTHxHEIGHT" format. Default: "1024x768"')
	parser.add_argument('url', help='Connection URL base, target can be set to anything. Example: "rdp+ntlm-password://TEST\\victim:Password!1@10.10.10.2"')
	parser.add_argument('targets', nargs='*', help = 'Hostname or IP address or file with a list of targets')

	args = parser.parse_args()

	if args.verbose >=1:
		logger.setLevel(logging.DEBUG)

	if args.verbose > 2:
		print('setting deepdebug')
		logger.setLevel(1) #enabling deep debug
		asyncio.get_event_loop().set_debug(True)
		logging.basicConfig(level=logging.DEBUG)

	rdp_url = args.url
	width, height = args.res.upper().split('X')
	height = int(height)
	width = int(width)

	iosettings = RDPIOSettings()
	iosettings.channels = []
	iosettings.video_width = width
	iosettings.video_height = height
	iosettings.video_bpp_min = 15 #servers dont support 8 any more :/
	iosettings.video_bpp_max = 32
	iosettings.video_out_format = VIDEO_FORMAT.PNG #PIL produces incorrect picture for some reason?! TODO: check bug
	iosettings.clipboard_use_pyperclip = False

	enumerator = RDPScreenGrabberScanner(
		rdp_url,
		iosettings,
		worker_count = args.worker_count,
		out_dir = args.out_dir,
		show_pbar = args.progress,
		screentime = args.screentime,
	)
	
	notfile = []
	if len(args.targets) == 0 and args.stdin is True:
		enumerator.target_gens.append(ListTargetGen(sys.stdin))
	else:
		for target in args.targets:
			try:
				f = open(target, 'r')
				f.close()
				enumerator.target_gens.append(FileTargetGen(target))
			except:
				notfile.append(target)
	
	if len(notfile) > 0:
		enumerator.target_gens.append(ListTargetGen(notfile))

	if len(enumerator.target_gens) == 0:
		enumerator.enum_url = True

	await enumerator.run()

def main():
	asyncio.run(amain())

if __name__ == '__main__':
	main()