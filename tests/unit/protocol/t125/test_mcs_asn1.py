"""Light ASN.1 MCS codec smoke using the in-tree specification string."""

import pytest

import asn1tools

from aardwolf.protocol.T125.MCSPDU_ver_2 import MCSPDU_ver_2


pytestmark = pytest.mark.unit


def test_mcs_erect_domain_request_round_trip():
    codec = asn1tools.compile_string(MCSPDU_ver_2, "per")
    encoded = codec.encode(
        "DomainMCSPDU",
        ("erectDomainRequest", {"subHeight": 0, "subInterval": 0}),
    )
    name, payload = codec.decode("DomainMCSPDU", encoded)
    assert name == "erectDomainRequest"
    assert payload["subHeight"] == 0
    assert payload["subInterval"] == 0
