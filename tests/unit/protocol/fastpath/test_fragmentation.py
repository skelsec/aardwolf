"""Fast-path PDU parse, fragment reassembly, and multifragment capability."""

import pytest

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.protocol.compression import BulkCompressionType, BulkDecompressor
from aardwolf.protocol.fastpath import (
    FASTPATH_FRAGMENT,
    FASTPATH_OUTPUT_COMPRESSION,
    FASTPATH_UPDATETYPE,
    TS_FP_UPDATE,
    TS_FP_UPDATE_PDU,
)
from aardwolf.protocol.fastpath.reassembly import (
    FastPathFragmentReassembler,
    FastPathProtocolError,
)
from aardwolf.protocol.pdu.capabilities import CAPSTYPE, TS_CAPS_SET
from aardwolf.protocol.pdu.capabilities.multifragmentupdate import (
    TS_MULTIFRAGMENTUPDATE_CAPABILITYSET,
)


pytestmark = pytest.mark.unit


def make_update(
    data,
    fragmentation=FASTPATH_FRAGMENT.SINGLE,
    update_code=FASTPATH_UPDATETYPE.SYNCHRONIZE,
):
    update = TS_FP_UPDATE()
    update.updateCode = update_code
    update.fragmentation = fragmentation
    update.compression = FASTPATH_OUTPUT_COMPRESSION.NONE
    update.updateData = data
    update.size = len(data)
    return update


def make_pdu(*updates):
    payload = b"".join(update.to_bytes() for update in updates)
    length = 2 + len(payload)
    if length >= 0x80:
        length += 1
        header = b"\x00" + (length | 0x8000).to_bytes(2, byteorder="big")
    else:
        header = b"\x00" + length.to_bytes(1, byteorder="big")
    return header + payload


def test_pdu_parses_all_updates():
    first = make_update(b"one")
    second = make_update(b"two", update_code=FASTPATH_UPDATETYPE.PTR_NULL)

    pdu = TS_FP_UPDATE_PDU.from_bytes(make_pdu(first, second))

    assert len(pdu.fpOutputUpdates) == 2
    assert pdu.fpOutputUpdates[0].updateData == b"one"
    assert pdu.fpOutputUpdates[1].updateCode == FASTPATH_UPDATETYPE.PTR_NULL
    assert pdu.fpOutputUpdates[0].update is None


def test_pdu_parses_two_byte_length():
    update = make_update(b"x" * 128)

    pdu = TS_FP_UPDATE_PDU.from_bytes(make_pdu(update))

    assert pdu.length2 is not None
    assert pdu.fpOutputUpdates[0].updateData == b"x" * 128


def test_encrypted_pdu_preserves_raw_output_data():
    payload = make_update(b"ciphertext").to_bytes()
    length = 2 + 8 + len(payload)
    pdu_data = b"\x80" + length.to_bytes(1, byteorder="big") + (b"\xaa" * 8) + payload

    pdu = TS_FP_UPDATE_PDU.from_bytes(pdu_data)

    assert pdu.dataSignature == b"\xaa" * 8
    assert pdu.fpOutputData == payload
    assert pdu.fpOutputUpdates == []


def test_pdu_rejects_truncated_update():
    update = bytes([FASTPATH_UPDATETYPE.SYNCHRONIZE.value]) + b"\x04\x00" + b"abc"
    pdu = b"\x00\x08" + update

    with pytest.raises(ValueError, match="Truncated fast-path update data"):
        TS_FP_UPDATE_PDU.from_bytes(pdu)


def test_update_rejects_reserved_compression_value():
    update = bytes([0x40 | FASTPATH_UPDATETYPE.SYNCHRONIZE.value]) + b"\x00\x00"

    with pytest.raises(ValueError, match="Invalid fast-path output compression"):
        TS_FP_UPDATE.from_bytes(update)


def test_update_round_trip():
    original = make_update(b"payload", update_code=FASTPATH_UPDATETYPE.PALETTE)
    parsed = TS_FP_UPDATE.from_bytes(original.to_bytes())
    assert parsed.updateCode == FASTPATH_UPDATETYPE.PALETTE
    assert parsed.updateData == b"payload"
    assert parsed.to_bytes() == original.to_bytes()


