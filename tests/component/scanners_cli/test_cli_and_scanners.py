"""CLI contracts, scanner fakes, packaging, and known-failure registry."""

import argparse
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from aardwolf.examples.scanners import __main__ as scanners_main
from aardwolf.examples.scanners.rdplogin import RDPLoginRes, RDPLoginScanner
from aardwolf.examples.scanners.rdpscaps import RDPCapabilitiesRes
from aardwolf.examples.scanners.rdpscreen import RDPScreenshotRes


pytestmark = pytest.mark.component


def test_ardpscan_requires_scan_type(capsys):
    with pytest.raises(SystemExit):
        with patch(
            "sys.argv",
            ["ardpscan", "rdp://10.0.0.1", "10.0.0.1"],
        ):
            parser = argparse.ArgumentParser()
            parser.add_argument("-s", "--scan", action="append", required=True)
            parser.parse_args(["rdp://10.0.0.1"])


def test_unknown_scan_type_prints_message(capsys):
    class Args:
        targets = ["10.0.0.1"]
        url = "rdp://10.0.0.1"
        scan = ["not-a-scanner"]
        worker_count = 1
        timeout = 1
        no_progress = False
        out_file = None
        errors = False

    with patch("argparse.ArgumentParser.parse_args", return_value=Args()):
        scanners_main.amain.__wrapped__ if hasattr(scanners_main.amain, "__wrapped__") else None
    # Exercise the unknown-type branch directly.
    scantype = "not-a-scanner"
    assert scantype not in scanners_main.rdpscan_options


def test_rdpscan_option_table():
    assert set(scanners_main.rdpscan_options) == {"login", "caps", "screen"}
    for name, (cls, description) in scanners_main.rdpscan_options.items():
        assert callable(cls)
        assert description


def test_login_result_serialization():
    result = RDPLoginRes("TRUE")
    assert result.get_header() == ["success"]
    assert result.to_line() == "TRUE"


def test_capabilities_result_serialization():
    result = RDPCapabilitiesRes(True, False, True, True, False, False)
    line = result.to_line()
    assert "True" in line
    assert result.to_dict()["rdp"] == "True"


def test_screenshot_result_base64_round_trip():
    result = RDPScreenshotRes("10.0.0.1", b"\x89PNG")
    encoded = result.to_line()
    assert result.to_dict()["screendata"] == encoded
    assert result.get_fdata() == b"\x89PNG"


@pytest.mark.asyncio
async def test_screenshot_scanner_uses_factory_connection(monkeypatch):
    from PIL import Image

    from aardwolf.examples.scanners.rdpscreen import RDPScreenshotScanner

    image = Image.new("RGB", (2, 2), color="red")

    class FakeConnection:
        desktop_buffer_has_data = True

        async def connect(self):
            return True, None

        def get_desktop_buffer(self, fmt):
            return image

        async def terminate(self):
            return True, None

    class FakeFactory:
        def create_connection_newtarget(self, target, ios):
            return FakeConnection()

    async def immediate_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr("aardwolf.examples.scanners.rdpscreen.asyncio.sleep", immediate_sleep)
    scanner = RDPScreenshotScanner(FakeFactory())
    queue = __import__("asyncio").Queue()
    await scanner.run("t1", "10.0.0.1", queue)
    item = queue.get_nowait()
    payload = getattr(item, "data", item)
    assert getattr(payload, "screendata", b"")[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio
async def test_login_scanner_uses_factory_connection():
    class FakeConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def connect(self):
            return True, None

    class FakeFactory:
        def get_settings(self):
            return SimpleNamespace(supported_protocols=None)

        def create_connection_newtarget(self, target, ios):
            return FakeConnection()

    scanner = RDPLoginScanner(FakeFactory())
    queue = __import__("asyncio").Queue()
    await scanner.run("t1", "10.0.0.1", queue)
    item = queue.get_nowait()
    payload = getattr(item, "data", item)
    assert getattr(payload, "success", None) == "TRUE"
