"""X.224 connection request/confirm and data TPDU round-trips."""

import pytest

from aardwolf.network.x224 import _format_mstshash_cookie
from aardwolf.protocol.x224 import X224Packet
from aardwolf.protocol.x224.client.connectionrequest import ConnectionRequest, RDP_NEG_REQ
from aardwolf.protocol.x224.constants import FAIL_CODE, NEG_FLAGS, RESP_FLAGS, SUPP_PROTOCOLS, TPDU_TYPE
from aardwolf.protocol.x224.data import Data
from aardwolf.protocol.x224.server.connectionconfirm import (
    ConnectionConfirm,
    RDP_NEG_FAILURE,
    RDP_NEG_RSP,
)


pytestmark = pytest.mark.unit


def test_mstshash_cookie_uses_mstsc_compatible_username():
    assert _format_mstshash_cookie("longusername") == b"Cookie: mstshash=longusern\r\n"


def test_mstshash_cookie_is_omitted_without_username():
    assert _format_mstshash_cookie(None) is None
    assert _format_mstshash_cookie("") is None


def test_mstshash_cookie_rejects_line_breaks():
    with pytest.raises(ValueError):
        _format_mstshash_cookie("user\r\nCookie: injected")


def test_rdp_neg_req_round_trip():
    request = RDP_NEG_REQ()
    request.flags = NEG_FLAGS(0)
    request.requestedProtocols = SUPP_PROTOCOLS.SSL | SUPP_PROTOCOLS.HYBRID
    wire = request.to_bytes()
    parsed = RDP_NEG_REQ.from_bytes(wire)
    assert parsed.requestedProtocols == request.requestedProtocols
    assert parsed.to_bytes() == wire


def test_connection_request_with_cookie_and_negotiation():
    negotiation = RDP_NEG_REQ()
    negotiation.flags = NEG_FLAGS(0)
    negotiation.requestedProtocols = SUPP_PROTOCOLS.SSL
    request = ConnectionRequest()
    request.SRC_REF = 0x1234
    request.cookie = b"Cookie: mstshash=user\r\n"
    request.rdpNegReq = negotiation
    wire = request.to_bytes()

    parsed = ConnectionRequest.from_bytes(wire)
    assert parsed.CR == TPDU_TYPE.CONNECTION_REQUEST
    assert parsed.SRC_REF == 0x1234
    assert parsed.cookie == b"Cookie: mstshash=user\r\n"
    assert parsed.rdpNegReq.requestedProtocols == SUPP_PROTOCOLS.SSL
    assert parsed.to_bytes() == wire


def test_x224_packet_dispatches_connection_request():
    request = ConnectionRequest()
    request.SRC_REF = 1
    parsed = X224Packet.from_bytes(request.to_bytes())
    assert isinstance(parsed, ConnectionRequest)
    assert parsed.SRC_REF == 1


def test_rdp_neg_rsp_round_trip():
    response = RDP_NEG_RSP()
    response.flags = RESP_FLAGS.EXTENDED_CLIENT_DATA_SUPPORTED
    response.selectedProtocol = SUPP_PROTOCOLS.SSL
    parsed = RDP_NEG_RSP.from_bytes(response.to_bytes())
    assert parsed.selectedProtocol == SUPP_PROTOCOLS.SSL
    assert parsed.flags == RESP_FLAGS.EXTENDED_CLIENT_DATA_SUPPORTED
    assert parsed.to_bytes() == response.to_bytes()


def test_rdp_neg_failure_round_trip():
    failure = RDP_NEG_FAILURE()
    failure.failureCode = FAIL_CODE.HYBRID_REQUIRED_BY_SERVER
    parsed = RDP_NEG_FAILURE.from_bytes(failure.to_bytes())
    assert parsed.failureCode == FAIL_CODE.HYBRID_REQUIRED_BY_SERVER
    assert parsed.to_bytes() == failure.to_bytes()


def test_connection_confirm_with_selected_protocol():
    confirm = ConnectionConfirm()
    confirm.SRC_REF = 0x0001
    confirm.DST_REF = 0x1234
    confirm.rdpNegData = RDP_NEG_RSP()
    confirm.rdpNegData.flags = RESP_FLAGS(0)
    confirm.rdpNegData.selectedProtocol = SUPP_PROTOCOLS.RDP
    wire = confirm.to_bytes()
    parsed = ConnectionConfirm.from_bytes(wire)
    assert parsed.CR == TPDU_TYPE.CONNECTION_CONFIRM
    assert parsed.rdpNegData.selectedProtocol == SUPP_PROTOCOLS.RDP
    assert parsed.to_bytes() == wire


def test_connection_confirm_failure_dispatch():
    confirm = ConnectionConfirm()
    confirm.SRC_REF = 1
    confirm.rdpNegData = RDP_NEG_FAILURE()
    confirm.rdpNegData.failureCode = FAIL_CODE.SSL_REQUIRED_BY_SERVER
    parsed = ConnectionConfirm.from_bytes(confirm.to_bytes())
    assert isinstance(parsed.rdpNegData, RDP_NEG_FAILURE)
    assert parsed.rdpNegData.failureCode == FAIL_CODE.SSL_REQUIRED_BY_SERVER


def test_x224_data_parse_and_dispatch():
    data = Data()
    data.data = b"payload"
    wire = data.to_bytes()
    parsed = Data.from_bytes(wire)
    assert parsed.DT == TPDU_TYPE.DATA
    assert parsed.data == b"payload"
    dispatched = X224Packet.from_bytes(wire)
    assert isinstance(dispatched, Data)


@pytest.mark.xfail(
    strict=True,
    reason="KF-0001: Data.from_bytes stores TPDU_NR as int so to_bytes cannot round-trip",
)
def test_x224_data_round_trip():
    data = Data()
    data.data = b"payload"
    wire = data.to_bytes()
    parsed = Data.from_bytes(wire)
    assert parsed.to_bytes() == wire
