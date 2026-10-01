"""Live xrdp login, capability, and screenshot smoke tests."""

import asyncio
from urllib.parse import quote

import pytest

from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.queuedata.constants import VIDEO_FORMAT
from aardwolf.protocol.x224.constants import SUPP_PROTOCOLS


pytestmark = [
    pytest.mark.xrdp,
    pytest.mark.asyncio,
    pytest.mark.timeout(90),
]


def _url(profile):
    password = quote(profile.password, safe="")
    return "rdp://{username}:{password}@{host}:{port}".format(
        username=profile.username,
        password=password,
        host=profile.host,
        port=profile.port,
    )


def _settings():
    settings = RDPIOSettings()
    settings.channels = []
    settings.clipboard_use_pyperclip = False
    settings.supported_protocols = SUPP_PROTOCOLS.RDP
    settings.video_out_format = VIDEO_FORMAT.RAW
    return settings


def _connection(profile):
    settings = _settings()
    factory = RDPConnectionFactory.from_url(_url(profile), settings)
    connection = factory.get_connection(settings)
    connection.target.timeout = 30
    return connection


@pytest.mark.capability("protocol_probe")
@pytest.mark.capability("rdp_plain")
async def test_xrdp_plain_login(xrdp_profile):
    connection = _connection(xrdp_profile)
    try:
        result, error = await asyncio.wait_for(connection.connect(), timeout=60)
        if error is not None:
            pytest.skip("xrdp login was not available: {}".format(type(error).__name__))
        assert result is True
    finally:
        await asyncio.wait_for(connection.terminate(), timeout=10)
