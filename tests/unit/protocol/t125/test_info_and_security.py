"""T.125 client info and security-exchange packets."""

import pytest

from aardwolf.protocol.T125.infopacket import INFO_FLAG, TS_INFO_PACKET
from aardwolf.protocol.T125.securityexchangepdu import TS_SECURITY_PACKET
from aardwolf.protocol.T125.extendedinfopacket import TS_SYSTEMTIME


pytestmark = pytest.mark.unit


def test_info_packet_unicode_encodes_credentials():
    packet = TS_INFO_PACKET()
    packet.CodePage = 0
    packet.flags = INFO_FLAG.MOUSE | INFO_FLAG.UNICODE | INFO_FLAG.DISABLECTRLALTDEL
    packet.Domain = "TEST"
    packet.UserName = "alice"
    packet.Password = "secret"
    packet.AlternateShell = ""
    packet.WorkingDir = ""
    wire = packet.to_bytes()
    assert b"T\x00E\x00S\x00T\x00" in wire
    assert b"a\x00l\x00i\x00c\x00e\x00" in wire
    flags = int.from_bytes(wire[4:8], "little")
    assert flags & int(INFO_FLAG.UNICODE)


def test_info_packet_ascii_encodes_username():
    packet = TS_INFO_PACKET()
    packet.CodePage = 1252
    packet.flags = INFO_FLAG.MOUSE
    packet.Domain = ""
    packet.UserName = "bob"
    packet.Password = ""
    packet.AlternateShell = ""
    packet.WorkingDir = ""
    wire = packet.to_bytes()
    assert b"bob\x00" in wire
    flags = int.from_bytes(wire[4:8], "little")
    assert flags & int(INFO_FLAG.UNICODE) == 0


def test_security_packet_round_trip():
    packet = TS_SECURITY_PACKET()
    packet.encryptedClientRandom = b"\x11" * 32
    wire = packet.to_bytes()
    assert wire[:4] == (32).to_bytes(4, "little")
    parsed = TS_SECURITY_PACKET.from_bytes(wire)
    assert parsed.encryptedClientRandom.endswith(b"\x11" * 32)


def test_systemtime_round_trip():
    stamp = TS_SYSTEMTIME()
    stamp.wMonth = 3
    stamp.wDayOfWeek = 0
    stamp.wDay = 2
    stamp.wHour = 2
    stamp.wMinute = 0
    parsed = TS_SYSTEMTIME.from_bytes(stamp.to_bytes())
    assert parsed.wMonth == 3
    assert parsed.wDay == 2
    assert parsed.to_bytes() == stamp.to_bytes()
