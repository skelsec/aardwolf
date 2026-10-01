"""RDP licensing PDU parse, acquisition FSM, and connection hooks."""

import asyncio
import io
import struct
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from aardwolf.connection import RDPConnection
from aardwolf.protocol.T124.userdata.constants import TS_UD_TYPE
from aardwolf.protocol.T124.userdata.serversecuritydata import SERVER_CERTIFICATE
from aardwolf.protocol.T128.licensing import (
    KEY_EXCHANGE_ALG_RSA,
    LicenseBinaryBlob,
    LicenseBlobType,
    LicenseErrorCode,
    LicenseInformation,
    LicenseMessageType,
    LicensePDU,
    LicenseState,
    LicenseStateTransition,
    LicensingProtocolError,
    RDPLicenseManager,
    extract_license_pdu,
)


pytestmark = pytest.mark.unit


VALID_CLIENT_PDU = bytes.fromhex(
    "ff031000"
    "07000000"
    "02000000"
    "04000000"
)


class FakeServerCertificate:
    def encrypt(self, secret):
        self.secret = secret
        return b"\xaa" * 72


def make_license_request(
    server_random=b"\x11" * 32,
    certificate_blob_type=LicenseBlobType.CERTIFICATE,
    scopes=(),
):
    company_name = "Microsoft Corporation\x00".encode("utf-16-le")
    product_id = "A02\x00".encode("utf-16-le")
    body = server_random
    body += struct.pack("<I", 0x00060000)
    body += struct.pack("<I", len(company_name)) + company_name
    body += struct.pack("<I", len(product_id)) + product_id
    body += LicenseBinaryBlob(
        LicenseBlobType.KEY_EXCHANGE_ALGORITHM,
        struct.pack("<I", KEY_EXCHANGE_ALG_RSA),
    ).to_bytes()
    body += LicenseBinaryBlob(certificate_blob_type, b"").to_bytes()
    body += struct.pack("<I", len(scopes))
    for scope in scopes:
        body += scope.to_bytes()
    return LicensePDU(
        LicenseMessageType.LICENSE_REQUEST,
        0,
        3,
        body,
    )


def make_manager():
    return RDPLicenseManager(
        username="alice",
        hostname="workstation",
        server_certificate=FakeServerCertificate(),
        random_source=lambda length: bytes(range(length)),
    )


def test_parses_valid_client_error():
    security_header = bytes.fromhex("80020000")
    security_flags, pdu = extract_license_pdu(security_header + VALID_CLIENT_PDU)

    assert security_flags == 0x0280
    assert pdu.message_type == LicenseMessageType.ERROR_ALERT
    manager = RDPLicenseManager()
    complete, response = manager.process(pdu)
    assert complete is True
    assert response is None
    assert manager.state == LicenseState.COMPLETED


def test_parses_valid_client_after_outer_decryption():
    security_flags, pdu = extract_license_pdu(VALID_CLIENT_PDU)

    assert security_flags == 0
    assert pdu.message_type == LicenseMessageType.ERROR_ALERT


def test_parses_license_header_with_nonzero_flags_hi():
    security_flags, pdu = extract_license_pdu(
        bytes.fromhex("80003412") + VALID_CLIENT_PDU
    )

    assert security_flags == 0x0080
    assert pdu.message_type == LicenseMessageType.ERROR_ALERT


def test_license_header_wins_over_demand_active_byte_collision():
    license_request = LicensePDU(
        LicenseMessageType.LICENSE_REQUEST,
        0,
        3,
        b"\x00" * 120,
    ).to_bytes()
    security_flags, pdu = extract_license_pdu(
        bytes.fromhex("80001100") + license_request
    )

    assert security_flags == 0x0080
    assert pdu.message_type == LicenseMessageType.LICENSE_REQUEST


def test_non_license_data_is_preserved_for_next_phase():
    demand_active = struct.pack("<HBBH", 0x0180, 0x11, 0, 1003)
    demand_active += b"\x00" * (0x0180 - len(demand_active))
    assert extract_license_pdu(demand_active) is None
    assert extract_license_pdu(bytes.fromhex("010211000000")) is None


def test_rejects_invalid_preamble_length():
    with pytest.raises(LicensingProtocolError, match="size mismatch"):
        LicensePDU.from_bytes(bytes.fromhex("ff031100070000000200000004000000"))


