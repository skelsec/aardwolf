"""Live xrdp capability exchange, screenshot, and input smoke."""

import asyncio

import pytest

from aardwolf.commons.queuedata.constants import MOUSEBUTTON, VIDEO_FORMAT

from .test_negotiate_login import _connection


pytestmark = [
    pytest.mark.xrdp,
    pytest.mark.asyncio,
    pytest.mark.timeout(90),
]


@pytest.mark.capability("screenshot")
@pytest.mark.capability("rdp_plain")
async def test_xrdp_screenshot_buffer(xrdp_profile):
    connection = _connection(xrdp_profile)
    try:
        result, error = await asyncio.wait_for(connection.connect(), timeout=60)
        if error is not None:
            pytest.skip("xrdp login was not available: {}".format(type(error).__name__))
        assert result is True
        await asyncio.sleep(2)
        if not getattr(connection, "desktop_buffer_has_data", False):
            pytest.skip("xrdp did not deliver a desktop buffer")
        buffer = connection.get_desktop_buffer(VIDEO_FORMAT.RAW)
        assert buffer is not None
        assert len(buffer) > 0
    finally:
        await asyncio.wait_for(connection.terminate(), timeout=10)


@pytest.mark.capability("keyboard_mouse")
@pytest.mark.capability("rdp_plain")
async def test_xrdp_keyboard_mouse_smoke(xrdp_profile):
    connection = _connection(xrdp_profile)
    try:
        result, error = await asyncio.wait_for(connection.connect(), timeout=60)
        if error is not None:
            pytest.skip("xrdp login was not available: {}".format(type(error).__name__))
        assert result is True
        await asyncio.wait_for(
            connection.send_mouse(MOUSEBUTTON.MOUSEBUTTON_HOVER, 20, 20, False),
            timeout=5,
        )
        await asyncio.wait_for(connection.send_key_scancode(0x1E, False, False), timeout=5)
    finally:
        await asyncio.wait_for(connection.terminate(), timeout=10)
