"""T.128 share headers, control/sync/font bodies, and confirm-active wrapping."""

import pytest

from aardwolf.protocol.T128.clientconfirmactivepdu import TS_CONFIRM_ACTIVE_PDU
from aardwolf.protocol.T128.controlpdu import CTRLACTION, TS_CONTROL_PDU
from aardwolf.protocol.T128.fontlistpdu import TS_FONT_LIST_PDU
from aardwolf.protocol.T128.share import (
    PDUTYPE,
    PDUTYPE2,
    STREAM_TYPE,
    CompType,
    TS_SHARECONTROLHEADER,
    TS_SHAREDATAHEADER,
)
from aardwolf.protocol.T128.synchronizepdu import TS_SYNCHRONIZE_PDU
from aardwolf.protocol.pdu.capabilities import TS_CAPS_SET
from aardwolf.protocol.pdu.capabilities.share import TS_SHARE_CAPABILITYSET


pytestmark = pytest.mark.unit


def make_share_control(pdu_type=PDUTYPE.DATAPDU, total_length=18, source=1003):
    header = TS_SHARECONTROLHEADER()
    header.totalLength = total_length
    header.pduType = pdu_type
    header.pduVersion = 1
    header.pduSource = source
    return header


def make_share_data(pdu_type2=PDUTYPE2.SYNCHRONIZE, total_length=22):
    header = TS_SHAREDATAHEADER()
    header.shareControlHeader = make_share_control(total_length=total_length)
    header.shareID = 0x000103EA
    header.streamID = STREAM_TYPE.MED
    header.uncompressedLength = total_length - 6
    header.pduType2 = pdu_type2
    header.compressedType = CompType(0)
    header.compressedLength = 0
    return header


def test_share_control_header_round_trip():
    header = make_share_control(PDUTYPE.DEMANDACTIVEPDU, total_length=6)
    parsed = TS_SHARECONTROLHEADER.from_bytes(header.to_bytes())
    assert parsed.pduType == PDUTYPE.DEMANDACTIVEPDU
    assert parsed.pduSource == 1003
    assert parsed.to_bytes() == header.to_bytes()


def test_share_data_header_round_trip():
    header = make_share_data()
    parsed = TS_SHAREDATAHEADER.from_bytes(header.to_bytes())
    assert parsed.pduType2 == PDUTYPE2.SYNCHRONIZE
    assert parsed.shareID == 0x000103EA
    assert parsed.streamID == STREAM_TYPE.MED
    assert parsed.to_bytes() == header.to_bytes()


def test_synchronize_body_round_trip_with_header():
    pdu = TS_SYNCHRONIZE_PDU()
    pdu.targetUser = 1002
    body = pdu.to_bytes()
    header = make_share_data(PDUTYPE2.SYNCHRONIZE, total_length=18 + len(body))
    parsed = TS_SYNCHRONIZE_PDU.from_bytes(header.to_bytes() + body)
    assert parsed.messageType == 1
    assert parsed.targetUser == 1002


def test_control_cooperate_body_round_trip_with_header():
    pdu = TS_CONTROL_PDU()
    pdu.action = CTRLACTION.COOPERATE
    pdu.grantId = 0
    pdu.controlId = 0
    body = pdu.to_bytes()
    header = make_share_data(PDUTYPE2.CONTROL, total_length=18 + len(body))
    parsed = TS_CONTROL_PDU.from_bytes(header.to_bytes() + body)
    assert parsed.action == CTRLACTION.COOPERATE


def test_font_list_body_round_trip_with_header():
    pdu = TS_FONT_LIST_PDU()
    body = pdu.to_bytes()
    header = make_share_data(PDUTYPE2.FONTLIST, total_length=18 + len(body))
    parsed = TS_FONT_LIST_PDU.from_bytes(header.to_bytes() + body)
    assert parsed.listFlags == 0x0003
    assert parsed.entrySize == 50


def test_confirm_active_body_includes_capability_sets():
    capability = TS_CAPS_SET.from_capability(TS_SHARE_CAPABILITYSET())
    pdu = TS_CONFIRM_ACTIVE_PDU()
    pdu.shareID = 0x000103EA
    pdu.originatorID = 1002
    pdu.capabilitySets = [capability]
    body = pdu.to_bytes()
    header = make_share_control(PDUTYPE.CONFIRMACTIVEPDU, total_length=6 + len(body))
    parsed = TS_CONFIRM_ACTIVE_PDU.from_bytes(header.to_bytes() + body)
    assert parsed.shareID == 0x000103EA
    assert parsed.originatorID == 1002
    assert parsed.sourceDescriptor == b"MSTSC\x00"
    assert len(parsed.capabilitySets) == 1