def test_surfaces_real_licensing_error():
    body = struct.pack(
        "<II",
        LicenseErrorCode.ERR_NO_LICENSE_SERVER,
        LicenseStateTransition.ST_TOTAL_ABORT,
    )
    body += LicenseBinaryBlob(LicenseBlobType.ERROR, b"").to_bytes()
    pdu = LicensePDU(LicenseMessageType.ERROR_ALERT, 0, 3, body)

    with pytest.raises(LicensingProtocolError, match="ERR_NO_LICENSE_SERVER"):
        RDPLicenseManager().process(pdu)


def test_accepts_empty_any_blob_in_valid_client_status():
    body = struct.pack(
        "<II",
        LicenseErrorCode.STATUS_VALID_CLIENT,
        LicenseStateTransition.ST_NO_TRANSITION,
    )
    body += LicenseBinaryBlob(LicenseBlobType.ANY, b"").to_bytes()
    complete, response = RDPLicenseManager().process(
        LicensePDU(LicenseMessageType.ERROR_ALERT, 0, 3, body)
    )

    assert complete is True
    assert response is None


def test_no_cache_license_acquisition():
    manager = make_manager()
    complete, new_request_data = manager.process(make_license_request())

    assert complete is False
    assert manager.state == LicenseState.NEW_REQUEST_SENT
    assert manager.crypto.mac_salt_key.hex() == "03f1bcb776f4ce184a82a6a74331e828"
    assert manager.crypto.license_key.hex() == "332a39a56aa1a92deca4dfb25dafe3d8"
    new_request = LicensePDU.from_bytes(new_request_data)
    assert new_request.message_type == LicenseMessageType.NEW_LICENSE_REQUEST
    request_body = io.BytesIO(new_request.body)
    assert struct.unpack("<I", request_body.read(4))[0] == KEY_EXCHANGE_ALG_RSA
    request_body.read(4 + 32)
    encrypted_premaster = LicenseBinaryBlob.from_buffer(
        request_body,
        "encrypted premaster secret",
    )
    username = LicenseBinaryBlob.from_buffer(request_body, "username")
    hostname = LicenseBinaryBlob.from_buffer(request_body, "hostname")
    assert encrypted_premaster.blob_type == LicenseBlobType.RANDOM
    assert encrypted_premaster.data == b"\xaa" * 72
    assert username.data == b"alice\x00"
    assert hostname.data == b"workstation\x00"
    assert request_body.read() == b""

    challenge = "TEST\x00".encode("utf-16-le")
    encrypted_challenge = manager.crypto.crypt(challenge)
    challenge_body = struct.pack("<I", 0)
    challenge_body += LicenseBinaryBlob(
        LicenseBlobType.ENCRYPTED_DATA,
        encrypted_challenge,
    ).to_bytes()
    challenge_body += manager.crypto.mac(challenge)
    challenge_pdu = LicensePDU(
        LicenseMessageType.PLATFORM_CHALLENGE,
        0,
        3,
        challenge_body,
    )

    complete, response_data = manager.process(challenge_pdu)
    assert complete is False
    assert manager.state == LicenseState.CHALLENGE_RESPONSE_SENT
    response = LicensePDU.from_bytes(response_data)
    assert response.message_type == LicenseMessageType.PLATFORM_CHALLENGE_RESPONSE
    response_body = io.BytesIO(response.body)
    encrypted_response = LicenseBinaryBlob.from_buffer(
        response_body, "challenge response"
    )
    encrypted_hwid = LicenseBinaryBlob.from_buffer(response_body, "hardware ID")
    response_mac = response_body.read(16)
    assert response_body.read() == b""
    plain_response = manager.crypto.crypt(encrypted_response.data)
    plain_hwid = manager.crypto.crypt(encrypted_hwid.data)
    version, client_type, detail_level, challenge_length = struct.unpack(
        "<HHHH",
        plain_response[:8],
    )
    assert version == 0x0100
    assert client_type == 0xFF00
    assert detail_level == 0x0003
    assert plain_response[8 : 8 + challenge_length] == challenge
    assert plain_hwid == manager.crypto.hardware_id
    assert response_mac == manager.crypto.mac(plain_response + plain_hwid)

    license_data = struct.pack("<I", 0x00060000)
    for value in (b"scope", b"company", b"product", b"opaque-cal"):
        license_data += struct.pack("<I", len(value)) + value
    new_license_body = LicenseBinaryBlob(
        LicenseBlobType.ENCRYPTED_DATA,
        manager.crypto.crypt(license_data),
    ).to_bytes()
    new_license_body += manager.crypto.mac(license_data)
    new_license = LicensePDU(
        LicenseMessageType.NEW_LICENSE,
        0,
        3,
        new_license_body,
    )

    complete, response = manager.process(new_license)
    assert complete is True
    assert response is None
    assert manager.state == LicenseState.COMPLETED
    assert isinstance(manager.issued_license, LicenseInformation)
    assert manager.issued_license.license_info == b"opaque-cal"


