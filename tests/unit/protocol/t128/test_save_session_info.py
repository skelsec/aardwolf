"""Save Session Info parsing and connection dispatch."""

import asyncio
import struct
from types import SimpleNamespace

import pytest

from aardwolf.connection import RDPConnection
from aardwolf.protocol.T128.savesessioninfopdu import (
    INFO_TYPE,
    LOGON_EX,
    LOGON_MSG_TYPE,
)
from aardwolf.protocol.T128.share import (
    CompType,
    PDUTYPE,
    PDUTYPE2,
    STREAM_TYPE,
    TS_SHARECONTROLHEADER,
    TS_SHAREDATAHEADER,
)


pytestmark = pytest.mark.unit


def make_save_session_info(notification_type, notification_data):
    logon_error = struct.pack("<II", int(notification_type), notification_data)
    extended = struct.pack("<HI", 18, int(LOGON_EX.LOGONERRORS))
    extended += struct.pack("<I", len(logon_error)) + logon_error
    payload = struct.pack("<I", int(INFO_TYPE.LOGON_EXTENDED_INFO)) + extended

    header = TS_SHAREDATAHEADER()
    header.shareControlHeader = TS_SHARECONTROLHEADER()
    header.shareControlHeader.totalLength = 18 + len(payload)
    header.shareControlHeader.pduType = PDUTYPE.DATAPDU
    header.shareControlHeader.pduVersion = 1
    header.shareControlHeader.pduSource = 1003
    header.shareID = 0x000103EA
    header.streamID = STREAM_TYPE.MED
    header.uncompressedLength = len(payload) + 4
    header.pduType2 = PDUTYPE2.SAVE_SESSION_INFO
    header.compressedType = CompType(0)
    header.compressedLength = 0
    return header.to_bytes() + payload


@pytest.mark.asyncio
async def test_connection_dispatches_save_session_info_with_security_header():
    connection = object.__new__(RDPConnection)
    connection._RDPConnection__joined_channels = {
        "MCS": SimpleNamespace(channel_id=1003)
    }
    connection.logon_info_received = asyncio.Event()
    connection.logon_info_queue = asyncio.Queue()
    wire = make_save_session_info(
        LOGON_MSG_TYPE.SESSION_BUSY_OPTIONS,
        2,
    )

    processed = await connection._RDPConnection__process_save_session_info(
        1003,
        b"\x00\x00\x00\x00" + wire,
        share_pdu_offset=4,
    )

    assert processed is True
    assert connection.logon_info_received.is_set()
    notification = connection.logon_info_queue.get_nowait()
    assert notification.info_type == INFO_TYPE.LOGON_EXTENDED_INFO
    assert notification.logon_errors.notification_type == LOGON_MSG_TYPE.SESSION_BUSY_OPTIONS
    assert notification.logon_errors.notification_data == 2
    assert notification.is_session_contention is True


@pytest.mark.asyncio
async def test_connection_ignores_save_session_info_on_virtual_channel():
    connection = object.__new__(RDPConnection)
    connection._RDPConnection__joined_channels = {
        "MCS": SimpleNamespace(channel_id=1003)
    }
    connection.logon_info_received = asyncio.Event()
    connection.logon_info_queue = asyncio.Queue()

    processed = await connection._RDPConnection__process_save_session_info(
        1004,
        make_save_session_info(LOGON_MSG_TYPE.ACCESS_DENIED, 0),
    )

    assert processed is False
    assert connection.logon_info_received.is_set() is False
    assert connection.logon_info_queue.empty()
