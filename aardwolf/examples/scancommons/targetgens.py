import uuid
import ipaddress

class FileTargetGen:
	def __init__(self, filename):
		self.filename = filename

	async def generate(self):
		try:
			with open(self.filename, 'r') as f:
				for line in f:
					line = line.strip()
					if line == '':
						continue
					yield str(uuid.uuid4()), line, None
		except Exception as e:
			yield None, None, e


class ListTargetGen:
	def __init__(self, targets):
		self.targets = targets

	async def generate(self):
		try:
			for target in self.targets:
				target = target.strip()
				try:
					ip = ipaddress.ip_address(target)
					yield str(uuid.uuid4()),str(ip), None
				except:
					try:
						for ip in ipaddress.ip_network(target, strict = False):
							yield  str(uuid.uuid4()),str(ip), None
					except:
						yield str(uuid.uuid4()), target, None
		except Exception as e:
			yield None, None, e