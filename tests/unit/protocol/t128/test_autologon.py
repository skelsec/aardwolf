"""INFO_AUTOLOGON in the Client Info PDU and waiting for the logon outcome."""

import asyncio
import struct
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.target import RDPTarget
from aardwolf.connection import AutologonError, RDPConnection
from aardwolf.protocol.T125.infopacket import INFO_FLAG
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
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS


pytestmark = pytest.mark.unit

MCS_CHANNEL = 1003


def make_save_session_info(info_type, payload):
    payload = struct.pack("<I", int(info_type)) + payload
    header = TS_SHAREDATAHEADER()
    header.shareControlHeader = TS_SHARECONTROLHEADER()
    header.shareControlHeader.totalLength = 18 + len(payload)
    header.shareControlHeader.pduType = PDUTYPE.DATAPDU
    header.shareControlHeader.pduVersion = 1
    header.shareControlHeader.pduSource = MCS_CHANNEL
    header.shareID = 0x000103EA
    header.streamID = STREAM_TYPE.MED
    header.uncompressedLength = len(payload) + 4
    header.pduType2 = PDUTYPE2.SAVE_SESSION_INFO
    header.compressedType = CompType(0)
    header.compressedLength = 0
    return header.to_bytes() + payload


def logon_errors_pdu(notification_type, notification_data=0):
    logon_error = struct.pack("<II", int(notification_type), notification_data)
    extended = struct.pack("<HI", 18, int(LOGON_EX.LOGONERRORS))
    extended += struct.pack("<I", len(logon_error)) + logon_error
    return make_save_session_info(INFO_TYPE.LOGON_EXTENDED_INFO, extended)


def logon_info_pdu():
    # TS_LOGON_INFO_VERSION_2 is not parsed further, any body will do
    return make_save_session_info(INFO_TYPE.LOGON_LONG, b"\x00" * 576)


def make_connection(timeout=0.2):
    connection = object.__new__(RDPConnection)
    connection._RDPConnection__joined_channels = {
        "MCS": SimpleNamespace(channel_id=MCS_CHANNEL)
    }
    connection.logon_info_received = asyncio.Event()
    connection.logon_info_queue = asyncio.Queue()
    connection.logon_notifications = []
    connection.logon_error = None
    connection.disconnected_evt = asyncio.Event()
    connection._RDPConnection__logon_evt = asyncio.Event()
    connection.autologon_timeout = timeout
    return connection


async def deliver(connection, wire):
    assert await connection._RDPConnection__process_save_session_info(MCS_CHANNEL, wire) is True


async def wait_for_autologon(connection):
    await asyncio.wait_for(connection._RDPConnection__wait_for_autologon(), timeout=2)


@pytest.mark.asyncio
async def test_logon_info_means_signed_in():
    connection = make_connection()
    await deliver(connection, logon_info_pdu())
    await wait_for_autologon(connection)


@pytest.mark.asyncio
async def test_notification_arriving_while_waiting_is_picked_up():
    connection = make_connection(timeout=1)

    async def later():
        await asyncio.sleep(0.05)
        await deliver(connection, logon_info_pdu())

    task = asyncio.create_task(later())
    await wait_for_autologon(connection)
    await task


@pytest.mark.asyncio
async def test_session_contention_means_credentials_were_accepted():
    connection = make_connection()
    await deliver(connection, logon_errors_pdu(LOGON_MSG_TYPE.BUMP_OPTIONS, 4))
    await wait_for_autologon(connection)
    assert connection.logon_info_queue.get_nowait().is_session_contention


@pytest.mark.asyncio
async def test_session_continue_keeps_waiting():
    connection = make_connection(timeout=1)
    await deliver(connection, logon_errors_pdu(LOGON_MSG_TYPE.SESSION_CONTINUE))

    async def later():
        await asyncio.sleep(0.05)
        await deliver(connection, logon_info_pdu())

    task = asyncio.create_task(later())
    await wait_for_autologon(connection)
    await task


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "notification_type",
    [LOGON_MSG_TYPE.NO_PERMISSION, LOGON_MSG_TYPE.ACCESS_DENIED, LOGON_MSG_TYPE.DISCONNECT_REFUSED],
)
async def test_logon_error_notification_fails(notification_type):
    connection = make_connection()
    await deliver(connection, logon_errors_pdu(notification_type, 2))
    with pytest.raises(AutologonError, match=notification_type.name) as excinfo:
        await wait_for_autologon(connection)
    assert excinfo.value.notification.logon_errors.notification_type == notification_type


