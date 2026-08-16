"""RDPCryptoLayer encrypt/decrypt and MAC with a fixed client random."""

import pytest

from aardwolf.commons.cryptolayer import RDPCryptoLayer


pytestmark = pytest.mark.unit


def make_layer(monkeypatch, keysize=128):
    monkeypatch.setattr("aardwolf.commons.cryptolayer.os.urandom", lambda n: b"\x11" * n)
    return RDPCryptoLayer(b"\x22" * 32, keysize=keysize)


def test_client_encrypt_matches_server_decrypt(monkeypatch):
    client = make_layer(monkeypatch)
    server = make_layer(monkeypatch)
    plaintext = b"slow-path-payload"
    ciphertext = client.client_enc(plaintext)
    assert ciphertext != plaintext
    assert server.server_dec(ciphertext) == plaintext


def test_server_encrypt_matches_client_decrypt(monkeypatch):
    client = make_layer(monkeypatch)
    server = make_layer(monkeypatch)
    plaintext = b"fast-path-payload"
    ciphertext = server.server_enc(plaintext)
    assert client.client_dec(ciphertext) == plaintext


def test_mac_is_eight_bytes_and_stable(monkeypatch):
    layer = make_layer(monkeypatch)
    mac = layer.calc_mac(b"abcd")
    assert len(mac) == 8
    assert mac == layer.calc_mac(b"abcd")
    assert mac != layer.calc_mac(b"abce")


def test_key_update_after_4096_packets(monkeypatch):
    layer = make_layer(monkeypatch)
    first_key = layer.CurrentClientEncryptKey128
    layer.PacketCount = 4096
    layer.client_enc(b"x")
    assert layer.CurrentClientEncryptKey128 != first_key


@pytest.mark.parametrize("keysize", [40, 56, 128])
def test_keysize_selects_mac_material(monkeypatch, keysize):
    layer = make_layer(monkeypatch, keysize=keysize)
    assert layer.keysize == keysize
    assert layer.current_mac is not None
    assert layer.client_crypto_enc is not None
