"""Virtual-channel PDU header and compressed-chunk normalization."""

import pytest

from aardwolf.protocol.channelpdu import CHANNEL_FLAG, CHANNEL_PDU_HEADER, normalize_channel_pdu
from aardwolf.protocol.compression import (
    BulkCompressionError,
    BulkCompressionFlags,
    BulkCompressionType,
    BulkDecompressor,
)


pytestmark = pytest.mark.unit


def test_channel_header_round_trip():
    header = CHANNEL_PDU_HEADER.serialize_packet(
        CHANNEL_FLAG.CHANNEL_FLAG_FIRST | CHANNEL_FLAG.CHANNEL_FLAG_LAST,
        b"clip-data",
    )
    wire = header.to_bytes()
    parsed = CHANNEL_PDU_HEADER.from_bytes(wire)
    assert parsed.length == len(b"clip-data")
    assert CHANNEL_FLAG.CHANNEL_FLAG_FIRST in parsed.flags
    assert parsed.data == b"clip-data"
    assert parsed.to_bytes() == wire


def test_channel_header_rejects_truncated_buffer():
    with pytest.raises(ValueError, match="Truncated"):
        CHANNEL_PDU_HEADER.from_bytes(b"\x00\x00")


def test_normalize_uncompressed_channel_is_passthrough():
    header = CHANNEL_PDU_HEADER.serialize_packet(
        CHANNEL_FLAG.CHANNEL_FLAG_FIRST | CHANNEL_FLAG.CHANNEL_FLAG_LAST,
        b"raw",
    )
    wire = header.to_bytes()
    assert normalize_channel_pdu(wire, None) == wire


def test_normalize_compressed_channel_without_decompressor_fails():
    header = CHANNEL_PDU_HEADER.serialize_packet(
        CHANNEL_FLAG.CHANNEL_FLAG_FIRST
        | CHANNEL_FLAG.CHANNEL_FLAG_LAST
        | CHANNEL_FLAG.CHANNEL_PACKET_COMPRESSED,
        b"\xff",
    )
    with pytest.raises(BulkCompressionError):
        normalize_channel_pdu(header.to_bytes(), None)


def test_normalize_compressed_channel_with_mppc():
    decompressor = BulkDecompressor(BulkCompressionType.RDP4_8K)
    from tests.unit.compression.test_native_vs_reference import (
        compression_flags,
        make_mppc_vector,
    )

    payload = make_mppc_vector(literals=b"abc")
    flags = CHANNEL_FLAG.CHANNEL_FLAG_FIRST | CHANNEL_FLAG.CHANNEL_FLAG_LAST
    flags |= CHANNEL_FLAG.CHANNEL_PACKET_COMPRESSED
    flags |= CHANNEL_FLAG.CHANNEL_PACKET_AT_FRONT
    flags |= CHANNEL_FLAG.CHANNEL_PACKET_FLUSHED
    header = CHANNEL_PDU_HEADER.serialize_packet(flags, payload)
    normalized = normalize_channel_pdu(header.to_bytes(), decompressor)
    parsed = CHANNEL_PDU_HEADER.from_bytes(normalized)
    assert parsed.data == b"abc"
    assert not int(parsed.flags) & int(CHANNEL_FLAG.CHANNEL_PACKET_COMPRESSED)
