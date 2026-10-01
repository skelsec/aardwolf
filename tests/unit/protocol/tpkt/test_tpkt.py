"""TPKT ISO transport header round-trips."""

import pytest

from aardwolf.protocol.tpkt import TPKT


pytestmark = pytest.mark.unit


def test_tpkt_round_trip():
    packet = TPKT()
    packet.tpdu = b"\x02\xf0\x80hello"
    wire = packet.to_bytes()

    assert wire[:2] == b"\x03\x00"
    assert int.from_bytes(wire[2:4], "big") == len(wire)

    parsed = TPKT.from_bytes(wire)
    assert parsed.version == 3
    assert parsed.reserved == 0
    assert parsed.tpdu == packet.tpdu
    assert parsed.to_bytes() == wire


def test_tpkt_empty_tpdu():
    packet = TPKT()
    packet.tpdu = b""
    parsed = TPKT.from_bytes(packet.to_bytes())
    assert parsed.tpdu == b""
    assert parsed.length == 4
