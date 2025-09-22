"""
@Descripttion: SPHINCS+ WOTS+ 基元测试（Stage-2）
@version: V0.3
@Author: GoldenModel-Team
@Date: 2025-03-20 12:00
"""

from __future__ import annotations

import pytest

from sphincs_params import get_params
from sphincs_utils import derive_wots_address
from sphincs_wots import wots_gen_pk, wots_pk_from_sig, wots_sign, wots_verify


@pytest.fixture(name="wots_context")
def fixture_wots_context():
    params = get_params()
    sk_seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    pub_seed = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
    base_address = derive_wots_address(0, 0, 0, 0, 0)
    message = bytes.fromhex("112233445566778899aabbccddeeff00")
    return params, sk_seed, pub_seed, base_address, message


def test_wots_sign_verify_roundtrip(wots_context):
    params, sk_seed, pub_seed, base_address, message = wots_context
    signature = wots_sign(params, message, sk_seed, pub_seed, base_address)
    assert len(signature) == int(params["len"]) * int(params["n"])
    pk = wots_gen_pk(params, sk_seed, pub_seed, base_address)
    derived_pk = wots_pk_from_sig(params, signature, message, pub_seed, base_address)
    assert derived_pk == pk
    assert wots_verify(params, message, signature, pub_seed, base_address, pk)


def test_wots_verify_fail_on_message_mismatch(wots_context):
    params, sk_seed, pub_seed, base_address, message = wots_context
    signature = wots_sign(params, message, sk_seed, pub_seed, base_address)
    pk = wots_gen_pk(params, sk_seed, pub_seed, base_address)
    tampered_message = bytes([message[0] ^ 0x01]) + message[1:]
    assert not wots_verify(params, tampered_message, signature, pub_seed, base_address, pk)


def test_wots_pk_length(wots_context):
    params, sk_seed, pub_seed, base_address, _ = wots_context
    pk = wots_gen_pk(params, sk_seed, pub_seed, base_address)
    assert len(pk) == int(params["len"]) * int(params["n"])
