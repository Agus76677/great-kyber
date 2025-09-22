"""
@Descripttion: SPHINCS+ 端到端测试（Stage-6 版本）
@version: V0.6
@Author: GoldenModel-Team
@Date: 2025-04-05 12:00
"""

from __future__ import annotations

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
def _deterministic_seed(n: int) -> bytes:
    return bytes(range(3 * n))


def _context(level: int) -> tuple[dict[str, int | str], dict[str, bytes], dict[str, bytes]]:
    params = get_params(level=level)
    seed = _deterministic_seed(int(params["n"]))
    pk, sk = KeyGen(params, seed=seed)
    return params, pk, sk


@pytest.mark.parametrize("level", [1, 3, 5])
def test_sign_verify_roundtrip(level: int) -> None:
    params, pk, sk = _context(level)
    message = f"Stage6 regression message L{level}".encode()
    signature = Sign(sk, message, params)
    assert len(signature) == _signature_length(params)
    assert Verify(pk, message, signature, params)
    if level == 1:
        tampered_message = message + b"!"
        assert not Verify(pk, tampered_message, signature, params)
        tampered_sig = bytearray(signature)
        tampered_sig[-1] ^= 0x01
        assert not Verify(pk, message, bytes(tampered_sig), params)
        assert signature == Sign(sk, message, params)


@pytest.mark.parametrize("level", [1])
def test_sign_verify_empty_message(level: int) -> None:
    params, pk, sk = _context(level)
    signature = Sign(sk, b"", params)
    assert len(signature) == _signature_length(params)
    assert Verify(pk, b"", signature, params)


@pytest.mark.parametrize("level", [1])
def test_sign_verify_large_message(level: int) -> None:
    params, pk, sk = _context(level)
    large_message = bytes([i % 251 for i in range(100_000)])
    signature = Sign(sk, large_message, params)
    assert Verify(pk, large_message, signature, params)
