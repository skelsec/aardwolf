"""Slow-path share-data decompression helper."""

import pytest

from aardwolf.protocol.T128.share import (
    PDUTYPE,
    PDUTYPE2,
    STREAM_TYPE,
    CompType,
    TS_SHARECONTROLHEADER,
    TS_SHAREDATAHEADER,
    normalize_share_data_pdu,
)
from aardwolf.protocol.compression import (
    BulkCompressionError,
    BulkCompressionFlags,
    BulkCompressionType,
    BulkDecompressor,
)
from tests.unit.compression.test_native_vs_reference import (
    compression_flags,
    make_mppc_vector,
)


pytestmark = pytest.mark.unit


def make_share_data_pdu(payload, compressed_type=CompType(0), uncompressed_length=None):
    header = TS_SHAREDATAHEADER()
    header.shareControlHeader = TS_SHARECONTROLHEADER()
    header.shareControlHeader.pduType = PDUTYPE.DATAPDU
    header.shareControlHeader.pduVersion = 1
    header.shareControlHeader.pduSource = 1003
    header.shareID = 0x000103EA
    header.streamID = STREAM_TYPE.MED
    header.pduType2 = PDUTYPE2.UPDATE
    header.compressedType = compressed_type
    header.compressedLength = 0
    header.uncompressedLength = (
        uncompressed_length if uncompressed_length is not None else len(payload) + 4
    )
    header.shareControlHeader.totalLength = 18 + len(payload)
    return header.to_bytes() + payload


def test_normalize_uncompressed_share_data_is_passthrough():
    wire = make_share_data_pdu(b"raw-update")
    assert normalize_share_data_pdu(wire, None) == wire


def test_normalize_non_data_pdu_is_passthrough():
    header = TS_SHARECONTROLHEADER()
    header.totalLength = 6
    header.pduType = PDUTYPE.DEMANDACTIVEPDU
    header.pduVersion = 1
    header.pduSource = 1003
    wire = header.to_bytes()
    assert normalize_share_data_pdu(wire, None) == wire


def test_normalize_compressed_share_data_without_decompressor_fails():
    flags = CompType(
        int(BulkCompressionFlags.COMPRESSED) | int(BulkCompressionType.RDP4_8K)
    )
    wire = make_share_data_pdu(b"\xff", compressed_type=flags)
    with pytest.raises(BulkCompressionError):
        normalize_share_data_pdu(wire, None)


def test_normalize_compressed_share_data_with_mppc():
    decompressor = BulkDecompressor(BulkCompressionType.RDP4_8K)
    payload = make_mppc_vector(literals=b"abc")
    flags = CompType(
        int(
            compression_flags(
                BulkCompressionType.RDP4_8K,
                BulkCompressionFlags.COMPRESSED,
                BulkCompressionFlags.AT_FRONT,
                BulkCompressionFlags.FLUSHED,
            )
        )
    )
    wire = make_share_data_pdu(payload, compressed_type=flags, uncompressed_length=7)
    normalized = normalize_share_data_pdu(wire, decompressor)
    parsed = TS_SHAREDATAHEADER.from_bytes(normalized)
    assert int(parsed.compressedType) == 0
    assert normalized[18:] == b"abc"
