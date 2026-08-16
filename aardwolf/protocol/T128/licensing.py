import enum
import hmac
import io
import os
import socket
import struct
from dataclasses import dataclass
from hashlib import md5, sha1
from typing import Callable

from arc4 import ARC4

from aardwolf.protocol.T124.userdata.serversecuritydata import SERVER_CERTIFICATE


SEC_ENCRYPT = 0x0008
SEC_LICENSE_PKT = 0x0080
PREAMBLE_VERSION_3_0 = 0x03
PREAMBLE_VERSION_MASK = 0x0F
MAX_LICENSE_FIELD_SIZE = 0xFFFF

KEY_EXCHANGE_ALG_RSA = 0x00000001
PLATFORM_ID = 0x04010000
PLATFORM_CHALLENGE_RESPONSE_VERSION = 0x0100
OTHER_PLATFORM_CHALLENGE_TYPE = 0xFF00
LICENSE_DETAIL_DETAIL = 0x0003


class LicensingProtocolError(Exception):
	pass


class LicenseMessageType(enum.IntEnum):
	LICENSE_REQUEST = 0x01
	PLATFORM_CHALLENGE = 0x02
	NEW_LICENSE = 0x03
	UPGRADE_LICENSE = 0x04
	LICENSE_INFO = 0x12
	NEW_LICENSE_REQUEST = 0x13
	PLATFORM_CHALLENGE_RESPONSE = 0x15
	ERROR_ALERT = 0xFF


class LicenseBlobType(enum.IntEnum):
	ANY = 0x0000
	DATA = 0x0001
	RANDOM = 0x0002
	CERTIFICATE = 0x0003
	ERROR = 0x0004
	ENCRYPTED_DATA = 0x0009
	KEY_EXCHANGE_ALGORITHM = 0x000D
	SCOPE = 0x000E
	CLIENT_USER_NAME = 0x000F
	CLIENT_MACHINE_NAME = 0x0010


class LicenseErrorCode(enum.IntEnum):
	ERR_INVALID_SERVER_CERTIFICATE = 0x00000001
	ERR_NO_LICENSE = 0x00000002
	ERR_INVALID_MAC = 0x00000003
	ERR_INVALID_SCOPE = 0x00000004
	ERR_NO_LICENSE_SERVER = 0x00000006
	STATUS_VALID_CLIENT = 0x00000007
	ERR_INVALID_CLIENT = 0x00000008
	ERR_INVALID_PRODUCT_ID = 0x0000000B
	ERR_INVALID_MESSAGE_LENGTH = 0x0000000C


class LicenseStateTransition(enum.IntEnum):
	ST_TOTAL_ABORT = 0x00000001
	ST_NO_TRANSITION = 0x00000002
	ST_RESET_PHASE_TO_START = 0x00000003
	ST_RESEND_LAST_MESSAGE = 0x00000004


class LicenseState(enum.Enum):
	INITIAL = 'initial'
	NEW_REQUEST_SENT = 'new-request-sent'
	CHALLENGE_RESPONSE_SENT = 'challenge-response-sent'
	COMPLETED = 'completed'


def _read_exact(buff: io.BytesIO, count: int, field_name: str) -> bytes:
	data = buff.read(count)
	if len(data) != count:
		raise LicensingProtocolError('Truncated licensing field %s' % field_name)
	return data


def _read_uint16(buff: io.BytesIO, field_name: str) -> int:
	return int.from_bytes(_read_exact(buff, 2, field_name), byteorder='little', signed=False)


def _read_uint32(buff: io.BytesIO, field_name: str) -> int:
	return int.from_bytes(_read_exact(buff, 4, field_name), byteorder='little', signed=False)


def _read_counted_bytes(buff: io.BytesIO, field_name: str) -> bytes:
	length = _read_uint32(buff, '%s length' % field_name)
	if length > MAX_LICENSE_FIELD_SIZE:
		raise LicensingProtocolError('%s is too large: %s bytes' % (field_name, length))
	return _read_exact(buff, length, field_name)


def _ensure_consumed(buff: io.BytesIO, field_name: str) -> None:
	if buff.read(1) != b'':
		raise LicensingProtocolError('Trailing data in %s' % field_name)


