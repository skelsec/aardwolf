import unittest

from aardwolf.protocol.T128.savesessioninfopdu import (
	INFO_TYPE,
	LOGON_EX,
	LOGON_MSG_TYPE,
	TS_SAVE_SESSION_INFO_PDU,
)
from aardwolf.protocol.T128.share import (
	CompType,
	PDUTYPE,
	PDUTYPE2,
	STREAM_TYPE,
	TS_SHARECONTROLHEADER,
	TS_SHAREDATAHEADER,
)


def build_logon_error_pdu(notification_type, notification_data):
	error_data = notification_type.to_bytes(4, byteorder='little', signed=False)
	error_data += notification_data.to_bytes(4, byteorder='little', signed=False)
	field = len(error_data).to_bytes(4, byteorder='little', signed=False) + error_data
	extended = (6 + len(field)).to_bytes(2, byteorder='little', signed=False)
	extended += LOGON_EX.LOGONERRORS.value.to_bytes(
		4, byteorder='little', signed=False
	)
	extended += field
	payload = INFO_TYPE.LOGON_EXTENDED_INFO.value.to_bytes(
		4, byteorder='little', signed=False
	) + extended

	control_header = TS_SHARECONTROLHEADER()
	control_header.totalLength = 18 + len(payload)
	control_header.pduType = PDUTYPE.DATAPDU
	control_header.pduSource = 1001

	data_header = TS_SHAREDATAHEADER()
	data_header.shareControlHeader = control_header
	data_header.shareID = 0x103EA
	data_header.streamID = STREAM_TYPE.MED
	data_header.uncompressedLength = len(payload)
	data_header.pduType2 = PDUTYPE2.SAVE_SESSION_INFO
	data_header.compressedType = CompType(0)
	data_header.compressedLength = 0
	return data_header.to_bytes() + payload


class SaveSessionInfoTests(unittest.TestCase):
	def test_parses_session_contention_notification(self):
		data = build_logon_error_pdu(LOGON_MSG_TYPE.BUMP_OPTIONS.value, 3)

		pdu = TS_SAVE_SESSION_INFO_PDU.from_bytes(data)

		self.assertEqual(pdu.info_type, INFO_TYPE.LOGON_EXTENDED_INFO)
		self.assertEqual(
			pdu.logon_errors.notification_type, LOGON_MSG_TYPE.BUMP_OPTIONS
		)
		self.assertEqual(pdu.logon_errors.notification_data, 3)
		self.assertTrue(pdu.logon_errors.is_session_contention)
		self.assertTrue(pdu.is_session_contention)

	def test_preserves_unknown_notification_type(self):
		data = build_logon_error_pdu(0x12345678, 7)

		pdu = TS_SAVE_SESSION_INFO_PDU.from_bytes(data)

		self.assertEqual(pdu.logon_errors.notification_type, 0x12345678)
		self.assertFalse(pdu.logon_errors.is_session_contention)

	def test_session_continue_is_not_contention(self):
		data = build_logon_error_pdu(LOGON_MSG_TYPE.SESSION_CONTINUE.value, 4)

		pdu = TS_SAVE_SESSION_INFO_PDU.from_bytes(data)

		self.assertEqual(
			pdu.logon_errors.notification_type, LOGON_MSG_TYPE.SESSION_CONTINUE
		)
		self.assertFalse(pdu.is_session_contention)

	def test_rejects_non_save_session_info_pdu(self):
		data = bytearray(build_logon_error_pdu(LOGON_MSG_TYPE.BUMP_OPTIONS.value, 3))
		data[14] = PDUTYPE2.SET_ERROR_INFO_PDU.value

		with self.assertRaises(ValueError):
			TS_SAVE_SESSION_INFO_PDU.from_bytes(bytes(data))


if __name__ == '__main__':
	unittest.main()