def test_accepts_empty_any_server_certificate_blob():
    complete, response = make_manager().process(
        make_license_request(certificate_blob_type=LicenseBlobType.ANY)
    )

    assert complete is False
    assert response is not None


def test_accepts_empty_any_scope_blob():
    complete, response = make_manager().process(
        make_license_request(scopes=(LicenseBinaryBlob(LicenseBlobType.ANY, b""),))
    )

    assert complete is False
    assert response is not None


def test_error_transitions_resend_and_reset():
    manager = make_manager()
    _, original_response = manager.process(make_license_request())
    resend_body = struct.pack(
        "<II",
        LicenseErrorCode.ERR_INVALID_CLIENT,
        LicenseStateTransition.ST_RESEND_LAST_MESSAGE,
    )
    resend_body += LicenseBinaryBlob(LicenseBlobType.ERROR, b"").to_bytes()

    complete, resent_response = manager.process(
        LicensePDU(LicenseMessageType.ERROR_ALERT, 0, 3, resend_body)
    )
    assert complete is False
    assert resent_response == original_response

    reset_body = struct.pack(
        "<II",
        LicenseErrorCode.ERR_INVALID_CLIENT,
        LicenseStateTransition.ST_RESET_PHASE_TO_START,
    )
    reset_body += LicenseBinaryBlob(LicenseBlobType.ERROR, b"").to_bytes()
    complete, response = manager.process(
        LicensePDU(LicenseMessageType.ERROR_ALERT, 0, 3, reset_body)
    )
    assert complete is False
    assert response is None
    assert manager.state == LicenseState.INITIAL
    assert manager.last_response is None


def test_rejects_tampered_platform_challenge():
    manager = make_manager()
    manager.process(make_license_request())
    challenge = b"challenge"
    body = struct.pack("<I", 0)
    body += LicenseBinaryBlob(
        LicenseBlobType.ENCRYPTED_DATA,
        manager.crypto.crypt(challenge),
    ).to_bytes()
    body += b"\x00" * 16

    with pytest.raises(LicensingProtocolError, match="MAC mismatch"):
        manager.process(LicensePDU(LicenseMessageType.PLATFORM_CHALLENGE, 0, 3, body))


def test_license_pdu_round_trip():
    original = LicensePDU(LicenseMessageType.ERROR_ALERT, 0, 3, VALID_CLIENT_PDU[8:])
    parsed = LicensePDU.from_bytes(original.to_bytes())
    assert parsed.message_type == original.message_type
    assert parsed.to_bytes() == original.to_bytes()


def make_connection():
    connection = object.__new__(RDPConnection)
    connection.credentials = SimpleNamespace(username="alice")
    connection.target = SimpleNamespace(timeout=1)
    connection._RDPConnection__server_connect_pdu = {
        TS_UD_TYPE.SC_SECURITY: SimpleNamespace(serverCertificate=None)
    }
    connection._RDPConnection__joined_channels = {
        "MCS": SimpleNamespace(out_queue=asyncio.Queue(), channel_id=1003)
    }
    connection._RDPConnection__pending_mcs_data = None
    return connection


@pytest.mark.asyncio
async def test_connection_accepts_valid_client_status():
    connection = make_connection()
    await connection._RDPConnection__joined_channels["MCS"].out_queue.put(
        (bytes.fromhex("80020000") + VALID_CLIENT_PDU, None)
    )

    result, error = await connection._RDPConnection__handle_license()

    assert result is True
    assert error is None
    assert connection._RDPConnection__pending_mcs_data is None


