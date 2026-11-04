"""Scripted in-process peer tests for RDP input and VNC handshake."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.connection import RDPConnection, _get_asn1_codecs
from aardwolf.network.x224 import X224Network
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE
from aardwolf.protocol.T128.controlpdu import TS_CONTROL_PDU
from aardwolf.protocol.T128.inputeventpdu import TS_INPUT_PDU_DATA
from aardwolf.protocol.T128.share import (
    PDUTYPE,
    PDUTYPE2,
    STREAM_TYPE,
    CompType,
    TS_SHARECONTROLHEADER,
    TS_SHAREDATAHEADER,
)
from aardwolf.protocol.T128.synchronizepdu import TS_SYNCHRONIZE_PDU
from aardwolf.protocol.pdu.input.keyboard import KBDFLAGS
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest, RDP_NEG_REQ
from aardwolf.protocol.x224.constants import NEG_FLAGS, SUPP_PROTOCOLS, TPDU_TYPE
from aardwolf.protocol.x224.server.connectionconfirm import ConnectionConfirm, RDP_NEG_RSP
from aardwolf.vncconnection import VNCConnection
from tests.support.scripted_rdp import DEFAULT_TIMEOUT, ScriptedUniConnection


pytestmark = [pytest.mark.fake_peer, pytest.mark.asyncio]


async def test_scripted_connection_replays_bytes_per_write():
    transport = ScriptedUniConnection([b"reply-one", b"reply-two"])
    await asyncio.wait_for(transport.write(b"first"), timeout=DEFAULT_TIMEOUT)
    await asyncio.wait_for(transport.write(b"second"), timeout=DEFAULT_TIMEOUT)
    reader = transport.read()
    first = await asyncio.wait_for(reader.__anext__(), timeout=DEFAULT_TIMEOUT)
    second = await asyncio.wait_for(reader.__anext__(), timeout=DEFAULT_TIMEOUT)
    assert first == b"reply-one"
    assert second == b"reply-two"
    assert transport.writes == [b"first", b"second"]
    await asyncio.wait_for(transport.close(), timeout=DEFAULT_TIMEOUT)


async def test_scripted_connection_callback_and_feed():
    def echo(data, conn):
        return b"echo:" + data

    transport = ScriptedUniConnection([echo])
    await asyncio.wait_for(transport.write(b"ping"), timeout=DEFAULT_TIMEOUT)
    reader = transport.read()
    reply = await asyncio.wait_for(reader.__anext__(), timeout=DEFAULT_TIMEOUT)
    assert reply == b"echo:ping"
    await asyncio.wait_for(transport.feed(b"unsolicited"), timeout=DEFAULT_TIMEOUT)
    extra = await asyncio.wait_for(reader.__anext__(), timeout=DEFAULT_TIMEOUT)
    assert extra == b"unsolicited"
    await asyncio.wait_for(transport.close(), timeout=DEFAULT_TIMEOUT)


async def test_x224_confirm_is_built_from_production_codecs():
    request = ConnectionRequest()
    request.SRC_REF = 0x1234
    request.rdpNegReq = RDP_NEG_REQ()
    request.rdpNegReq.flags = NEG_FLAGS(0)
    request.rdpNegReq.requestedProtocols = SUPP_PROTOCOLS.SSL

    confirm = ConnectionConfirm()
    confirm.SRC_REF = 0x0001
    confirm.DST_REF = request.SRC_REF
    confirm.rdpNegData = RDP_NEG_RSP()
    confirm.rdpNegData.flags = 0
    confirm.rdpNegData.selectedProtocol = SUPP_PROTOCOLS.SSL

    def reply(_data, _conn):
        return confirm.to_bytes()

    transport = ScriptedUniConnection([reply])
    await asyncio.wait_for(transport.write(request.to_bytes()), timeout=DEFAULT_TIMEOUT)
    parsed = ConnectionConfirm.from_bytes(transport.writes[0] and confirm.to_bytes())
    reader = transport.read()
    wire = await asyncio.wait_for(reader.__anext__(), timeout=DEFAULT_TIMEOUT)
    parsed = ConnectionConfirm.from_bytes(wire)
    assert parsed.CR == TPDU_TYPE.CONNECTION_CONFIRM
    assert parsed.rdpNegData.selectedProtocol == SUPP_PROTOCOLS.SSL
    await asyncio.wait_for(transport.close(), timeout=DEFAULT_TIMEOUT)


def make_bare_rdp_connection():
    connection = object.__new__(RDPConnection)
    connection.cryptolayer = None
    connection._RDPConnection__joined_channels = {
        "MCS": SimpleNamespace(channel_id=1003, disconnect=AsyncMock())
    }
    connection._RDPConnection__channel_task = {}
    connection._RDPConnection__external_reader_task = None
    connection._RDPConnection__x224_reader_task = None
    connection._RDPConnection__terminate_called = False
    connection.disconnected_evt = asyncio.Event()
    connection.ext_out_queue = asyncio.Queue()
    return connection


async def test_send_key_scancode_release_emits_input_pdu():
    connection = make_bare_rdp_connection()
    captured = []

    async def capture(data, *args, **kwargs):
        captured.append(data)

    connection.handle_out_data = capture
    await asyncio.wait_for(
        connection.send_key_scancode(0x1E, False, False),
        timeout=DEFAULT_TIMEOUT,
    )
    assert len(captured) == 1
    assert isinstance(captured[0], TS_INPUT_PDU_DATA)
    event = captured[0].slowPathInputEvents[0]
    assert event.input.keyCode == 0x1E
    assert KBDFLAGS.RELEASE in event.input.keyboardFlags


async def test_send_mouse_records_coordinates():
    connection = make_bare_rdp_connection()
    captured = []

    async def capture(data, *args, **kwargs):
        captured.append(data)

    connection.handle_out_data = capture
    from aardwolf.commons.queuedata.constants import MOUSEBUTTON

    await asyncio.wait_for(
        connection.send_mouse(MOUSEBUTTON.MOUSEBUTTON_LEFT, 40, 80, True),
        timeout=DEFAULT_TIMEOUT,
    )
    assert captured
    event = captured[0].slowPathInputEvents[0]
    assert event.input.xPos == 40
    assert event.input.yPos == 80


async def test_cleanup_failed_connect_closes_transport():
    connection = make_bare_rdp_connection()
    transport = ScriptedUniConnection()
    connection._RDPConnection__connection = transport
    await asyncio.wait_for(
        connection._RDPConnection__cleanup_failed_connect(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert transport.closed is True


async def test_fastpath_reassembler_on_connection_settings():
    from aardwolf.protocol.fastpath import FASTPATH_FRAGMENT, FASTPATH_UPDATETYPE, TS_FP_UPDATE
    from aardwolf.protocol.fastpath.reassembly import FastPathFragmentReassembler

    connection = make_bare_rdp_connection()
    connection.iosettings = RDPIOSettings()
    reassembler = FastPathFragmentReassembler(connection.iosettings.fastpath_max_request_size)

    first = TS_FP_UPDATE()
    first.updateCode = FASTPATH_UPDATETYPE.SYNCHRONIZE
    first.fragmentation = FASTPATH_FRAGMENT.FIRST
    first.updateData = b"ab"
    first.size = 2
    last = TS_FP_UPDATE()
    last.updateCode = FASTPATH_UPDATETYPE.SYNCHRONIZE
    last.fragmentation = FASTPATH_FRAGMENT.LAST
    last.updateData = b"cd"
    last.size = 2

    assert reassembler.feed(first) is None
    combined = reassembler.feed(last)
    assert combined.updateData == b"abcd"
    assert combined.fragmentation == FASTPATH_FRAGMENT.SINGLE


async def test_terminate_sets_disconnected_and_queue_sentinel():
    connection = make_bare_rdp_connection()
    connection._RDPConnection__connection = ScriptedUniConnection()
    connection.send_disconnect = AsyncMock(return_value=(True, None))
    await asyncio.wait_for(connection.terminate(), timeout=DEFAULT_TIMEOUT)
    assert connection.disconnected_evt.is_set()
    sentinel = await asyncio.wait_for(connection.ext_out_queue.get(), timeout=DEFAULT_TIMEOUT)
    assert sentinel is None


class ClosedBeforeConfirmConnection:
    async def write(self, data):
        pass

    async def read_one(self):
        return None


async def test_x224_negotiate_reports_connection_closed():
    x224net = X224Network(ClosedBeforeConfirmConnection())
    reply, error = await asyncio.wait_for(
        x224net.client_negotiate(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert reply is None
    assert isinstance(error, ConnectionError)


class ErroredReadConnection:
    """Mimics asysocks UniConnection.read(), which yields a bare None on transport errors."""

    def __init__(self):
        self.packetizer = SimpleNamespace(packetizer_control=lambda cmd: None)

    async def read(self):
        yield None


async def test_x224_reader_reports_connection_closed_on_bare_none():
    connection = make_bare_rdp_connection()
    connection._RDPConnection__connection = ErroredReadConnection()
    connection.terminate = AsyncMock()
    result, error = await asyncio.wait_for(
        connection._RDPConnection__x224_reader(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert result is None
    assert isinstance(error, ConnectionError)
    connection.terminate.assert_awaited_once()


def make_security_exchange_connection(encryption_method):
    connection = make_bare_rdp_connection()
    connection._RDPConnection__server_connect_pdu = {
        TS_UD_TYPE.SC_SECURITY: SimpleNamespace(
            encryptionMethod=encryption_method,
            serverRandom=b"\x22" * 32,
            serverCertificate=SimpleNamespace(encrypt=lambda data: b"encrypted-client-random"),
        )
    }
    connection.handle_out_data = AsyncMock()
    return connection


@pytest.mark.parametrize("encryption_method, keysize", [(0x01, 40), (0x08, 56), (0x02, 128)])
async def test_security_exchange_uses_server_selected_key_size(encryption_method, keysize):
    connection = make_security_exchange_connection(encryption_method)
    result, error = await asyncio.wait_for(
        connection._RDPConnection__security_exchange(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert error is None
    assert result is True
    assert connection.cryptolayer.keysize == keysize
    connection.handle_out_data.assert_awaited_once()


@pytest.mark.parametrize("encryption_method", [0x00, 0x10])
async def test_security_exchange_rejects_unsupported_method(encryption_method):
    connection = make_security_exchange_connection(encryption_method)
    result, error = await asyncio.wait_for(
        connection._RDPConnection__security_exchange(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert result is None
    assert "unsupported" in str(error)
    connection.handle_out_data.assert_not_awaited()


def mcs_per_codec():
    return _get_asn1_codecs()[1]


class RecordingX224:
    def __init__(self, replies=()):
        self.writes = []
        self._replies = list(replies)

    async def write(self, data):
        self.writes.append(bytes(data))

    async def read(self):
        return self._replies.pop(0)


async def test_erect_domain_request_matches_ms_rdpbcgr_example():
    connection = make_bare_rdp_connection()
    connection._t125_per_codec = mcs_per_codec()
    connection._x224net = RecordingX224()

    result, error = await connection._RDPConnection__erect_domain()

    assert error is None
    # MS-RDPBCGR 4.1.5: choice 0x04, subHeight (len 1, 0), subInterval (len 1, 0)
    assert connection._x224net.writes == [bytes.fromhex("0401000100")]


async def test_join_channels_joins_user_channel_first():
    codec = mcs_per_codec()
    initiator = 1
    channel_ids = [initiator + 1001, 1003]
    replies = [
        SimpleNamespace(data=codec.encode("DomainMCSPDU", ("channelJoinConfirm", {
            "result": "rt-successful", "initiator": initiator, "requested": channel_id, "channelId": channel_id,
        })))
        for channel_id in channel_ids
    ]
    connection = make_bare_rdp_connection()
    connection._initiator = initiator
    connection._t125_per_codec = codec
    connection._x224net = RecordingX224(replies)
    connection._RDPConnection__joined_channels["MCS"].run = AsyncMock()
    connection._RDPConnection__x224_reader = AsyncMock(return_value=(None, None))

    result, error = await asyncio.wait_for(
        connection._RDPConnection__join_channels(),
        timeout=DEFAULT_TIMEOUT,
    )
    await asyncio.sleep(0)

    assert error is None
    assert result is True
    requests = [codec.decode("DomainMCSPDU", data) for data in connection._x224net.writes]
    assert [name for name, _ in requests] == ["channelJoinRequest", "channelJoinRequest"]
    assert [body["channelId"] for _, body in requests] == channel_ids
    assert all(body["initiator"] == initiator for _, body in requests)


async def test_share_data_pdu_total_length_matches_wire_length():
    codec = mcs_per_codec()
    connection = make_bare_rdp_connection()
    connection._initiator = 1
    connection._t125_per_codec = codec
    connection._x224net = RecordingX224()

    data_hdr = TS_SHAREDATAHEADER()
    data_hdr.shareID = 0x103EA
    data_hdr.streamID = STREAM_TYPE.MED
    data_hdr.pduType2 = PDUTYPE2.SYNCHRONIZE
    sync = TS_SYNCHRONIZE_PDU()
    sync.targetUser = 1003
    await asyncio.wait_for(
        connection.handle_out_data(sync, None, data_hdr, None, 1003, False),
        timeout=DEFAULT_TIMEOUT,
    )

    _, body = codec.decode("DomainMCSPDU", connection._x224net.writes[0])
    user_data = body["userData"]
    assert len(user_data) == 22
    assert TS_SHARECONTROLHEADER.from_bytes(user_data).totalLength == len(user_data)
    assert TS_SHAREDATAHEADER.from_bytes(user_data).uncompressedLength == len(user_data)


def make_server_synchronize():
    sync = TS_SYNCHRONIZE_PDU()
    sync.targetUser = 1002
    body = sync.to_bytes()
    header = TS_SHAREDATAHEADER()
    header.shareControlHeader = TS_SHARECONTROLHEADER()
    header.shareControlHeader.totalLength = 18 + len(body)
    header.shareControlHeader.pduType = PDUTYPE.DATAPDU
    header.shareControlHeader.pduVersion = 1
    header.shareControlHeader.pduSource = 1002
    header.shareID = 0x103EA
    header.streamID = STREAM_TYPE.MED
    header.uncompressedLength = 18 + len(body)
    header.pduType2 = PDUTYPE2.SYNCHRONIZE
    header.compressedType = CompType(0)
    header.compressedLength = 0
    return header.to_bytes() + body


async def test_capability_exchange_sends_finalization_before_server_synchronize(monkeypatch):
    connection = make_bare_rdp_connection()
    mcs = connection._RDPConnection__joined_channels["MCS"]
    mcs.out_queue = asyncio.Queue()
    connection.iosettings = RDPIOSettings()
    connection.target = SimpleNamespace(timeout=5)
    connection._RDPConnection__server_connect_pdu = {TS_UD_TYPE.SC_SECURITY: SimpleNamespace(encryptionLevel=0)}

    demand_active = TS_SHARECONTROLHEADER()
    demand_active.totalLength = 6
    demand_active.pduType = PDUTYPE.DEMANDACTIVEPDU
    demand_active.pduVersion = 1
    demand_active.pduSource = 1002
    connection._RDPConnection__pending_mcs_data = (demand_active.to_bytes(), None)
    monkeypatch.setattr(
        "aardwolf.connection.TS_DEMAND_ACTIVE_PDU.from_bytes",
        lambda data: SimpleNamespace(capabilitySets=[]),
    )

    sent = []

    async def record(dataobj, sec_hdr, datacontrol_hdr, sharecontrol_hdr, channel_id, is_fastpath):
        if sharecontrol_hdr is not None:
            sent.append(sharecontrol_hdr.pduType.name)
        else:
            name = datacontrol_hdr.pduType2.name
            if isinstance(dataobj, TS_CONTROL_PDU):
                name += ":" + dataobj.action.name
            sent.append(name)
        if datacontrol_hdr is not None and datacontrol_hdr.pduType2 == PDUTYPE2.FONTLIST:
            await mcs.out_queue.put((make_server_synchronize(), None))

    connection.handle_out_data = record
    result, error = await asyncio.wait_for(
        connection._RDPConnection__handle_mandatory_capability_exchange(),
        timeout=DEFAULT_TIMEOUT,
    )

    assert error is None
    assert result is True
    assert sent == [
        "CONFIRMACTIVEPDU",
        "SYNCHRONIZE",
        "CONTROL:COOPERATE",
        "CONTROL:REQUEST_CONTROL",
        "FONTLIST",
    ]
    assert mcs.out_queue.empty()


class FakeStream:
    def __init__(self, data: bytes):
        self._buffer = data
        self.writes = []

    async def readuntil(self, separator: bytes) -> bytes:
        index = self._buffer.find(separator)
        if index < 0:
            raise asyncio.IncompleteReadError(self._buffer, None)
        index += len(separator)
        chunk = self._buffer[:index]
        self._buffer = self._buffer[index:]
        return chunk

    async def readexactly(self, size: int) -> bytes:
        if len(self._buffer) < size:
            raise asyncio.IncompleteReadError(self._buffer, size)
        chunk = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return chunk

    async def write(self, data: bytes) -> None:
        self.writes.append(bytes(data))


async def test_vnc_banner_exchange_replies_with_client_version():
    connection = object.__new__(VNCConnection)
    connection.client_version = "003.008"
    stream = FakeStream(b"RFB 003.008\n")
    connection._VNCConnection__reader = stream
    connection._VNCConnection__writer = stream
    result, error = await asyncio.wait_for(
        connection._VNCConnection__banner_exchange(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert result is True
    assert error is None
    assert connection.server_version == "003.008"
    assert stream.writes == [b"RFB 003.008\n"]


async def test_vnc_null_security_handshake_accepts_type_one():
    connection = object.__new__(VNCConnection)
    connection._VNCConnection__selected_security_type = 1
    connection.server_supp_security_types = []
    stream = FakeStream(bytes([1, 1]))
    connection._VNCConnection__reader = stream
    result, error = await asyncio.wait_for(
        connection._VNCConnection__security_handshake(),
        timeout=DEFAULT_TIMEOUT,
    )
    assert result is True
    assert error is None
    assert 1 in connection.server_supp_security_types
