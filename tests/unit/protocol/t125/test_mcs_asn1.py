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


def test_connection_codecs_are_built_once_and_shared(monkeypatch):
    from aardwolf import connection

    parsed = []
    original_parse = asn1tools.parse_string

    def counting_parse(*args, **kwargs):
        parsed.append(args[0])
        return original_parse(*args, **kwargs)

    monkeypatch.setattr(asn1tools, "parse_string", counting_parse)
    monkeypatch.setattr(asn1tools.compiler, "parse_string", counting_parse)
    monkeypatch.setattr(connection, "_asn1_codecs", None)

    first = connection.get_asn1_codecs()
    second = connection.get_asn1_codecs()

    assert second is first
    # MCS is parsed once for both the BER and PER codecs, GCC once
    assert len(parsed) == 2

    _, per_codec, _ = first
    pdu = ("erectDomainRequest", {"subHeight": 0, "subInterval": 0})
    assert per_codec.decode("DomainMCSPDU", per_codec.encode("DomainMCSPDU", pdu)) == pdu
