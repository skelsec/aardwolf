"""Fast-path bitmap update payload parse."""

import pytest

from aardwolf.protocol.fastpath.bitmap import TS_BITMAP_DATA, TS_BITMAP_FLAG, TS_UPDATE_BITMAP_DATA


pytestmark = pytest.mark.unit


def test_uncompressed_bitmap_data_round_trip():
    bitmap = TS_BITMAP_DATA()
    bitmap.destLeft = 0
    bitmap.destTop = 0
    bitmap.destRight = 7
    bitmap.destBottom = 0
    bitmap.width = 8
    bitmap.height = 1
    bitmap.bitsPerPixel = 16
    bitmap.flags = TS_BITMAP_FLAG(0)
    bitmap.bitmapDataStream = b"\x00" * 16
    parsed = TS_BITMAP_DATA.from_bytes(bitmap.to_bytes())
    assert parsed.width == 8
    assert parsed.height == 1
    assert parsed.bitmapDataStream == b"\x00" * 16
    assert parsed.to_bytes() == bitmap.to_bytes()


def test_update_bitmap_data_zero_rectangles():
    update = TS_UPDATE_BITMAP_DATA()
    update.numberRectangles = 0
    update.rectangles = []
    parsed = TS_UPDATE_BITMAP_DATA.from_bytes(update.to_bytes())
    assert parsed.numberRectangles == 0
    assert parsed.rectangles == []
