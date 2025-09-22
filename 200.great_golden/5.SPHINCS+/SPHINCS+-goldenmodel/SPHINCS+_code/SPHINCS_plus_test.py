"""
@Descripttion: SPHINCS+ 端到端测试（Stage-6 多安全级别版）
@version: V0.6
@Author: GoldenModel-Team
@Date: 2025-04-05 12:00
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pytest

from SPHINCS_plus import KeyGen, Sign, Verify
from sphincs_params import get_params


def _signature_length(params: Dict[str, int | str]) -> int:
    n = int(params["n"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    d = int(params["d"])
    tree_height = int(params["tree_height"])
    wots_len = int(params["len"]) * n
    auth_len = tree_height * n
    fors_len = fors_trees * (fors_height + 1) * n
    return n + fors_len + d * (wots_len + auth_len)


@dataclass
class SphincsContext:
    level: int
    params: Dict[str, int | str]
    pk: dict[str, bytes]
    sk: dict[str, bytes]
    message: bytes
    signature: bytes


@pytest.fixture(params=[1, 3, 5], name="sphincs_context")
def fixture_sphincs_context(request) -> SphincsContext:
    level = int(request.param)
    params = get_params(level=level)
    n = int(params["n"])
    seed = bytes((i % 256) for i in range(3 * n))
    pk, sk = KeyGen(params, seed=seed)
    message = f"Stage6 regression message L{level}".encode("utf-8")
    signature = Sign(sk, message, params)
    return SphincsContext(level, params, pk, sk, message, signature)


def test_sign_verify_roundtrip(sphincs_context: SphincsContext) -> None:
    level = sphincs_context.level
    params = sphincs_context.params
    pk = sphincs_context.pk
    sk = sphincs_context.sk
    message = sphincs_context.message
    signature = sphincs_context.signature

    assert len(signature) == _signature_length(params)
    assert Verify(pk, message, signature, params)
    tampered_message = message + b"!"
    assert not Verify(pk, tampered_message, signature, params)
    tampered_sig = bytearray(signature)
    tampered_sig[-1] ^= 0x01
    assert not Verify(pk, message, bytes(tampered_sig), params)
    if level == 1:
        assert signature == Sign(sk, message, params)


def test_sign_verify_empty_message(sphincs_context: SphincsContext) -> None:
    params = sphincs_context.params
    pk = sphincs_context.pk
    sk = sphincs_context.sk
    signature = Sign(sk, b"", params)
    assert len(signature) == _signature_length(params)
    assert Verify(pk, b"", signature, params)


def test_sign_verify_large_message(sphincs_context: SphincsContext) -> None:
    level = sphincs_context.level
    params = sphincs_context.params
    pk = sphincs_context.pk
    sk = sphincs_context.sk
    if level != 1:
        pytest.skip("100KB 长消息性能基线在 Level-1 覆盖，高等级共享相同实现。")
    large_message = bytes([i % 251 for i in range(100_000)])
    signature = Sign(sk, large_message, params)
    assert Verify(pk, large_message, signature, params)
