"""
@Descripttion: SPHINCS+ 端到端测试（Stage-4 版本）
@version: V0.4
@Author: GoldenModel-Team
@Date: 2025-03-30 12:00
"""

from __future__ import annotations

from typing import Tuple

import pytest

from SPHINCS_plus import KeyGen, Sign, Verify
from sphincs_params import get_params


def _signature_length(params: dict[str, int | str]) -> int:
    n = int(params["n"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    d = int(params["d"])
    tree_height = int(params["tree_height"])
    wots_len = int(params["len"]) * n
    auth_len = tree_height * n
    fors_len = fors_trees * (fors_height + 1) * n
    return n + fors_len + d * (wots_len + auth_len)


@pytest.fixture(name="sphincs_context")
def fixture_sphincs_context() -> Tuple[dict[str, int | str], dict[str, bytes], dict[str, bytes]]:
    params = get_params()
    seed = bytes.fromhex(
        "00112233445566778899aabbccddeeff"
        "102132435465768798a9babbdcddfef0"
        "203142434445464748494a4b4c4d4e4f"
    )
    pk, sk = KeyGen(params, seed=seed)
    return params, pk, sk


def test_sign_verify_roundtrip(sphincs_context) -> None:
    params, pk, sk = sphincs_context
    message = b"Stage4 regression message"
    signature = Sign(sk, message, params)
    assert len(signature) == _signature_length(params)
    assert Verify(pk, message, signature, params)
    tampered_message = message + b"!"
    assert not Verify(pk, tampered_message, signature, params)
    tampered_sig = bytearray(signature)
    tampered_sig[-1] ^= 0x01
    assert not Verify(pk, message, bytes(tampered_sig), params)
    assert signature == Sign(sk, message, params)


def test_sign_verify_empty_message(sphincs_context) -> None:
    params, pk, sk = sphincs_context
    signature = Sign(sk, b"", params)
    assert len(signature) == _signature_length(params)
    assert Verify(pk, b"", signature, params)


def test_sign_verify_large_message(sphincs_context) -> None:
    params, pk, sk = sphincs_context
    large_message = bytes([i % 251 for i in range(100_000)])
    signature = Sign(sk, large_message, params)
    assert Verify(pk, large_message, signature, params)
