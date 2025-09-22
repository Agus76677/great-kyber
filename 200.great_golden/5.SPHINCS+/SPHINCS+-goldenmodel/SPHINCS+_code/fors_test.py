"""
@Descripttion: SPHINCS+ FORS 基元测试（Stage-3）
@version: V0.4
@Author: GoldenModel-Team
@Date: 2025-03-25 12:00
"""

from __future__ import annotations

import pytest

from sphincs_fors import fors_pk_from_sig, fors_sign, fors_verify
from sphincs_params import get_params
from sphincs_utils import derive_fors_tree_address, fors_message_to_indices


@pytest.fixture(name="fors_context")
def fixture_fors_context():
    params = get_params()
    sk_seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    pub_seed = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
    base_address = derive_fors_tree_address(0, 0, 0)
    message = bytes(range(24))
    return params, sk_seed, pub_seed, base_address, message


def test_fors_sign_verify_roundtrip(fors_context):
    params, sk_seed, pub_seed, base_address, message = fors_context
    signature, pk = fors_sign(params, message, sk_seed, pub_seed, base_address)
    n = int(params["n"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    assert len(signature) == fors_trees * (1 + fors_height) * n
    derived_pk = fors_pk_from_sig(params, signature, message, pub_seed, base_address)
    assert derived_pk == pk
    assert fors_verify(params, signature, message, pub_seed, base_address, pk)


def test_fors_message_to_indices_deterministic(fors_context):
    params, _, _, _, message = fors_context
    indices_first = fors_message_to_indices(message, params)
    indices_second = fors_message_to_indices(message, params)
    assert indices_first == indices_second
    assert len(indices_first) == int(params["fors_trees"])


def test_fors_verify_rejects_tampered_message(fors_context):
    params, sk_seed, pub_seed, base_address, message = fors_context
    signature, pk = fors_sign(params, message, sk_seed, pub_seed, base_address)
    tampered = bytes([message[0] ^ 0xFF]) + message[1:]
    assert not fors_verify(params, signature, tampered, pub_seed, base_address, pk)
