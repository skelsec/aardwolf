
from aardwolf.commons.connection.url import RDPConnectionURL
from aardwolf.commons.connection.credential import RDPCredentialTypes

RDP_CONNECTION_PARAM_MANDATORY = ['domain','user','password','auth_type', 'timeout', 'protocol']


class RDPConnectionParams:
	def __init__(self):
		pass
	
	@staticmethod
	def extend_parser(parser):
		group = parser.add_argument_group('Parameter based connection')
		group.add_argument('-d', '--domain', default='.', help='Domainname')
		group.add_argument('-u', '--user', help='Username')
		group.add_argument('-p', '--password', help='Password (or other secret for authentication)')
		group.add_argument('-a', '--auth-type', choices=[e.value for e in RDPCredentialTypes], default='ntlm-password', help='authentication type')
		group.add_argument('-t', '--timeout', type=int, default=5, help='Connection timeout')
		group.add_argument('--protocol', choices=['RDP', 'RDP2', 'RDP3'], default='RDP2', help='RDP protocol version')
		group.add_argument('--dc', help='DC ip for kerberos')

	@staticmethod
	def parse_args(args):
		for p in RDP_CONNECTION_PARAM_MANDATORY:
			if hasattr(args, p) is False:
				raise Exception('The parameter "%s" is mandatory for parameter based connection setup!' % p)
			if getattr(args, p) is None:
				raise Exception('The parameter "%s" cannot be empty!' % p)

		url_template = '{protocol}+{auth_type}://{domainname}\\{username}:{password}@{host}/'
		params = {
			'protocol'  : args.protocol,
			'auth_type' : args.auth_type,
			'domainname': args.domain,
			'username'  : args.user,
			'password'  : args.password,
			'host'      : args.host if hasattr(args, 'host') else None,
		}

		url = url_template.format(**params)
		print(url)
		return url


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(prog='TEST')

	RDPConnectionParams.extend_parser(parser)

	print(parser)

	args = parser.parse_args()

	RDPConnectionParams.parse_args(args)
