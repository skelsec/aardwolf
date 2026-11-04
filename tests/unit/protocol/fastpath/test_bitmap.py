"""Fast-path bitmap update payload parse."""

import pytest

from aardwolf.protocol.fastpath.bitmap import TS_BITMAP_DATA, TS_BITMAP_FLAG, TS_CD_HEADER, TS_UPDATE_BITMAP_DATA


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


def compressed_rectangle(left, data):
    bitmap = TS_BITMAP_DATA()
    bitmap.destLeft = left
    bitmap.destTop = 0
    bitmap.destRight = left + 3
    bitmap.destBottom = 0
    bitmap.width = 4
    bitmap.height = 1
    bitmap.bitsPerPixel = 32
    bitmap.flags = TS_BITMAP_FLAG.BITMAP_COMPRESSION
    bitmap.bitmapComprHdr = TS_CD_HEADER()
    bitmap.bitmapComprHdr.cbCompFirstRowSize = 0
    bitmap.bitmapComprHdr.cbCompMainBodySize = len(data)
    bitmap.bitmapComprHdr.cbScanWidth = 4
    bitmap.bitmapComprHdr.cbUncompressedSize = 16
    bitmap.bitmapDataStream = data
    return bitmap


def test_bitmap_length_includes_compression_header():
    # MS-RDPBCGR 2.2.9.1.1.3.1.2.2: bitmapLength covers bitmapComprHdr + bitmapDataStream
    raw = compressed_rectangle(0, b"\xaa" * 5).to_bytes()
    assert int.from_bytes(raw[16:18], "little") == 8 + 5
    parsed = TS_BITMAP_DATA.from_bytes(raw)
    assert parsed.bitmapComprHdr.cbCompMainBodySize == 5
    assert parsed.bitmapDataStream == b"\xaa" * 5
    assert parsed.to_bytes() == raw


def test_bitmap_update_with_compression_header_from_ironrdp_test_vector():
    # IronRDP crates/ironrdp-pdu/src/basic_output/bitmap/tests.rs BITMAP_BUFFER
    header = bytes.fromhex("01000100" "0007" "0004" "3f07" "3704" "4000" "3800" "1000" "0100" "5c00")
    compr_hdr = bytes.fromhex("0000" "5000" "1c00" "0400")
    body = bytes.fromhex(
        "210021000100200984210021002100120010d820000b000000000000"
        "00601e210000a883210055adffff45297acea3100e8245297aced582"
        "100100000000800e45299ef7ffff9ef74529210055ad1010a8d86012"
    )
    update = TS_UPDATE_BITMAP_DATA.from_bytes(header + compr_hdr + body)
    (rect,) = update.rectangles
    assert (rect.destLeft, rect.destTop, rect.width, rect.height, rect.bitsPerPixel) == (1792, 1024, 64, 56, 16)
    assert rect.bitmapLength == 92
    assert rect.bitmapComprHdr.cbCompMainBodySize == 80
    assert rect.bitmapComprHdr.cbScanWidth == 28
    assert rect.bitmapDataStream == body


def test_update_bitmap_data_with_compression_headers_keeps_rectangles_aligned():
    update = TS_UPDATE_BITMAP_DATA()
    update.rectangles = [compressed_rectangle(0, b"\x11" * 5), compressed_rectangle(4, b"\x22" * 7)]
    parsed = TS_UPDATE_BITMAP_DATA.from_bytes(update.to_bytes())
    assert [(r.destLeft, r.bitsPerPixel, r.bitmapDataStream) for r in parsed.rectangles] == [
        (0, 32, b"\x11" * 5),
        (4, 32, b"\x22" * 7),
    ]


def test_update_bitmap_data_zero_rectangles():
    update = TS_UPDATE_BITMAP_DATA()
    update.numberRectangles = 0
    update.rectangles = []
    parsed = TS_UPDATE_BITMAP_DATA.from_bytes(update.to_bytes())
    assert parsed.numberRectangles == 0
    assert parsed.rectangles == []
