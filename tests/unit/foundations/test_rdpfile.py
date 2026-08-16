"""Parse, write, and map Microsoft .rdp connection files."""

from pathlib import Path

import pytest

from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.rdpfile import (
    RDPFile,
    RDPFileType,
    split_rdp_address,
    split_rdp_username,
)
from aardwolf.commons.target import RDPTarget
from aardwolf.extensions.RDPECLIP.channel import RDPECLIPChannel
from aardwolf.protocol.T125.extendedinfopacket import PERF
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS


pytestmark = pytest.mark.unit


SAMPLE_TEXT = """\
screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
compression:i:1
disable wallpaper:i:0
allow font smoothing:i:1
disable themes:i:1
full address:s:rdp.contoso.local:3390
username:s:CONTOSO\\alice
domain:s:CONTOSO
alternate shell:s:C:\\Windows\\System32\\cmd.exe
shell working directory:s:C:\\Windows\\System32
redirectclipboard:i:1
enablecredsspsupport:i:1
authentication level:i:2
gatewayhostname:s:gw.contoso.local
restricted admin:i:1
password 51:b:01020304AABB
custom vendor:s:kept
"""


def test_split_rdp_address_host_port_and_ipv6():
    assert split_rdp_address("10.0.0.5") == ("10.0.0.5", None)
    assert split_rdp_address("10.0.0.5:3390") == ("10.0.0.5", 3390)
    assert split_rdp_address("rdp.example:3389") == ("rdp.example", 3389)
    assert split_rdp_address("2001:db8::1") == ("2001:db8::1", None)
    assert split_rdp_address("[2001:db8::1]:3390") == ("2001:db8::1", 3390)


def test_split_rdp_username_domain_and_upn():
    assert split_rdp_username(r"CONTOSO\alice") == ("alice", "CONTOSO")
    assert split_rdp_username("alice@contoso.local") == ("alice@contoso.local", None)
    assert split_rdp_username("") == (None, None)


def test_from_text_parses_known_and_unknown_properties():
    rdp = RDPFile.from_text(SAMPLE_TEXT)
    assert rdp["full address"] == "rdp.contoso.local:3390"
    assert rdp["desktopwidth"] == 1920
    assert rdp["password 51"] == bytes.fromhex("01020304AABB")
    assert rdp["custom vendor"] == "kept"
    assert rdp.username == "alice"
    assert rdp.domain == "CONTOSO"
    assert rdp.alternate_shell == r"C:\Windows\System32\cmd.exe"
    assert rdp.gateway_hostname == "gw.contoso.local"
    assert rdp.restricted_admin is True
    assert rdp.password51 == bytes.fromhex("01020304AABB")


def test_case_insensitive_lookup_preserves_original_name():
    rdp = RDPFile.from_text("full address:s:host\r\n")
    assert "FULL ADDRESS" in rdp
    assert list(rdp.keys()) == ["full address"]


def test_malformed_line_raises():
    with pytest.raises(ValueError, match="Malformed RDP line 1"):
        RDPFile.from_text("not-a-setting\n")


def test_invalid_integer_raises():
    with pytest.raises(ValueError, match="Invalid integer"):
        RDPFile.from_text("desktopwidth:i:wide\n")


def test_text_and_utf16_round_trip(tmp_path: Path):
    original = RDPFile.from_text(SAMPLE_TEXT)
    text = original.to_text()
    assert text.endswith("\r\n")
    assert "custom vendor:s:kept" in text

    encoded = original.to_bytes()
    assert encoded.startswith(b"\xff\xfe")
    parsed = RDPFile.from_bytes(encoded)
    assert dict(parsed.items()) == dict(original.items())

    path = tmp_path / "session.rdp"
    original.to_file(path)
    from_disk = RDPFile.from_file(path)
    assert from_disk["session bpp"] == 32
    assert from_disk["password 51"] == original["password 51"]


def test_utf8_without_bom_is_accepted():
    rdp = RDPFile.from_bytes(b"full address:s:10.0.0.8\nserver port:i:3389\n")
    assert rdp["full address"] == "10.0.0.8"
    assert rdp["server port"] == 3389


def test_to_target_prefers_server_port_and_maps_auth_level():
    rdp = RDPFile.from_text(
        "full address:s:10.1.2.3:3390\nserver port:i:4400\nauthentication level:i:0\n"
    )
    target = rdp.to_target()
    assert target.ip == "10.1.2.3"
    assert target.port == 4400
    assert target.unsafe_ssl is True


def test_to_target_requires_full_address():
    with pytest.raises(ValueError, match="full address"):
        RDPFile().to_target()


def test_to_iosettings_applies_display_perf_and_clipboard():
    rdp = RDPFile.from_text(
        "desktopwidth:i:1280\n"
        "desktopheight:i:720\n"
        "session bpp:i:24\n"
        "compression:i:0\n"
        "disable wallpaper:i:0\n"
        "allow font smoothing:i:1\n"
        "redirectclipboard:i:0\n"
        "enablecredsspsupport:i:0\n"
    )
    settings = rdp.to_iosettings()
    assert settings.video_width == 1280
    assert settings.video_height == 720
    assert settings.video_bpp_max == 24
    assert settings.bulk_compression_max_type is None
    assert PERF.DISABLE_WALLPAPER not in settings.performance_flags
    assert PERF.ENABLE_FONT_SMOOTHING in settings.performance_flags
    assert RDPECLIPChannel not in settings.channels
    assert settings.supported_protocols == SUPP_PROTOCOLS.RDP | SUPP_PROTOCOLS.SSL


def test_desktop_size_id_used_when_width_height_missing():
    rdp = RDPFile.from_text("desktop size id:i:3\nfull address:s:host\n")
    settings = rdp.to_iosettings()
    assert settings.video_width == 1280
    assert settings.video_height == 1024


def test_from_settings_and_factory_round_trip():
    target = RDPTarget(ip="192.0.2.10", port=3391, hostname=None, domain="TEST")
    settings = RDPIOSettings()
    settings.video_width = 800
    settings.video_height = 600
    settings.video_bpp_max = 16
    written = RDPFile.from_settings(target, settings, username="bob", domain="TEST")
    assert written["full address"] == "192.0.2.10"
    assert written["server port"] == 3391
    assert written["username"] == "bob"
    assert written["desktopwidth"] == 800
    assert written["redirectclipboard"] == 1

    factory = RDPConnectionFactory.from_rdp(written)
    assert factory.target.ip == "192.0.2.10"
    assert factory.target.port == 3391
    assert factory.iosettings.video_width == 800


def test_factory_from_rdp_file(tmp_path: Path):
    path = tmp_path / "box.rdp"
    Path(path).write_text("full address:s:10.0.0.9\ndesktopwidth:i:1024\ndesktopheight:i:768\n")
    factory = RDPConnectionFactory.from_rdp_file(path)
    assert factory.target.ip == "10.0.0.9"
    exported = factory.to_rdp_file()
    assert exported["full address"] == "10.0.0.9"


def test_set_infers_type_and_delete_removes_key():
    rdp = RDPFile()
    rdp["full address"] = "host"
    rdp["server port"] = 3389
    rdp["password 51"] = b"\xde\xad"
    assert rdp.get_int("server port") == 3389
    assert rdp.get_bytes("password 51") == b"\xde\xad"
    del rdp["server port"]
    assert "server port" not in rdp
    rdp.set("session bpp", "32", rdp_type=RDPFileType.INTEGER)
    assert rdp["session bpp"] == 32
