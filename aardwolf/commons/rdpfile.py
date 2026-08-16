import copy
import enum
import ipaddress
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.target import RDPConnectionDialect, RDPTarget
from aardwolf.extensions.RDPECLIP.channel import RDPECLIPChannel
from aardwolf.protocol.T125.extendedinfopacket import PERF
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS


PathLike = Union[str, Path]
RDPValue = Union[int, str, bytes]


class RDPFileType(enum.Enum):
	INTEGER = 'i'
	STRING = 's'
	BINARY = 'b'


# Names mstsc writes as integers. Unknown names default to string unless the
# assigned Python value is int/bytes.
_INTEGER_PROPERTIES = frozenset({
	'administrative session',
	'allow desktop composition',
	'allow font smoothing',
	'audiocapturemode',
	'audiomode',
	'audioqualitymode',
	'authentication level',
	'autoreconnect max retries',
	'autoreconnection enabled',
	'bandwidthautodetect',
	'bitmapcachepersistenable',
	'bitmapcachesize',
	'compression',
	'connect to console',
	'connection type',
	'desktop size id',
	'desktopheight',
	'desktopscalefactor',
	'desktopwidth',
	'disable connection sharing',
	'disable ctrl+alt+del',
	'disable cursor setting',
	'disable full window drag',
	'disable menu anims',
	'disable themes',
	'disable wallpaper',
	'disableconnectionsharing',
	'displayconnectionbar',
	'dynamic resolution',
	'enablecredsspsupport',
	'enablerdsaadauth',
	'enableworkspacereconnect',
	'encode redirected video capture',
	'gatewaybrokeringtype',
	'gatewaycredentialssource',
	'gatewayprofileusagemethod',
	'gatewayusagemethod',
	'keyboardhook',
	'maximizetocurrentdisplays',
	'negotiate security layer',
	'networkautodetect',
	'pinconnectionbar',
	'prompt for credentials',
	'promptcredentialonce',
	'public mode',
	'rdgiskdcproxy',
	'redirectclipboard',
	'redirectcomports',
	'redirectdirectx',
	'redirected video capture encoding quality',
	'redirectlocation',
	'redirectposdevices',
	'redirectprinters',
	'redirectsmartcards',
	'redirectwebauthn',
	'remoteapplicationexpandcmdline',
	'remoteapplicationexpandworkingdir',
	'remoteapplicationmode',
	'restricted admin',
	'restrictedadmin',
	'screen mode id',
	'server port',
	'session bpp',
	'singlemoninwindowedmode',
	'smart sizing',
	'targetisaadjoined',
	'use multimon',
	'use redirection server name',
	'videoplaybackmode',
})

_BINARY_PROPERTIES = frozenset({
	'password 51',
})

_NAME_ALIASES = {
	'restrictedadmin': 'restricted admin',
	'connect to console': 'connect to console',
}

_DESKTOP_SIZE_ID = {
	0: (640, 480),
	1: (800, 600),
	2: (1024, 768),
	3: (1280, 1024),
	4: (1600, 1200),
}

_UTF16LE_BOMS = (b'\xff\xfe',)
_UTF16BE_BOMS = (b'\xfe\xff',)
_UTF8_BOMS = (b'\xef\xbb\xbf',)


def _normalize_name(name: str) -> str:
	key = ' '.join(name.strip().lower().split())
	return _NAME_ALIASES.get(key, key)


def _type_for_name(name: str, value: RDPValue) -> RDPFileType:
	key = _normalize_name(name)
	if key in _BINARY_PROPERTIES or isinstance(value, (bytes, bytearray)):
		return RDPFileType.BINARY
	if key in _INTEGER_PROPERTIES or isinstance(value, bool) or (isinstance(value, int) and not isinstance(value, bool)):
		return RDPFileType.INTEGER
	return RDPFileType.STRING


def _decode_rdp_bytes(data: bytes) -> str:
	if data.startswith(_UTF16LE_BOMS[0]):
		return data.decode('utf-16-le')
	if data.startswith(_UTF16BE_BOMS[0]):
		return data.decode('utf-16-be')
	if data.startswith(_UTF8_BOMS[0]):
		return data.decode('utf-8-sig')
	if len(data) >= 4 and data[1:2] == b'\x00' and data[3:4] == b'\x00':
		try:
			return data.decode('utf-16-le')
		except UnicodeDecodeError:
			pass
	return data.decode('utf-8')


def _encode_with_bom(text: str, encoding: str, bom: bool) -> bytes:
	encoding_norm = encoding.lower().replace('_', '-')
	payload = text.encode(encoding)
	if not bom:
		return payload
	if encoding_norm in ('utf-16-le', 'utf-16le'):
		return b'\xff\xfe' + payload
	if encoding_norm in ('utf-16-be', 'utf-16be'):
		return b'\xfe\xff' + payload
	if encoding_norm in ('utf-8', 'utf8'):
		return b'\xef\xbb\xbf' + payload
	return payload


