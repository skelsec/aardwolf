"""RDPCryptoLayer encrypt/decrypt and MAC with a fixed client random."""

from hashlib import md5, sha1

import pytest
from arc4 import ARC4 as RC4

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


@pytest.mark.parametrize("keysize, salt", [(40, b"\xD1\x26\x9E"), (56, b"\xD1")])
def test_short_key_update_follows_ms_rdpbcgr_5_3_7_1(monkeypatch, keysize, salt):
    layer = make_layer(monkeypatch, keysize=keysize)
    initial = getattr(layer, "InitialClientEncryptKey%d" % keysize)[:8]
    current = getattr(layer, "CurrentClientEncryptKey%d" % keysize)[:8]
    sha_component = sha1(initial + b"\x36" * 40 + current).digest()
    temp_key64 = md5(initial + b"\x5C" * 48 + sha_component).digest()[:8]
    pre_salt_key = RC4(temp_key64).encrypt(temp_key64)
    expected = salt + pre_salt_key[len(salt):]

    layer.PacketCount = 4096
    ciphertext = layer.client_enc(b"payload")

    new_key = getattr(layer, "CurrentClientEncryptKey%d" % keysize)
    assert new_key == expected
    assert ciphertext == RC4(expected).encrypt(b"payload")


@pytest.mark.parametrize("keysize", [40, 56, 128])
def test_keysize_selects_mac_material(monkeypatch, keysize):
    layer = make_layer(monkeypatch, keysize=keysize)
    assert layer.keysize == keysize
    assert layer.current_mac is not None
    assert layer.client_crypto_enc is not None
