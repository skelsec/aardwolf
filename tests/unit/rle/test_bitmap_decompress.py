"""Bitmap RLE native decoder and rectconvert image construction."""

import ast
import hashlib
from pathlib import Path

import pytest

from aardwolf import _rle
from aardwolf.utils import rectconvert as rectconvert_module
from aardwolf.utils.rectconvert import rectconvert


pytestmark = pytest.mark.unit


def compressed_417x8_16bpp_blob():
    source = Path(rectconvert_module.__file__).read_text(encoding="utf-8")
    for node in ast.parse(source).body:
        if not isinstance(node, ast.If):
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            names = [
                target.id for target in statement.targets if isinstance(target, ast.Name)
            ]
            if names == ["compressed_data"] and isinstance(statement.value, ast.Constant):
                return statement.value.value
    raise AssertionError("rectconvert compressed 417x8 blob was not found")


def test_uncompressed_16bpp_bitmap_decompress_length():
    width, height = 2, 2
    raw = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    pixels = _rle.bitmap_decompress(raw, width, height, 16, 0)
    assert len(pixels) == width * height * 4


# 2x2 planar RLE planes (MS-RDPEGDI 2.2.2.5.1): each scanline is a control byte with
# two raw bytes; the first scanline is absolute, the second is sign-magnitude delta
# encoded, and scanlines are stored bottom-up.
PLANAR_R = b"\x20\x0a\x14" + b"\x20\x0a\x05"  # bottom [10, 20], top [+5, -3] -> [15, 17]
PLANAR_G = b"\x20\x01\x02" + b"\x20\x00\x00"  # bottom [1, 2], top [1, 2]
PLANAR_B = b"\x20\x64\xc8" + b"\x20\x02\x02"  # bottom [100, 200], top [101, 201]
PLANAR_A = b"\x20\x80\x40" + b"\x20\x00\x00"  # bottom [128, 64], top [128, 64]


def planar_pixels(alpha):
    # decoder output is B, G, R, A per pixel, top row first
    top = [(101, 1, 15, alpha[0]), (201, 2, 17, alpha[1])]
    bottom = [(100, 1, 10, alpha[0]), (200, 2, 20, alpha[1])]
    return bytes(value for pixel in top + bottom for value in pixel)


def test_planar_32bpp_with_alpha_plane():
    data = b"\x10" + PLANAR_A + PLANAR_R + PLANAR_G + PLANAR_B
    pixels = _rle.bitmap_decompress(data, 2, 2, 32, 1)
    assert bytes(pixels) == planar_pixels((128, 64))


def test_planar_32bpp_without_alpha_plane_is_opaque():
    data = b"\x30" + PLANAR_R + PLANAR_G + PLANAR_B
    pixels = _rle.bitmap_decompress(data, 2, 2, 32, 1)
    assert bytes(pixels) == planar_pixels((0xFF, 0xFF))


@pytest.mark.parametrize(
    "header",
    [0x00, 0x20, 0x11, 0x18, 0x33, 0x38],
    ids=["raw", "raw-no-alpha", "color-loss", "chroma-subsampling", "na-color-loss", "na-chroma"],
)
def test_planar_32bpp_rejects_unsupported_format_header(header):
    data = bytes([header]) + PLANAR_A + PLANAR_R + PLANAR_G + PLANAR_B
    with pytest.raises(ValueError, match="Bad header"):
        _rle.bitmap_decompress(data, 2, 2, 32, 1)


def test_rectconvert_rejects_unsupported_bpp():
    with pytest.raises(ValueError, match="bitsPerPixel"):
        rectconvert(1, 1, 8, False, b"\x00")


def test_rectconvert_produces_rgba_image_from_uncompressed_pixels():
    image = rectconvert(2, 2, 16, False, b"\x00" * 8)
    assert image.mode == "RGBA"
    assert image.size == (2, 2)
    digest = hashlib.sha256(image.tobytes()).hexdigest()
    assert len(digest) == 64
    assert digest != hashlib.sha256(b"").hexdigest()


@pytest.mark.xfail(
    strict=True,
    reason="KF-0003: native 16-bpp RLE decoder rejects the in-tree 417x8 compressed sample",
)
def test_rectconvert_produces_rgba_image_from_compressed_blob():
    image = rectconvert(417, 8, 16, True, compressed_417x8_16bpp_blob())
    assert image.mode == "RGBA"
    assert image.size == (417, 8)
    digest = hashlib.sha256(image.tobytes()).hexdigest()
    assert len(digest) == 64
    assert digest != hashlib.sha256(b"").hexdigest()