def _parse_binary(value: str) -> bytes:
	hexstr = ''.join(value.split())
	if hexstr == '':
		return b''
	try:
		return bytes.fromhex(hexstr)
	except ValueError as exc:
		raise ValueError('Invalid binary (hex) RDP value: %r' % value) from exc


def _format_binary(value: bytes) -> str:
	return value.hex().upper()


def split_rdp_address(address: str, default_port: Optional[int] = None) -> Tuple[str, Optional[int]]:
	"""Split ``host``, ``host:port``, or ``[ipv6]:port`` into host and port."""
	address = address.strip()
	if address == '':
		raise ValueError('RDP full address is empty')
	if address.startswith('['):
		end = address.find(']')
		if end < 0:
			raise ValueError('Invalid IPv6 RDP address: %r' % address)
		host = address[1:end]
		rest = address[end + 1:]
		if rest == '':
			return host, default_port
		if rest.startswith(':') and rest[1:].isdigit():
			return host, int(rest[1:])
		raise ValueError('Invalid IPv6 RDP address: %r' % address)
	if address.count(':') == 1:
		host, port_s = address.rsplit(':', 1)
		if port_s.isdigit():
			return host, int(port_s)
	return address, default_port


def split_rdp_username(username: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
	"""Return ``(user, domain)`` from ``DOMAIN\\user`` or a bare / UPN name."""
	if username is None or username == '':
		return None, None
	if '\\' in username:
		domain, user = username.split('\\', 1)
		return user or None, domain or None
	return username, None


def _host_to_target_fields(host: str) -> Tuple[str, Optional[str]]:
	try:
		ipaddress.ip_address(host)
	except ValueError:
		return host, host
	return host, None


class RDPFile:
	"""Parse, create, and write Microsoft ``.rdp`` connection files.

	Each line is ``name:type:value`` where type is ``i`` (int), ``s`` (string),
	or ``b`` (hex-encoded binary). mstsc writes UTF-16 LE with a BOM.

	Unknown properties are kept so a file can be round-tripped. The DPAPI blob
	in ``password 51`` is stored as bytes and is not decrypted.
	"""

	def __init__(self):
		self._order: List[str] = []
		self._items: Dict[str, Tuple[str, RDPFileType, RDPValue]] = {}

	@staticmethod
	def from_text(text: str) -> 'RDPFile':
		rdp = RDPFile()
		if text.startswith('\ufeff'):
			text = text[1:]
		for lineno, raw_line in enumerate(text.splitlines(), start=1):
			line = raw_line.strip()
			if line == '' or line.startswith('#'):
				continue
			parts = line.split(':', 2)
			if len(parts) != 3:
				raise ValueError('Malformed RDP line %s: %r' % (lineno, raw_line))
			name, type_token, value = parts
			name = name.strip()
			type_token = type_token.strip().lower()
			if name == '' or type_token not in ('i', 's', 'b'):
				raise ValueError('Malformed RDP line %s: %r' % (lineno, raw_line))
			rdp_type = RDPFileType(type_token)
			if rdp_type is RDPFileType.INTEGER:
				try:
					parsed: RDPValue = int(value, 10)
				except ValueError as exc:
					raise ValueError('Invalid integer on RDP line %s: %r' % (lineno, raw_line)) from exc
			elif rdp_type is RDPFileType.BINARY:
				parsed = _parse_binary(value)
			else:
				parsed = value
			rdp._set(name, rdp_type, parsed)
		return rdp

	@staticmethod
	def from_bytes(data: bytes) -> 'RDPFile':
		return RDPFile.from_text(_decode_rdp_bytes(data))

	@staticmethod
	def from_file(path: PathLike) -> 'RDPFile':
		return RDPFile.from_bytes(Path(path).read_bytes())

	@staticmethod
	def from_settings(
			target: Optional[RDPTarget] = None,
			iosettings: Optional[RDPIOSettings] = None,
			username: Optional[str] = None,
			domain: Optional[str] = None) -> 'RDPFile':
		rdp = RDPFile()
		if target is not None:
			host = target.get_hostname_or_ip()
			if host:
				rdp['full address'] = host
			if target.port is not None:
				rdp['server port'] = int(target.port)
			if domain is None and target.domain:
				domain = target.domain
		if username:
			rdp['username'] = username
		if domain:
			rdp['domain'] = domain
		if iosettings is not None:
			rdp['desktopwidth'] = int(iosettings.video_width)
			rdp['desktopheight'] = int(iosettings.video_height)
			rdp['session bpp'] = int(iosettings.video_bpp_max)
			rdp['compression'] = 0 if iosettings.bulk_compression_max_type is None else 1
			rdp['redirectclipboard'] = 1 if RDPECLIPChannel in iosettings.channels else 0
			flags = iosettings.performance_flags or PERF(0)
			rdp['disable wallpaper'] = 1 if PERF.DISABLE_WALLPAPER in flags else 0
			rdp['disable full window drag'] = 1 if PERF.DISABLE_FULLWINDOWDRAG in flags else 0
			rdp['disable menu anims'] = 1 if PERF.DISABLE_MENUANIMATIONS in flags else 0
			rdp['disable themes'] = 1 if PERF.DISABLE_THEMING in flags else 0
			rdp['disable cursor setting'] = 1 if PERF.DISABLE_CURSORSETTINGS in flags else 0
			rdp['allow font smoothing'] = 1 if PERF.ENABLE_FONT_SMOOTHING in flags else 0
			rdp['allow desktop composition'] = 1 if PERF.ENABLE_DESKTOP_COMPOSITION in flags else 0
			if iosettings.supported_protocols is not None:
				rdp['enablecredsspsupport'] = int(
					bool(iosettings.supported_protocols & (SUPP_PROTOCOLS.HYBRID | SUPP_PROTOCOLS.HYBRID_EX))
				)
		return rdp

	def to_text(self) -> str:
		lines = []
		for key in self._order:
			name, rdp_type, value = self._items[key]
			if rdp_type is RDPFileType.INTEGER:
				rendered = str(int(value))
			elif rdp_type is RDPFileType.BINARY:
				rendered = _format_binary(bytes(value))
			else:
				rendered = '' if value is None else str(value)
			lines.append('%s:%s:%s' % (name, rdp_type.value, rendered))
		return '\r\n'.join(lines) + ('\r\n' if lines else '')

	def to_bytes(self, encoding: str = 'utf-16-le', bom: bool = True) -> bytes:
		return _encode_with_bom(self.to_text(), encoding, bom)

	def to_file(self, path: PathLike, encoding: str = 'utf-16-le', bom: bool = True) -> None:
		Path(path).write_bytes(self.to_bytes(encoding=encoding, bom=bom))

	def to_target(
			self,
			timeout: int = 1,
			unsafe_ssl: Optional[bool] = None,
			dialect: RDPConnectionDialect = RDPConnectionDialect.RDP) -> RDPTarget:
		address = self.get_str('full address')
		if not address:
			raise ValueError('RDP file has no "full address"')
		explicit_port = self.get_int('server port')
		host, port = split_rdp_address(address, default_port=explicit_port)
		if explicit_port is not None:
			port = explicit_port
		if port is None:
			port = 3389
		ip, hostname = _host_to_target_fields(host)
		_, username_domain = split_rdp_username(self.get_str('username'))
		domain = self.get_str('domain') or username_domain
		if unsafe_ssl is None:
			unsafe_ssl = self.get_int('authentication level') == 0
		return RDPTarget(
			ip=ip,
			port=port,
			hostname=hostname,
			timeout=timeout,
			domain=domain,
			unsafe_ssl=bool(unsafe_ssl),
			dialect=dialect,
		)

	def to_iosettings(self, base: Optional[RDPIOSettings] = None) -> RDPIOSettings:
		settings = copy.deepcopy(base) if base is not None else RDPIOSettings()
		width = self.get_int('desktopwidth')
		height = self.get_int('desktopheight')
		if width is None or height is None:
			preset = _DESKTOP_SIZE_ID.get(self.get_int('desktop size id'))
			if preset is not None:
				preset_w, preset_h = preset
				if width is None:
					width = preset_w
				if height is None:
					height = preset_h
		if width is not None:
			settings.video_width = width
		if height is not None:
			settings.video_height = height
		bpp = self.get_int('session bpp')
		if bpp is not None:
			settings.video_bpp_max = bpp
			if bpp not in settings.video_bpp_supported:
				settings.video_bpp_supported = list(settings.video_bpp_supported) + [bpp]
		if self.get_int('compression') == 0:
			settings.bulk_compression_max_type = None
		flags = settings.performance_flags if settings.performance_flags is not None else PERF(0)
		flags = _apply_flag(flags, PERF.DISABLE_WALLPAPER, self.get_int('disable wallpaper'), enable_when=1)
		flags = _apply_flag(flags, PERF.DISABLE_FULLWINDOWDRAG, self.get_int('disable full window drag'), enable_when=1)
		flags = _apply_flag(flags, PERF.DISABLE_MENUANIMATIONS, self.get_int('disable menu anims'), enable_when=1)
		flags = _apply_flag(flags, PERF.DISABLE_THEMING, self.get_int('disable themes'), enable_when=1)
		flags = _apply_flag(flags, PERF.DISABLE_CURSORSETTINGS, self.get_int('disable cursor setting'), enable_when=1)
		flags = _apply_flag(flags, PERF.ENABLE_FONT_SMOOTHING, self.get_int('allow font smoothing'), enable_when=1)
		flags = _apply_flag(flags, PERF.ENABLE_DESKTOP_COMPOSITION, self.get_int('allow desktop composition'), enable_when=1)
		settings.performance_flags = flags
		clipboard = self.get_int('redirectclipboard')
		if clipboard == 0:
			settings.channels = [channel for channel in settings.channels if channel is not RDPECLIPChannel]
		elif clipboard == 1 and RDPECLIPChannel not in settings.channels:
			settings.channels = list(settings.channels) + [RDPECLIPChannel]
		if self.get_int('enablecredsspsupport') == 0:
			settings.supported_protocols = SUPP_PROTOCOLS.RDP | SUPP_PROTOCOLS.SSL
		return settings

	@property
	def username(self) -> Optional[str]:
		user, _ = split_rdp_username(self.get_str('username'))
		return user

	@property
	def domain(self) -> Optional[str]:
		explicit = self.get_str('domain')
		if explicit:
			return explicit
		_, domain = split_rdp_username(self.get_str('username'))
		return domain

	@property
	def alternate_shell(self) -> Optional[str]:
		value = self.get_str('alternate shell')
		return value or None

	@property
	def working_dir(self) -> Optional[str]:
		value = self.get_str('shell working directory')
		return value or None

	@property
	def gateway_hostname(self) -> Optional[str]:
		value = self.get_str('gatewayhostname')
		return value or None

	@property
	def restricted_admin(self) -> bool:
		return self.get_int('restricted admin') == 1

	@property
	def password51(self) -> Optional[bytes]:
		value = self.get('password 51')
		if value is None or value == b'':
			return None
		return bytes(value)

	def get(self, name: str, default: Optional[RDPValue] = None) -> Optional[RDPValue]:
		item = self._items.get(_normalize_name(name))
		if item is None:
			return default
		return item[2]

	def get_int(self, name: str, default: Optional[int] = None) -> Optional[int]:
		value = self.get(name)
		if value is None or value == '':
			return default
		return int(value)

	def get_str(self, name: str, default: Optional[str] = None) -> Optional[str]:
		value = self.get(name)
		if value is None:
			return default
		return str(value)

	def get_bytes(self, name: str, default: Optional[bytes] = None) -> Optional[bytes]:
		value = self.get(name)
		if value is None:
			return default
		if isinstance(value, str):
			return _parse_binary(value)
		return bytes(value)

	def set(self, name: str, value: RDPValue, rdp_type: Optional[RDPFileType] = None) -> None:
		if rdp_type is None:
			existing = self._items.get(_normalize_name(name))
			rdp_type = existing[1] if existing is not None else _type_for_name(name, value)
		if rdp_type is RDPFileType.INTEGER:
			value = int(value)
		elif rdp_type is RDPFileType.BINARY:
			if isinstance(value, str):
				value = _parse_binary(value)
			else:
				value = bytes(value)
		else:
			value = '' if value is None else str(value)
		self._set(name, rdp_type, value)

	def keys(self) -> Iterable[str]:
		return (self._items[key][0] for key in self._order)

	def items(self) -> Iterable[Tuple[str, RDPValue]]:
		return ((self._items[key][0], self._items[key][2]) for key in self._order)

	def _set(self, name: str, rdp_type: RDPFileType, value: RDPValue) -> None:
		key = _normalize_name(name)
		if key not in self._items:
			self._order.append(key)
		# Keep the first spelling we saw so round-trips stay stable.
		original = self._items[key][0] if key in self._items else name.strip()
		self._items[key] = (original, rdp_type, value)

	def __contains__(self, name: object) -> bool:
		if not isinstance(name, str):
			return False
		return _normalize_name(name) in self._items

	def __getitem__(self, name: str) -> RDPValue:
		item = self._items.get(_normalize_name(name))
		if item is None:
			raise KeyError(name)
		return item[2]

	def __setitem__(self, name: str, value: RDPValue) -> None:
		self.set(name, value)

	def __delitem__(self, name: str) -> None:
		key = _normalize_name(name)
		if key not in self._items:
			raise KeyError(name)
		del self._items[key]
		self._order.remove(key)

	def __len__(self) -> int:
		return len(self._order)

	def __iter__(self) -> Iterator[str]:
		return iter(self.keys())

	def __repr__(self) -> str:
		return 'RDPFile(%r)' % (dict(self.items()),)


def _apply_flag(flags: PERF, bit: PERF, value: Optional[int], enable_when: int) -> PERF:
	if value is None:
		return flags
	if value == enable_when:
		return flags | bit
	return flags & ~bit