def test_reassembles_fragments_across_pdus():
    bitmap_data = b"\x01\x00\x00\x00"
    first_pdu = TS_FP_UPDATE_PDU.from_bytes(
        make_pdu(
            make_update(
                bitmap_data[:1], FASTPATH_FRAGMENT.FIRST, FASTPATH_UPDATETYPE.BITMAP
            ),
            make_update(
                bitmap_data[1:2], FASTPATH_FRAGMENT.NEXT, FASTPATH_UPDATETYPE.BITMAP
            ),
        )
    )
    last_pdu = TS_FP_UPDATE_PDU.from_bytes(
        make_pdu(
            make_update(
                bitmap_data[2:], FASTPATH_FRAGMENT.LAST, FASTPATH_UPDATETYPE.BITMAP
            ),
        )
    )
    reassembler = FastPathFragmentReassembler(64)

    completed = []
    for pdu in (first_pdu, last_pdu):
        for update in pdu.fpOutputUpdates:
            result = reassembler.feed(update)
            if result is not None:
                completed.append(result)

    assert len(completed) == 1
    assert completed[0].fragmentation == FASTPATH_FRAGMENT.SINGLE
    assert completed[0].updateData == bitmap_data
    completed[0].parse_update_data()
    assert completed[0].update.numberRectangles == 0
    assert reassembler.has_pending_update is False


def test_rejects_continuation_without_first():
    reassembler = FastPathFragmentReassembler(64)

    with pytest.raises(FastPathProtocolError, match="without a FIRST"):
        reassembler.feed(make_update(b"data", FASTPATH_FRAGMENT.NEXT))


def test_rejects_changed_update_type_and_resets():
    reassembler = FastPathFragmentReassembler(64)
    reassembler.feed(
        make_update(b"a", FASTPATH_FRAGMENT.FIRST, FASTPATH_UPDATETYPE.BITMAP)
    )

    with pytest.raises(FastPathProtocolError, match="update type changed"):
        reassembler.feed(
            make_update(b"b", FASTPATH_FRAGMENT.LAST, FASTPATH_UPDATETYPE.PALETTE)
        )
    assert reassembler.has_pending_update is False


def test_enforces_negotiated_size_limit():
    reassembler = FastPathFragmentReassembler(3)
    reassembler.feed(make_update(b"ab", FASTPATH_FRAGMENT.FIRST))

    with pytest.raises(FastPathProtocolError, match="exceeds the negotiated"):
        reassembler.feed(make_update(b"cd", FASTPATH_FRAGMENT.LAST))
    assert reassembler.has_pending_update is False


def test_decompresses_fragments_before_reassembly():
    compressed_bitmap_data = b"\x01\x00\x00\x00"
    first = make_update(
        compressed_bitmap_data[:2],
        FASTPATH_FRAGMENT.FIRST,
        FASTPATH_UPDATETYPE.BITMAP,
    )
    last = make_update(
        compressed_bitmap_data[2:],
        FASTPATH_FRAGMENT.LAST,
        FASTPATH_UPDATETYPE.BITMAP,
    )
    first.compression = FASTPATH_OUTPUT_COMPRESSION.USED
    first.compressionFlags = 0x60
    last.compression = FASTPATH_OUTPUT_COMPRESSION.USED
    last.compressionFlags = 0x20
    reassembler = FastPathFragmentReassembler(64)
    decompressor = BulkDecompressor(BulkCompressionType.RDP4_8K)

    first.updateData = decompressor.decompress(
        first.updateData,
        first.compressionFlags,
    )
    first.compression = FASTPATH_OUTPUT_COMPRESSION.NONE
    first.compressionFlags = 0
    assert reassembler.feed(first) is None
    last.updateData = decompressor.decompress(
        last.updateData,
        last.compressionFlags,
    )
    last.compression = FASTPATH_OUTPUT_COMPRESSION.NONE
    last.compressionFlags = 0
    completed = reassembler.feed(last)
    assert completed.updateData == compressed_bitmap_data
    completed.parse_update_data()
    assert completed.update.numberRectangles == 0


def test_default_limit_round_trips_through_capability():
    settings = RDPIOSettings()
    capability = TS_MULTIFRAGMENTUPDATE_CAPABILITYSET()
    capability.MaxRequestSize = settings.fastpath_max_request_size

    wrapped = TS_CAPS_SET.from_capability(capability)
    parsed = TS_CAPS_SET.from_bytes(wrapped.to_bytes())

    assert parsed.capabilitySetType == CAPSTYPE.MULTIFRAGMENTUPDATE
    assert parsed.capability.MaxRequestSize == 608299
