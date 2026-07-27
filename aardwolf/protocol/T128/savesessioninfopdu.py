import enum
import io
from typing import ClassVar

from aardwolf.protocol.T128.share import PDUTYPE, PDUTYPE2, TS_SHAREDATAHEADER


class INFO_TYPE(enum.IntEnum):
	LOGON = 0x00000000
	LOGON_LONG = 0x00000001
	LOGON_PLAIN_NOTIFY = 0x00000002
	LOGON_EXTENDED_INFO = 0x00000003


class LOGON_EX(enum.IntFlag):
	AUTORECONNECTCOOKIE = 0x00000001
	LOGONERRORS = 0x00000002


class LOGON_MSG_TYPE(enum.IntEnum):
	SESSION_BUSY_OPTIONS = 0xFFFFFFF8
	DISCONNECT_REFUSED = 0xFFFFFFF9
	NO_PERMISSION = 0xFFFFFFFA
	BUMP_OPTIONS = 0xFFFFFFFB
	RECONNECT_OPTIONS = 0xFFFFFFFC
	SESSION_TERMINATE = 0xFFFFFFFD
	SESSION_CONTINUE = 0xFFFFFFFE
	ACCESS_DENIED = 0xFFFFFFFF


class TS_LOGON_ERRORS_INFO:
	SESSION_CONTENTION_TYPES: ClassVar = {
		LOGON_MSG_TYPE.SESSION_BUSY_OPTIONS,
		LOGON_MSG_TYPE.BUMP_OPTIONS,
		LOGON_MSG_TYPE.RECONNECT_OPTIONS,
	}

	def __init__(self):
		self.notification_type_raw: int = None
		self.notification_type: LOGON_MSG_TYPE | int = None
		self.notification_data: int = None

	@property
	def is_session_contention(self):
		return self.notification_type in self.SESSION_CONTENTION_TYPES

	@staticmethod
	def from_bytes(data: bytes):
		return TS_LOGON_ERRORS_INFO.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		data = buff.read(8)
		if len(data) != 8:
			raise ValueError('Logon Errors Info requires 8 bytes')

		msg = TS_LOGON_ERRORS_INFO()
		msg.notification_type_raw = int.from_bytes(
			data[:4], byteorder='little', signed=False
		)
		try:
			msg.notification_type = LOGON_MSG_TYPE(msg.notification_type_raw)
		except ValueError:
			msg.notification_type = msg.notification_type_raw
		msg.notification_data = int.from_bytes(
			data[4:], byteorder='little', signed=False
		)
		return msg


class TS_LOGON_INFO_EXTENDED:
	def __init__(self):
		self.length: int = None
		self.fields_present: LOGON_EX = None
		self.auto_reconnect_cookie: bytes = None
		self.logon_errors: TS_LOGON_ERRORS_INFO = None

	@staticmethod
	def from_bytes(data: bytes):
		return TS_LOGON_INFO_EXTENDED.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		header = buff.read(6)
		if len(header) != 6:
			raise ValueError('Logon Info Extended requires a 6-byte header')

		msg = TS_LOGON_INFO_EXTENDED()
		msg.length = int.from_bytes(header[:2], byteorder='little', signed=False)
		if msg.length < 6:
			raise ValueError('Logon Info Extended length is smaller than its header')
		msg.fields_present = LOGON_EX(
			int.from_bytes(header[2:], byteorder='little', signed=False)
		)

		fields_length = msg.length - 6
		fields_data = buff.read(fields_length)
		if len(fields_data) != fields_length:
			raise ValueError('Logon Info Extended fields are truncated')
		fields = io.BytesIO(fields_data)

		if LOGON_EX.AUTORECONNECTCOOKIE in msg.fields_present:
			msg.auto_reconnect_cookie = TS_LOGON_INFO_EXTENDED._read_field(fields)

		if LOGON_EX.LOGONERRORS in msg.fields_present:
			error_data = TS_LOGON_INFO_EXTENDED._read_field(fields)
			msg.logon_errors = TS_LOGON_ERRORS_INFO.from_bytes(error_data)

		return msg

	@staticmethod
	def _read_field(buff: io.BytesIO):
		length_data = buff.read(4)
		if len(length_data) != 4:
			raise ValueError('Logon Info Field length is truncated')
		field_length = int.from_bytes(length_data, byteorder='little', signed=False)
		field_data = buff.read(field_length)
		if len(field_data) != field_length:
			raise ValueError('Logon Info Field data is truncated')
		return field_data


class TS_SAVE_SESSION_INFO_PDU:
	def __init__(self):
		self.share_data_header: TS_SHAREDATAHEADER = None
		self.info_type_raw: int = None
		self.info_type: INFO_TYPE | int = None
		self.logon_info_extended: TS_LOGON_INFO_EXTENDED = None
		self.raw_info: bytes = None

	@property
	def logon_errors(self):
		if self.logon_info_extended is None:
			return None
		return self.logon_info_extended.logon_errors

	@property
	def is_session_contention(self):
		return self.logon_errors is not None and self.logon_errors.is_session_contention

	@staticmethod
	def from_bytes(data: bytes):
		if len(data) < 22:
			raise ValueError('Save Session Info PDU is shorter than its headers')
		return TS_SAVE_SESSION_INFO_PDU.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO):
		msg = TS_SAVE_SESSION_INFO_PDU()
		msg.share_data_header = TS_SHAREDATAHEADER.from_buffer(buff)
		if msg.share_data_header.shareControlHeader.pduType != PDUTYPE.DATAPDU:
			raise ValueError('Save Session Info PDU is not a Data PDU')
		if msg.share_data_header.pduType2 != PDUTYPE2.SAVE_SESSION_INFO:
			raise ValueError('PDU is not Save Session Info')
		total_length = msg.share_data_header.shareControlHeader.totalLength
		available_length = len(buff.getbuffer())
		if total_length < 22 or total_length > available_length:
			raise ValueError('Save Session Info PDU has an invalid totalLength')

		info_type_data = buff.read(4)
		if len(info_type_data) != 4:
			raise ValueError('Save Session Info PDU is missing infoType')
		msg.info_type_raw = int.from_bytes(
			info_type_data, byteorder='little', signed=False
		)
		msg.info_type = INFO_TYPE(msg.info_type_raw)

		if msg.info_type == INFO_TYPE.LOGON_EXTENDED_INFO:
			msg.logon_info_extended = TS_LOGON_INFO_EXTENDED.from_buffer(buff)
		else:
			msg.raw_info = buff.read()
		return msg
