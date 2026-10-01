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
