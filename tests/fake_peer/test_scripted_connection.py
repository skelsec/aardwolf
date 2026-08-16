"""Scripted in-process peer tests for RDP input and VNC handshake."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.connection import RDPConnection
from aardwolf.protocol.T128.inputeventpdu import TS_INPUT_PDU_DATA
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