@pytest.mark.asyncio
async def test_no_notification_times_out():
    # what Windows does on a wrong password: sign-in screen with an error, nothing sent
    connection = make_connection(timeout=0.1)
    with pytest.raises(AutologonError, match="no logon confirmation"):
        await wait_for_autologon(connection)


@pytest.mark.asyncio
async def test_set_error_info_fails():
    connection = make_connection(timeout=1)
    connection.logon_error = SimpleNamespace(name="LOGOFF_BY_USER")
    with pytest.raises(AutologonError, match="LOGOFF_BY_USER"):
        await wait_for_autologon(connection)


@pytest.mark.asyncio
async def test_disconnect_while_waiting_fails():
    connection = make_connection(timeout=1)
    asyncio.get_running_loop().call_later(0.05, connection.disconnected_evt.set)
    with pytest.raises(AutologonError, match="connection closed"):
        await wait_for_autologon(connection)


def make_userdata_connection(autologon=True, secret="hodor", authapi=None, protocol=SUPP_PROTOCOLS.SSL):
    connection = object.__new__(RDPConnection)
    connection.iosettings = RDPIOSettings()
    connection.bulk_decompressor = None
    connection.cryptolayer = None
    connection.authapi = authapi
    connection.x224_protocol = protocol
    connection.credentials = SimpleNamespace(domain="NORTH", username="hodor", secret=secret)
    connection.target = RDPTarget(ip="192.0.2.1", autologon=autologon)
    connection._RDPConnection__joined_channels = {"MCS": SimpleNamespace(channel_id=MCS_CHANNEL)}
    connection._RDPConnection__autologon_sent = False
    connection.handle_out_data = AsyncMock()
    return connection


async def sent_info_flags(connection):
    _, err = await connection._RDPConnection__send_userdata()
    assert err is None
    return connection.handle_out_data.await_args.args[0].flags


@pytest.mark.asyncio
async def test_password_in_client_info_requests_autologon():
    connection = make_userdata_connection()
    assert INFO_FLAG.AUTOLOGON in await sent_info_flags(connection)
    assert connection._RDPConnection__autologon_sent is True


@pytest.mark.asyncio
async def test_autologon_can_be_disabled_on_the_target():
    connection = make_userdata_connection(autologon=False)
    assert INFO_FLAG.AUTOLOGON not in await sent_info_flags(connection)
    assert connection._RDPConnection__autologon_sent is False


@pytest.mark.asyncio
async def test_no_autologon_without_password():
    connection = make_userdata_connection(secret=None)
    assert INFO_FLAG.AUTOLOGON not in await sent_info_flags(connection)


@pytest.mark.asyncio
async def test_no_autologon_after_nla():
    # the server signs in with the CredSSP credentials, the Client Info PDU carries no password
    connection = make_userdata_connection(authapi=object(), protocol=SUPP_PROTOCOLS.HYBRID_EX)
    assert INFO_FLAG.AUTOLOGON not in await sent_info_flags(connection)
    assert connection._RDPConnection__autologon_sent is False


def test_target_autologon_defaults_on_and_url_can_disable_it():
    target = RDPTarget.from_url("rdp+plain://NORTH%5Chodor:hodor@192.0.2.1")
    assert (target.autologon, target.autologon_confirm) == (True, True)
    target = RDPTarget.from_url("rdp+plain://NORTH%5Chodor:hodor@192.0.2.1/?autologon=0")
    assert (target.autologon, target.autologon_confirm) == (False, True)
    target = RDPTarget.from_url("rdp+plain://NORTH%5Chodor:hodor@192.0.2.1/?autologon_confirm=0")
    assert (target.autologon, target.autologon_confirm) == (True, False)
