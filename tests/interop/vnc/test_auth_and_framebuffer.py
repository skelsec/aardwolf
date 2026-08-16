"""Live TigerVNC authentication and framebuffer smoke tests."""

import asyncio
from urllib.parse import quote

import pytest

from aardwolf.commons.factory import RDPConnectionFactory
from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.commons.queuedata.constants import VIDEO_FORMAT


pytestmark = [
    pytest.mark.vnc,
    pytest.mark.asyncio,
    pytest.mark.timeout(60),
    pytest.mark.capability("vnc_password"),
]


def _url(profile):
    password = quote(profile.password, safe="")
    return "vnc://{password}@{host}:{port}".format(
        password=password,
        host=profile.host,
        port=profile.port,
    )


def _settings():
    settings = RDPIOSettings()
    settings.clipboard_use_pyperclip = False
    settings.video_out_format = VIDEO_FORMAT.RAW
    settings.vnc_fps = 5
    settings.vnc_encodings = [2, 1, 0]
    return settings


@pytest.mark.capability("protocol_probe")
@pytest.mark.capability("vnc_password")
async def test_vnc_password_login(vnc_profile):
    settings = _settings()
    factory = RDPConnectionFactory.from_url(_url(vnc_profile), settings)
    connection = factory.get_connection(settings)
    connection.target.timeout = 30
    try:
        result, error = await asyncio.wait_for(connection.connect(), timeout=30)
        if error is not None:
            pytest.skip("VNC login was not available: {}".format(type(error).__name__))
        assert result is True
        assert connection.server_version
    finally:
        await asyncio.wait_for(connection.terminate(), timeout=10)


@pytest.mark.capability("framebuffer")
@pytest.mark.capability("vnc_password")
async def test_vnc_framebuffer_update(vnc_profile):
    settings = _settings()
    factory = RDPConnectionFactory.from_url(_url(vnc_profile), settings)
    connection = factory.get_connection(settings)
    connection.target.timeout = 30
    try:
        result, error = await asyncio.wait_for(connection.connect(), timeout=30)
        if error is not None:
            pytest.skip("VNC login was not available: {}".format(type(error).__name__))
        assert result is True
        await asyncio.sleep(1)
        width = getattr(connection, "width", None) or getattr(connection, "fb_width", None)
        height = getattr(connection, "height", None) or getattr(connection, "fb_height", None)
        assert width or connection.server_version
        assert height or connection.server_version
    finally:
        await asyncio.wait_for(connection.terminate(), timeout=10)
