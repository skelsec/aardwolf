"""TPKT and CredSSP packetizer framing."""

import pytest

from aardwolf.network.tpkt import CredSSPPacketizer, TPKTPacketizer
from aardwolf.protocol.tpkt import TPKT
from aardwolf.protocol.x224.data import Data


pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_tpkt_packetizer_emits_complete_slow_path_packets():
    packetizer = TPKTPacketizer()
    inner = Data()
    inner.data = b"abc"
    tpkt = TPKT()
    tpkt.tpdu = inner.to_bytes()
    wire = tpkt.to_bytes()

    packets = []
    async for item in packetizer.data_in(wire[:3] + wire[3:]):
        if item is not None:
            packets.append(item)
    assert len(packets) == 1
    is_fastpath, payload = packets[0]
    assert is_fastpath is False
    assert payload == inner.to_bytes()


@pytest.mark.asyncio
async def test_tpkt_packetizer_holds_partial_then_completes():
    packetizer = TPKTPacketizer()
    tpkt = TPKT()
    tpkt.tpdu = b"\x02\xf0\x80xyz"
    wire = tpkt.to_bytes()

    first = []
    async for item in packetizer.data_in(wire[:4]):
        if item is not None:
            first.append(item)
    assert first == []

    second = []
    async for item in packetizer.data_in(wire[4:]):
        if item is not None:
            second.append(item)
    assert len(second) == 1
    assert second[0][1] == tpkt.tpdu


@pytest.mark.asyncio
async def test_tpkt_packetizer_fastpath_one_byte_length():
    packetizer = TPKTPacketizer()
    payload = b"\x00\x06\x00\x00\x00\x00"
    packets = []
    async for item in packetizer.data_in(payload):
        if item is not None:
            packets.append(item)
    assert packets == [(True, payload)]


@pytest.mark.asyncio
async def test_tpkt_packetizer_wraps_outbound_tpkt():
    packetizer = TPKTPacketizer()
    chunks = []
    async for chunk in packetizer.data_out(b"inner"):
        chunks.append(chunk)
    parsed = TPKT.from_bytes(chunks[0])
    assert parsed.tpdu == b"inner"


@pytest.mark.asyncio
async def test_credssp_packetizer_short_length():
    packetizer = CredSSPPacketizer()
    payload = bytes([0x30, 0x04, 0x01, 0x02, 0x03, 0x04])
    packets = []
    async for item in packetizer.data_in(payload):
        if item is not None:
            packets.append(item)
    assert packets == [payload]


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason="KF-0002: CredSSP packetizer waits for 6 header bytes before decoding short BER",
)
async def test_credssp_packetizer_short_ber_under_preread():
    packetizer = CredSSPPacketizer()
    payload = bytes([0x30, 0x03, 0x01, 0x02, 0x03])
    packets = []
    async for item in packetizer.data_in(payload):
        if item is not None:
            packets.append(item)
    assert packets == [payload]


def test_credssp_length_long_form():
    data = bytes([0x30, 0x82, 0x00, 0x05]) + b"abcde"
    assert CredSSPPacketizer.calcualte_length(data) == 9