@dataclass(frozen=True)
class LicenseBinaryBlob:
	blob_type: int
	data: bytes

	@classmethod
	def from_buffer(cls, buff: io.BytesIO, field_name: str = 'binary blob'):
		blob_type = _read_uint16(buff, '%s type' % field_name)
		length = _read_uint16(buff, '%s length' % field_name)
		return cls(blob_type, _read_exact(buff, length, field_name))

	def to_bytes(self) -> bytes:
		if len(self.data) > MAX_LICENSE_FIELD_SIZE:
			raise LicensingProtocolError('Licensing blob is too large')
		return struct.pack('<HH', self.blob_type, len(self.data)) + self.data


@dataclass(frozen=True)
class LicensePDU:
	message_type: LicenseMessageType
	flags: int
	version: int
	body: bytes

	@classmethod
	def from_bytes(cls, data: bytes):
		if len(data) < 4:
			raise LicensingProtocolError('Truncated licensing preamble')

		try:
			message_type = LicenseMessageType(data[0])
		except ValueError as e:
			raise LicensingProtocolError('Unknown licensing message type 0x%02x' % data[0]) from e

		flags = data[1]
		version = flags & PREAMBLE_VERSION_MASK
		if version not in (2, 3):
			raise LicensingProtocolError('Unsupported licensing version %s' % version)

		message_size = int.from_bytes(data[2:4], byteorder='little', signed=False)
		if message_size < 4:
			raise LicensingProtocolError('Invalid licensing message size %s' % message_size)
		if message_size != len(data):
			raise LicensingProtocolError(
				'Licensing message size mismatch: header says %s, received %s'
				% (message_size, len(data))
			)

		return cls(message_type, flags & ~PREAMBLE_VERSION_MASK, version, data[4:])

	def to_bytes(self) -> bytes:
		message_size = 4 + len(self.body)
		if message_size > MAX_LICENSE_FIELD_SIZE:
			raise LicensingProtocolError('Licensing PDU is too large')
		flags = self.flags | self.version
		return bytes((self.message_type, flags)) + struct.pack('<H', message_size) + self.body


def extract_license_pdu(data: bytes):
	"""
	Returns ``(security_flags, LicensePDU)`` for licensing data, or ``None``
	when the MCS user data belongs to the following capability-exchange phase.

	The connection reader removes the security header from encrypted Standard
	RDP Security packets, but leaves a four-byte basic header on cleartext
	licensing packets. Both forms are accepted here.
	"""
	if len(data) >= 4 and data[0] in LicenseMessageType._value2member_map_:
		version = data[1] & PREAMBLE_VERSION_MASK
		message_size = int.from_bytes(data[2:4], byteorder='little', signed=False)
		if version in (2, 3) and message_size == len(data):
			return 0, LicensePDU.from_bytes(data)

	license_error = None
	if len(data) >= 4:
		security_flags = int.from_bytes(data[:2], byteorder='little', signed=False)
		if security_flags & SEC_LICENSE_PKT:
			try:
				if security_flags & SEC_ENCRYPT:
					raise LicensingProtocolError('Encrypted licensing data was not decrypted')
				return security_flags, LicensePDU.from_bytes(data[4:])
			except LicensingProtocolError as e:
				license_error = e

	# A Share Control Header starts with totalLength, whose bits can resemble
	# SEC_LICENSE_PKT. Recognize a complete Demand Active PDU before treating
	# a failed licensing-header candidate as malformed licensing data.
	if len(data) >= 6:
		total_length = int.from_bytes(data[:2], byteorder='little', signed=False)
		pdu_type = data[2] & 0x0F
		pdu_version = data[2] >> 4
		if total_length == len(data) and pdu_type == 0x01 and pdu_version == 0x01:
			return None

	if license_error is not None:
		raise license_error

	return None


@dataclass(frozen=True)
class LicenseErrorMessage:
	error_code: int
	state_transition: int
	error_info: LicenseBinaryBlob

	@classmethod
	def from_bytes(cls, data: bytes):
		buff = io.BytesIO(data)
		message = cls(
			_read_uint32(buff, 'licensing error code'),
			_read_uint32(buff, 'licensing state transition'),
			LicenseBinaryBlob.from_buffer(buff, 'licensing error information'),
		)
		_ensure_consumed(buff, 'licensing error message')
		return message