@pytest.mark.asyncio
async def test_connection_preserves_direct_demand_active():
    connection = make_connection()
    demand_active = struct.pack("<HBBH", 0x0180, 0x11, 0, 1003)
    demand_active += b"\x00" * (0x0180 - len(demand_active))
    await connection._RDPConnection__joined_channels["MCS"].out_queue.put(
        (demand_active, None)
    )

    result, error = await connection._RDPConnection__handle_license()

    assert result is True
    assert error is None
    assert connection._RDPConnection__pending_mcs_data == (demand_active, None)


@pytest.mark.asyncio
async def test_connection_wraps_outbound_licensing_data():
    connection = make_connection()
    connection._initiator = 1001
    connection._t125_per_codec = Mock()
    connection._t125_per_codec.encode.return_value = b"wrapped"
    connection._x224net = SimpleNamespace(write=AsyncMock())

    await connection._RDPConnection__send_license_data(b"license-pdu")

    message_type, (mcs_type, wrapper) = connection._t125_per_codec.encode.call_args.args
    assert message_type == "DomainMCSPDU"
    assert mcs_type == "sendDataRequest"
    assert wrapper["initiator"] == 1001
    assert wrapper["channelId"] == 1003
    assert wrapper["userData"] == bytes.fromhex("80000000") + b"license-pdu"
    connection._x224net.write.assert_awaited_once_with(b"wrapped")


@pytest.mark.asyncio
async def test_failed_connect_cleanup_cancels_tasks_and_closes_transport():
    connection = make_connection()
    reader_task = asyncio.create_task(asyncio.sleep(10))
    channel = AsyncMock()
    connection._RDPConnection__joined_channels = {"MCS": channel}
    connection._RDPConnection__external_reader_task = None
    connection._RDPConnection__x224_reader_task = reader_task
    connection._RDPConnection__channel_task = {}
    connection._RDPConnection__connection = SimpleNamespace(close=AsyncMock())
    connection._RDPConnection__terminate_called = False

    await connection._RDPConnection__cleanup_failed_connect()

    channel.disconnect.assert_awaited_once()
    assert reader_task.cancelled()
    connection._RDPConnection__connection.close.assert_awaited_once()
    assert connection._RDPConnection__terminate_called is True


@pytest.mark.asyncio
async def test_connect_cancellation_runs_cleanup():
    connection = object.__new__(RDPConnection)
    connection.target = SimpleNamespace()
    connection.disconnected_evt = asyncio.Event()
    cleanup = AsyncMock()
    connection._RDPConnection__cleanup_failed_connect = cleanup
    block_connect = asyncio.Event()

    with patch("aardwolf.connection.UniClient") as client_type:
        client_type.return_value.connect = AsyncMock(side_effect=block_connect.wait)
        connect_task = asyncio.create_task(connection.connect())
        await asyncio.sleep(0)
        connect_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await connect_task

    cleanup.assert_awaited_once()
    assert connection.disconnected_evt.is_set()


def test_x509_chain_uses_terminal_server_certificate():
    with patch(
        "aardwolf.protocol.T124.userdata.serversecuritydata.Certificate.load"
    ) as certificate_load:
        certificate = Mock()
        certificate.public_key.native = {
            "public_key": {
                "public_exponent": 1,
                "modulus": (1 << 1024) - 109,
            }
        }
        certificate_load.return_value = certificate
        first_cert = b"first"
        terminal_cert = b"terminal"
        chain = struct.pack("<II", 0x80000002, 2)
        chain += struct.pack("<I", len(first_cert)) + first_cert
        chain += struct.pack("<I", len(terminal_cert)) + terminal_cert
        chain += b"\x00" * 16

        server_certificate = SERVER_CERTIFICATE.from_bytes(chain)

        certificate_load.assert_called_once_with(terminal_cert)
        assert server_certificate.t
        assert server_certificate.certData == terminal_cert
        assert len(server_certificate.encrypt(b"secret")) == 136


def test_x509_chain_requires_two_certificates_and_padding():
    with pytest.raises(ValueError, match="certificate count"):
        SERVER_CERTIFICATE.from_bytes(struct.pack("<II", 2, 1))

    certificate = b"certificate"
    chain = struct.pack("<II", 2, 2)
    chain += struct.pack("<I", len(certificate)) + certificate
    chain += struct.pack("<I", len(certificate)) + certificate
    with pytest.raises(ValueError, match="padding"):
        SERVER_CERTIFICATE.from_bytes(chain)
