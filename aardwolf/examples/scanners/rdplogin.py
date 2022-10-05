import copy
from asysocks.unicomm.common.scanner.common import *
from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS


class RDPLoginRes:
	def __init__(self, success):
		self.success = success

	def get_header(self):
		return ['success']

	def to_line(self, separator = '\t'):
		return str(self.success)

class RDPLoginScanner:
	def __init__(self, factory:RDPConnectionFactory):
		self.factory:RDPConnectionFactory = factory
		self.flags_test = [SUPP_PROTOCOLS.HYBRID_EX, None]

	async def run(self, targetid, target, out_queue):
		try:
			for i, proto in enumerate(self.flags_test):
				result = 'TRUE'
				if proto == None:
					result = 'MAYBE'
				ios = self.factory.get_settings()
				ios.supported_protocols = proto
				async with self.factory.create_connection_newtarget(target, ios) as connection:
					_, err = await connection.connect()
					if err is not None:
						result = 'FALSE'
					
					if result == 'FALSE' and i != (len(self.flags_test)-1):
						# avoid printing NO multiple times
						continue
					
					await out_queue.put(ScannerData(target, RDPLoginRes(result)))
					if result == 'TRUE':
						break

		except Exception as e:
			await out_queue.put(ScannerError(target, e))
