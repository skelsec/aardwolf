"""RDPECLIP and RDPEDYC protocol PDU round-trips."""

import pytest

from aardwolf.extensions.RDPECLIP.protocol import CB_FLAG, CB_TYPE, CLIPRDR_HEADER
from aardwolf.extensions.RDPECLIP.protocol.formatdatarequest import CLIPRDR_FORMAT_DATA_REQUEST
from aardwolf.extensions.RDPECLIP.protocol.formatlist import (
    CLIPBRD_FORMAT,
    CLIPRDR_FORMAT_LIST,
    CLIPRDR_SHORT_FORMAT_NAME,
)
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD, DYNVC_MESSAGE, dynvc_header_to_bytes
from aardwolf.extensions.RDPEDYC.protocol.close import DYNVC_CLOSE
from aardwolf.extensions.RDPEDYC.protocol.create import DYNVC_CREATE_REQ, DYNVC_CREATE_RSP


pytestmark = pytest.mark.unit


def test_cliprdr_header_round_trip():
    header = CLIPRDR_HEADER()
    header.msgType = CB_TYPE.CB_MONITOR_READY
    header.msgFlags = CB_FLAG(0)
    header.dataLen = 0
    parsed = CLIPRDR_HEADER.from_bytes(header.to_bytes())
    assert parsed.msgType == CB_TYPE.CB_MONITOR_READY
    assert parsed.dataLen == 0
    assert parsed.to_bytes() == header.to_bytes()


def test_cliprdr_serialize_monitor_ready():
    wire = CLIPRDR_HEADER.serialize_packet(CB_TYPE.CB_MONITOR_READY, CB_FLAG(0), None)
    header, body = CLIPRDR_HEADER.parse_packet_bytes(wire)
    assert header.msgType == CB_TYPE.CB_MONITOR_READY
    assert body is None


def test_cliprdr_format_list_short_name_round_trip():
    entry = CLIPRDR_SHORT_FORMAT_NAME()
    entry.formatId = CLIPBRD_FORMAT.CF_UNICODETEXT
    entry.formatName = ""
    listing = CLIPRDR_FORMAT_LIST()
    listing.templist = [entry]
    parsed = CLIPRDR_FORMAT_LIST.from_bytes(listing.to_bytes())
    assert parsed.templist[0].formatId == CLIPBRD_FORMAT.CF_UNICODETEXT
    assert parsed.to_bytes() == listing.to_bytes()


def test_cliprdr_format_data_request_round_trip():
    request = CLIPRDR_FORMAT_DATA_REQUEST()
    request.requestedFormatId = CLIPBRD_FORMAT.CF_UNICODETEXT
    parsed = CLIPRDR_FORMAT_DATA_REQUEST.from_bytes(request.to_bytes())
    assert parsed.requestedFormatId == CLIPBRD_FORMAT.CF_UNICODETEXT
    wire = CLIPRDR_HEADER.serialize_packet(
        CB_TYPE.CB_FORMAT_DATA_REQUEST,
        CB_FLAG(0),
        request,
    )
    header, body = CLIPRDR_HEADER.parse_packet_bytes(wire)
    assert header.msgType == CB_TYPE.CB_FORMAT_DATA_REQUEST
    assert body.requestedFormatId == CLIPBRD_FORMAT.CF_UNICODETEXT


def test_dynvc_create_request_round_trip():
    request = DYNVC_CREATE_REQ()
    request.cbid = 2
    request.pri = 0
    request.cmd = DYNVC_CMD.CREATE_RSP
    request.ChannelId = 1
    request.ChannelName = "ECHO"
    wire = request.to_bytes()
    parsed = DYNVC_CREATE_REQ.from_bytes(wire)
    assert parsed.ChannelId == 1
    assert parsed.ChannelName.rstrip("\x00") == "ECHO"
    dispatched = DYNVC_MESSAGE.from_bytes(wire)
    assert isinstance(dispatched, DYNVC_CREATE_REQ)


def test_dynvc_create_response_round_trip():
    response = DYNVC_CREATE_RSP()
    response.cbid = 2
    response.ChannelId = 1
    response.CreationStatus = 0
    parsed = DYNVC_CREATE_RSP.from_bytes(response.to_bytes())
    assert parsed.ChannelId == 1
    assert parsed.CreationStatus == 0


def test_dynvc_close_round_trip():
    close = DYNVC_CLOSE()
    close.cbid = 2
    close.ChannelId = 7
    parsed = DYNVC_CLOSE.from_bytes(close.to_bytes())
    assert parsed.ChannelId == 7
    assert parsed.cmd == DYNVC_CMD.CLOSE
    assert parsed.to_bytes() == close.to_bytes()


def test_dynvc_header_codec():
    encoded = dynvc_header_to_bytes(2, 0, DYNVC_CMD.CLOSE, cbid_mod=True)
    assert encoded == bytes([(DYNVC_CMD.CLOSE.value << 4) ^ 1])
