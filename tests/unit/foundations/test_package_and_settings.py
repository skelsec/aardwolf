"""Package import, URL targets, factory dialect, and IO settings."""

import pytest

from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.target import RDPConnectionDialect, RDPTarget
from aardwolf.connection import RDPConnection
from aardwolf.extensions.RDPECLIP.channel import RDPECLIPChannel
from aardwolf.extensions.RDPEDYC.channel import RDPEDYCChannel
from aardwolf.extensions.RDPEFS.providers.memory import MemoryDriveProvider
from aardwolf.protocol.compression import BulkCompressionType
from aardwolf.vncconnection import VNCConnection


pytestmark = pytest.mark.unit


def test_package_and_native_extensions_import():
    import aardwolf
    import aardwolf._rle
    import aardwolf._bulk
    import librlers

    assert aardwolf._rle.bitmap_decompress is not None
    assert aardwolf._bulk.NativeBulkDecompressor is not None or hasattr(
        aardwolf._bulk, "NativeBulkDecompressor"
    )
    assert librlers.bitmap_decompress is aardwolf._rle.bitmap_decompress


def test_ardpscan_entry_point_is_importable():
    from aardwolf.examples.scanners.__main__ import main, rdpscan_options

    assert callable(main)
    assert "login" in rdpscan_options
    assert "caps" in rdpscan_options
    assert "screen" in rdpscan_options


@pytest.mark.parametrize(
    "url,dialect,port",
    [
        ("rdp://10.0.0.1", RDPConnectionDialect.RDP, 3389),
        ("rdp://10.0.0.1:3390", RDPConnectionDialect.RDP, 3390),
        ("vnc://10.0.0.1", RDPConnectionDialect.VNC, 5800),
        ("vnc://10.0.0.1:5901", RDPConnectionDialect.VNC, 5901),
        ("rdp+ntlm-password://TEST\\user:pass@10.0.0.1", RDPConnectionDialect.RDP, 3389),
    ],
)
def test_target_from_url(url, dialect, port):
    target = RDPTarget.from_url(url)
    assert target.dialect == dialect
    assert target.port == port


def test_target_helpers():
    target = RDPTarget(ip="10.0.0.5", hostname="host.example")
    assert target.get_ip() == "10.0.0.5"
    assert target.get_hostname() == "host.example"
    assert target.get_hostname_or_ip() == "host.example"
    assert target.get_port() == 3389
    assert "termsrv" in target.to_target_string()


def test_factory_creates_rdp_and_vnc_connections():
    settings = RDPIOSettings()
    rdp = RDPConnectionFactory.from_url("rdp://10.0.0.1", settings)
    connection = rdp.get_connection(settings)
    assert isinstance(connection, RDPConnection)

    vnc = RDPConnectionFactory.from_url("vnc://10.0.0.1", settings)
    connection = vnc.get_connection(settings)
    assert isinstance(connection, VNCConnection)


def test_factory_create_connection_newtarget_ip():
    settings = RDPIOSettings()
    factory = RDPConnectionFactory.from_url("rdp://10.0.0.1", settings)
    connection = factory.create_connection_newtarget("192.0.2.9", settings)
    assert connection.target.ip == "192.0.2.9"


def test_iosettings_defaults():
    settings = RDPIOSettings()
    assert settings.video_width == 1024
    assert settings.video_height == 768
    assert settings.fastpath_max_request_size == 608299
    assert settings.bulk_compression_max_type == BulkCompressionType.RDP61
    assert RDPECLIPChannel in settings.channels
    assert RDPEDYCChannel in settings.channels
    assert settings.client_keyboard == "enus"
    assert settings.vnc_encodings == [2, 1, 0]
    assert settings.drives == []
    assert all(getattr(channel, "name", None) != "rdpdr" for channel in settings.channels)


def test_connection_joins_rdpdr_when_drives_configured():
    settings = RDPIOSettings()
    settings.drives = [MemoryDriveProvider("MEM", {"a.txt": b"a"})]
    connection = RDPConnectionFactory.from_url("rdp://10.0.0.1", settings).get_connection(settings)
    assert "rdpdr" in connection._RDPConnection__joined_channels
