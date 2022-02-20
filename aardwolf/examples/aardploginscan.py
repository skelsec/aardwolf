import traceback
import uuid
import asyncio
import logging
import copy
import json

from aardwolf import logger
from aardwolf.commons.url import RDPConnectionURL
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.examples.scancommons.targetgens import *
from aardwolf.examples.scancommons.internal import *
from aardwolf.examples.scancommons.utils import *
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS
from aardwolf.commons.queuedata.constants import VIDEO_FORMAT
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
			return '[R] %s | %s | %s' % (self.target_id, self.target, self.obj)

		elif self.otype == 'progress':
			return '[P][%s/%s][%s] %s' % (self.obj.total_finished, self.obj.total_targets, str(self.obj.gens_finished), self.obj.current_finished)

		else:
			return '[UNK]'
	
	def to_dict(self):
		if self.otype == 'result':
			return {
				'target' : self.target,
				'target_id' : self.target_id,
				'result': str(self.obj),
				'otype': self.otype,
			}
	
	def to_tsv(self):
		if self.otype == 'result':
			return '%s\t%s\t%s' % (self.target, self.target_id, self.obj)
	
	def to_json(self):
		t = self.to_dict()
		if t is not None:
			return json.dumps(self.to_dict())


class RDPLoginScanner:
	def __init__(self, rdp_url, iosettings:RDPIOSettings, worker_count = 10, out_file = None, out_format = 'str', show_pbar = True, task_q = None, ext_result_q = None):
		self.target_gens = []
		self.rdp_mgr = rdp_url
		if isinstance(rdp_url, RDPConnectionURL) is False:
			self.rdp_mgr = RDPConnectionURL(rdp_url)
		self.worker_count = worker_count
		self.task_q = task_q
		self.res_q = None
		self.workers = []
		self.result_processing_task = None
		self.out_file = out_file
		self.show_pbar = show_pbar
		self.ext_result_q = ext_result_q
		self.enum_url = False
		self.out_format = out_format

		self.iosettings = iosettings
		self.flags_test = [SUPP_PROTOCOLS.HYBRID_EX, None]

		self.__gens_finished = False
		self.__total_targets = 0
		self.__total_finished = 0
		self.__total_errors = 0

	async def __executor(self, tid, target):
		try:
			for i, proto in enumerate(self.flags_test):
				result = 'YES'
				if proto == None:
					result = 'MAYBE'
				ios = copy.deepcopy(self.iosettings)
				ios.supported_protocols = proto
				async with self.rdp_mgr.create_connection_newtarget(target, ios) as connection:
					_, err = await connection.connect()
					if err is not None:
						result = 'NO'
					
					if result == 'NO' and i != (len(self.flags_test)-1):
						# avoid printing NO multiple times
						continue

					await self.res_q.put(EnumResult(tid, target, result, status = EnumResultStatus.RESULT))
					if result == 'YES':
						break

		except asyncio.CancelledError:
			return
		except Exception as e:
			traceback.print_exc()
			await self.res_q.put(EnumResult(tid, target, None, error = e, status = EnumResultStatus.ERROR))
		finally:
			await self.res_q.put(EnumResult(tid, target, None, status = EnumResultStatus.FINISHED))
			

	async def worker(self):
		try:
			while True:
				indata = await self.task_q.get()
				if indata is None:
					return
				
				tid, target = indata
				try:
					await asyncio.wait_for(self.__executor(tid, target), timeout=10)
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
				pbar['targets']  = tqdm(desc='Targets ', unit='', position=0)
				pbar['yes']      = tqdm(desc='Yes     ', unit='', position=1)
				pbar['no']       = tqdm(desc='No      ', unit='', position=2)
				pbar['maybe']    = tqdm(desc='Maybe   ', unit='', position=3)
				pbar['errors']   = tqdm(desc='Errors  ', unit='', position=4)
				pbar['finished'] = tqdm(desc='Finished', unit='', position=5)

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

					if len(out_buffer) >= 100 or final_iter and self.ext_result_q is None:
						out_data = ''
						if self.out_format == 'str':
							out_data = '\r\n'.join([str(x) for x in out_buffer])
						elif self.out_format == 'tsv':
							for line in [x.to_tsv() for x in out_buffer]:
								if line is not None:
									out_data += line + '\r\n'
						elif self.out_format == 'json':
							for line in [x.to_json() for x in out_buffer]:
								if line is not None:
									out_data += line + '\r\n'
						if self.out_file is None:
							print(out_data)
						else:
							with open(self.out_file, 'a', newline = '') as f:
								f.write(out_data)
						if self.show_pbar is True:
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
							if er.result in ['YES', 'NO', 'MAYBE']:
								pbar[er.result.lower()].update(1)
							

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

	parser = argparse.ArgumentParser(description='RDP login scanner', formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-v', '--verbose', action='count', default=0)
	parser.add_argument('-w', '--worker-count', type=int, default=50, help='Parallell count')
	parser.add_argument('-o', '--out-file', help='Output file path.')
	parser.add_argument('--progress', action='store_true', help='Show progress bar. Pleasue use out-file with this!!')
	parser.add_argument('--tsv', action='store_true', help='Output results in TSV format')
	parser.add_argument('--json', action='store_true', help='Output results in JSON format')
	parser.add_argument('-s', '--stdin', action='store_true', help='Read targets from stdin')
	parser.add_argument('url', help='Connection URL base, target can be set to anything. Example: "rdp+ntlm-password://TEST\\victim:Password!1@10.10.10.2"')
	parser.add_argument('targets', nargs='*', help = 'Hostname or IP address or file with a list of targets')

	args = parser.parse_args()

	if args.verbose >=1:
		logger.setLevel(logging.WARNING)

	if args.verbose > 2:
		print('setting deepdebug')
		logger.setLevel(1) #enabling deep debug
		asyncio.get_event_loop().set_debug(True)
		logging.basicConfig(level=logging.DEBUG)

	oformat = 'str'
	if args.tsv is True:
		oformat = 'tsv'
	if args.json is True:
		oformat = 'json'

	rdp_url = args.url

	iosettings = RDPIOSettings()
	iosettings.channels = []
	iosettings.video_out_format = VIDEO_FORMAT.RAW
	iosettings.clipboard_use_pyperclip = False

	enumerator = RDPLoginScanner(
		rdp_url,
		iosettings,
		worker_count = args.worker_count,
		out_file = args.out_file,
		show_pbar = args.progress,
		out_format=oformat,
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