@dataclass(frozen=True)
class ServerLicenseRequest:
	server_random: bytes
	product_version: int
	company_name: bytes
	product_id: bytes
	key_exchange_list: LicenseBinaryBlob
	server_certificate: LicenseBinaryBlob
	scopes: tuple

	@classmethod
	def from_bytes(cls, data: bytes):
		buff = io.BytesIO(data)
		server_random = _read_exact(buff, 32, 'server random')
		product_version = _read_uint32(buff, 'product version')
		company_name = _read_counted_bytes(buff, 'company name')
		product_id = _read_counted_bytes(buff, 'product ID')
		key_exchange_list = LicenseBinaryBlob.from_buffer(buff, 'key exchange list')
		server_certificate = LicenseBinaryBlob.from_buffer(buff, 'server certificate')
		scope_count = _read_uint32(buff, 'scope count')
		# Every scope consumes at least its four-byte blob header.
		if scope_count > (len(data) - buff.tell()) // 4:
			raise LicensingProtocolError('Invalid licensing scope count %s' % scope_count)
		scopes = tuple(
			LicenseBinaryBlob.from_buffer(buff, 'scope %s' % i)
			for i in range(scope_count)
		)
		_ensure_consumed(buff, 'server license request')

		if key_exchange_list.blob_type != LicenseBlobType.KEY_EXCHANGE_ALGORITHM:
			raise LicensingProtocolError('Invalid key exchange list blob type')
		if len(key_exchange_list.data) == 0 or len(key_exchange_list.data) % 4 != 0:
			raise LicensingProtocolError('Invalid key exchange algorithm list')
		algorithms = [
			int.from_bytes(key_exchange_list.data[i:i + 4], byteorder='little', signed=False)
			for i in range(0, len(key_exchange_list.data), 4)
		]
		if KEY_EXCHANGE_ALG_RSA not in algorithms:
			raise LicensingProtocolError('Server does not offer RSA licensing key exchange')
		if (
			server_certificate.data
			and server_certificate.blob_type != LicenseBlobType.CERTIFICATE
		):
			raise LicensingProtocolError('Invalid server certificate blob type')
		if any(
			scope.data and scope.blob_type != LicenseBlobType.SCOPE
			for scope in scopes
		):
			raise LicensingProtocolError('Invalid licensing scope blob type')

		return cls(
			server_random,
			product_version,
			company_name,
			product_id,
			key_exchange_list,
			server_certificate,
			scopes,
		)


@dataclass(frozen=True)
class LicenseInformation:
	version: int
	scope: bytes
	company_name: bytes
	product_id: bytes
	license_info: bytes

	@classmethod
	def from_bytes(cls, data: bytes):
		buff = io.BytesIO(data)
		info = cls(
			_read_uint32(buff, 'issued license version'),
			_read_counted_bytes(buff, 'issued license scope'),
			_read_counted_bytes(buff, 'issued license company name'),
			_read_counted_bytes(buff, 'issued license product ID'),
			_read_counted_bytes(buff, 'issued license data'),
		)
		_ensure_consumed(buff, 'issued license information')
		return info


class LicenseCrypto:
	def __init__(
		self,
		server_random: bytes,
		hostname: str,
		random_source: Callable[[int], bytes] = os.urandom,
	):
		if len(server_random) != 32:
			raise LicensingProtocolError('Server licensing random must be 32 bytes')

		self.server_random = server_random
		self.client_random = self._get_random(random_source, 32, 'client random')
		self.premaster_secret = self._get_random(random_source, 48, 'premaster secret')

		master_secret = b''.join(
			self._salted_hash(
				self.premaster_secret,
				label,
				self.client_random,
				self.server_random,
			)
			for label in (b'A', b'BB', b'CCC')
		)
		session_key_blob = b''.join(
			self._salted_hash(
				master_secret,
				label,
				self.server_random,
				self.client_random,
			)
			for label in (b'A', b'BB', b'CCC')
		)
		self.mac_salt_key = session_key_blob[:16]
		self.license_key = md5(
			session_key_blob[16:32] + self.client_random + self.server_random
		).digest()
		self.hardware_id = struct.pack('<I', PLATFORM_ID) + md5(
			hostname.encode('utf-8', errors='replace')
		).digest()

	@staticmethod
	def _get_random(random_source, length: int, field_name: str) -> bytes:
		data = random_source(length)
		if len(data) != length:
			raise LicensingProtocolError('%s generator returned the wrong length' % field_name)
		return data

	@staticmethod
	def _salted_hash(secret: bytes, label: bytes, random1: bytes, random2: bytes) -> bytes:
		return md5(secret + sha1(label + secret + random1 + random2).digest()).digest()

	def crypt(self, data: bytes) -> bytes:
		# MS-RDPELE starts a fresh RC4 stream for each encrypted licensing field.
		return ARC4(self.license_key).encrypt(data)

	def mac(self, data: bytes) -> bytes:
		data_length = struct.pack('<I', len(data))
		sha_component = sha1(
			self.mac_salt_key + (b'\x36' * 40) + data_length + data
		).digest()
		return md5(self.mac_salt_key + (b'\x5c' * 48) + sha_component).digest()


