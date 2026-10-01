"""Optional Hypothesis properties for MPPC literal streams."""

import pytest

from aardwolf.protocol.compression import (
    BulkCompressionFlags,
    BulkCompressionType,
    BulkDecompressor,
)
from tests.unit.compression.test_native_vs_reference import (
    compression_flags,
    make_mppc_vector,
)


pytestmark = pytest.mark.unit

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings
from hypothesis import strategies as st


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=1, max_size=40))
def test_mppc_literal_stream_round_trip(payload):
    decompressor = BulkDecompressor(BulkCompressionType.RDP4_8K)
    flags = compression_flags(
        BulkCompressionType.RDP4_8K,
        BulkCompressionFlags.COMPRESSED,
        BulkCompressionFlags.AT_FRONT,
        BulkCompressionFlags.FLUSHED,
    )
    encoded = make_mppc_vector(literals=payload)
    assert decompressor.decompress(encoded, flags) == payload