class RDPLicenseManager:
	def __init__(
		self,
		username: str = '',
		hostname: str = None,
		server_certificate: SERVER_CERTIFICATE = None,
		random_source: Callable[[int], bytes] = os.urandom,
	):
		self.username = username or 'aardwolf'
		self.hostname = hostname or socket.gethostname()
		self.server_certificate = server_certificate
		self.random_source = random_source
		self.state = LicenseState.INITIAL
		self.crypto = None
		self.issued_license = None
		self.last_response = None

	def process(self, pdu: LicensePDU):
		if self.state == LicenseState.COMPLETED:
			raise LicensingProtocolError('Received licensing data after licensing completed')

		if pdu.message_type == LicenseMessageType.ERROR_ALERT:
			return self._process_error(pdu.body)
		if pdu.message_type == LicenseMessageType.LICENSE_REQUEST:
			self.last_response = self._process_license_request(pdu.body)
			return False, self.last_response
		if pdu.message_type == LicenseMessageType.PLATFORM_CHALLENGE:
			self.last_response = self._process_platform_challenge(pdu.body)
			return False, self.last_response
		if pdu.message_type in (LicenseMessageType.NEW_LICENSE, LicenseMessageType.UPGRADE_LICENSE):
			self._process_new_license(pdu.body)
			self.state = LicenseState.COMPLETED
			return True, None

		raise LicensingProtocolError(
			'Unexpected server licensing message %s' % pdu.message_type.name
		)

	def _process_error(self, data: bytes):
		message = LicenseErrorMessage.from_bytes(data)
		if (
			message.error_code == LicenseErrorCode.STATUS_VALID_CLIENT
			and message.state_transition == LicenseStateTransition.ST_NO_TRANSITION
		):
			if len(message.error_info.data) != 0:
				raise LicensingProtocolError('Invalid STATUS_VALID_CLIENT error information')
			self.state = LicenseState.COMPLETED
			return True, None

		if message.state_transition == LicenseStateTransition.ST_RESEND_LAST_MESSAGE:
			if self.last_response is None:
				raise LicensingProtocolError(
					'Server requested a licensing resend before the client sent a message'
				)
			return False, self.last_response

		if message.state_transition == LicenseStateTransition.ST_RESET_PHASE_TO_START:
			self.state = LicenseState.INITIAL
			self.crypto = None
			self.issued_license = None
			self.last_response = None
			return False, None

		error_name = LicenseErrorCode._value2member_map_.get(message.error_code)
		transition_name = LicenseStateTransition._value2member_map_.get(message.state_transition)
		raise LicensingProtocolError(
			'RDP licensing failed: %s (0x%08x), transition %s (0x%08x)'
			% (
				error_name.name if error_name else 'UNKNOWN_ERROR',
				message.error_code,
				transition_name.name if transition_name else 'UNKNOWN_TRANSITION',
				message.state_transition,
			)
		)

	def _process_license_request(self, data: bytes) -> bytes:
		if self.state != LicenseState.INITIAL:
			raise LicensingProtocolError('Unexpected duplicate server license request')

		request = ServerLicenseRequest.from_bytes(data)
		if request.server_certificate.data:
			try:
				server_certificate = SERVER_CERTIFICATE.from_bytes(
					request.server_certificate.data
				)
			except Exception as e:
				raise LicensingProtocolError('Invalid licensing server certificate') from e
		else:
			server_certificate = self.server_certificate
		if server_certificate is None:
			raise LicensingProtocolError('Server did not provide a licensing certificate')

		self.crypto = LicenseCrypto(
			request.server_random,
			self.hostname,
			random_source=self.random_source,
		)
		try:
			encrypted_premaster = server_certificate.encrypt(self.crypto.premaster_secret)
		except Exception as e:
			raise LicensingProtocolError('Could not encrypt licensing premaster secret') from e

		username = self._encode_client_name(self.username, 'client username')
		hostname = self._encode_client_name(self.hostname, 'client machine name')
		body = struct.pack('<II', KEY_EXCHANGE_ALG_RSA, PLATFORM_ID)
		body += self.crypto.client_random
		body += LicenseBinaryBlob(LicenseBlobType.RANDOM, encrypted_premaster).to_bytes()
		body += LicenseBinaryBlob(LicenseBlobType.CLIENT_USER_NAME, username).to_bytes()
		body += LicenseBinaryBlob(LicenseBlobType.CLIENT_MACHINE_NAME, hostname).to_bytes()
		self.state = LicenseState.NEW_REQUEST_SENT
		return LicensePDU(
			LicenseMessageType.NEW_LICENSE_REQUEST,
			0,
			PREAMBLE_VERSION_3_0,
			body,
		).to_bytes()

	@staticmethod
	def _encode_client_name(value: str, field_name: str) -> bytes:
		data = value.encode('utf-8', errors='replace') + b'\x00'
		if len(data) > MAX_LICENSE_FIELD_SIZE:
			raise LicensingProtocolError('%s is too long' % field_name)
		return data

	def _process_platform_challenge(self, data: bytes) -> bytes:
		if self.state != LicenseState.NEW_REQUEST_SENT or self.crypto is None:
			raise LicensingProtocolError('Unexpected server platform challenge')

		buff = io.BytesIO(data)
		_read_uint32(buff, 'platform challenge connect flags')
		encrypted_challenge = LicenseBinaryBlob.from_buffer(buff, 'encrypted platform challenge')
		challenge_mac = _read_exact(buff, 16, 'platform challenge MAC')
		_ensure_consumed(buff, 'server platform challenge')
		if encrypted_challenge.blob_type not in (
			LicenseBlobType.ANY,
			LicenseBlobType.ENCRYPTED_DATA,
		):
			raise LicensingProtocolError('Invalid platform challenge blob type')

		challenge = self.crypto.crypt(encrypted_challenge.data)
		if not hmac.compare_digest(self.crypto.mac(challenge), challenge_mac):
			raise LicensingProtocolError('Server platform challenge MAC mismatch')
		if len(challenge) > MAX_LICENSE_FIELD_SIZE:
			raise LicensingProtocolError('Server platform challenge is too large')

		response_data = struct.pack(
			'<HHHH',
			PLATFORM_CHALLENGE_RESPONSE_VERSION,
			OTHER_PLATFORM_CHALLENGE_TYPE,
			LICENSE_DETAIL_DETAIL,
			len(challenge),
		) + challenge
		response_mac = self.crypto.mac(response_data + self.crypto.hardware_id)
		encrypted_response = self.crypto.crypt(response_data)
		encrypted_hwid = self.crypto.crypt(self.crypto.hardware_id)
		body = LicenseBinaryBlob(
			LicenseBlobType.ENCRYPTED_DATA,
			encrypted_response,
		).to_bytes()
		body += LicenseBinaryBlob(
			LicenseBlobType.ENCRYPTED_DATA,
			encrypted_hwid,
		).to_bytes()
		body += response_mac
		self.state = LicenseState.CHALLENGE_RESPONSE_SENT
		return LicensePDU(
			LicenseMessageType.PLATFORM_CHALLENGE_RESPONSE,
			0,
			PREAMBLE_VERSION_3_0,
			body,
		).to_bytes()

	def _process_new_license(self, data: bytes) -> None:
		if self.state != LicenseState.CHALLENGE_RESPONSE_SENT or self.crypto is None:
			raise LicensingProtocolError('Unexpected new or upgraded license')

		buff = io.BytesIO(data)
		encrypted_license = LicenseBinaryBlob.from_buffer(buff, 'encrypted license')
		license_mac = _read_exact(buff, 16, 'new license MAC')
		_ensure_consumed(buff, 'new or upgraded license')
		if encrypted_license.blob_type not in (
			LicenseBlobType.ANY,
			LicenseBlobType.ENCRYPTED_DATA,
		):
			raise LicensingProtocolError('Invalid encrypted license blob type')

		license_data = self.crypto.crypt(encrypted_license.data)
		if not hmac.compare_digest(self.crypto.mac(license_data), license_mac):
			raise LicensingProtocolError('New or upgraded license MAC mismatch')
		self.issued_license = LicenseInformation.from_bytes(license_data)
