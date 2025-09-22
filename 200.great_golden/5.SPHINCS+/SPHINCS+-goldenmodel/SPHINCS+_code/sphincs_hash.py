"""
@Descripttion: SPHINCS+ 哈希接口（SHA256 Level-1）
@version: V0.5
@Author: GoldenModel-Team
@Date: 2025-04-02 12:00

与 Kyber / Dilithium 黄金模型保持一致的注释与结构，
该版本对齐 NIST 参考实现中的 mgf1/thash/HMAC 细节，
为 Stage-5 向量对齐提供基础能力。
"""

from __future__ import annotations

import hashlib
from typing import Iterable, List, Mapping, Sequence, Tuple

from auxiliary_function import ADR_BYTES, concat_bytes, ensure_bytes, xor_bytes

_SHA256_BLOCK_BYTES = 64
_SHA256_OUTPUT_BYTES = 32


def _truncate_to_n(digest: bytes, params: Mapping[str, int | str]) -> bytes:
    n = int(params["n"])
    return digest[:n]


def _sha256(data: bytes) -> bytes:
    """hashlib.sha256 包装，便于未来替换 SHAKE/HARAKA 实现。"""

    # TODO(Stage-7/8): 引入 SHAKE256 / Haraka 加速。
    return hashlib.sha256(data).digest()


def _mgf1(seed: bytes, out_len: int) -> bytes:
    """参照参考实现的 MGF1，用 SHA256 扩展掩码。"""

    if out_len <= 0:
        return b""
    counter = 0
    blocks: List[bytes] = []
    while len(b"".join(blocks)) < out_len:
        ctr_bytes = counter.to_bytes(4, "big")
        blocks.append(_sha256(seed + ctr_bytes))
        counter += 1
    return b"".join(blocks)[:out_len]


def _pad_key_block(key: bytes) -> bytearray:
    padded = bytearray(_SHA256_BLOCK_BYTES)
    padded[: len(key)] = key
    return padded


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    """简化版 HMAC-SHA256，对齐参考实现。"""

    key_block = _pad_key_block(key)
    for idx in range(_SHA256_BLOCK_BYTES):
        key_block[idx] ^= 0x36
    inner = bytes(key_block) + data
    inner_hash = _sha256(inner)

    key_block = _pad_key_block(key)
    for idx in range(_SHA256_BLOCK_BYTES):
        key_block[idx] ^= 0x5C
    outer = bytes(key_block) + inner_hash
    return _sha256(outer)


def _thash(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    address: bytes,
    inputs: Sequence[bytes],
) -> bytes:
    """通用 tweakable hash，兼容 F/H/FORS 聚合场景。"""

    n = int(params["n"])
    if not inputs:
        raise ValueError("thash requires at least one input block")
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    addr_n = ensure_bytes(address, length=ADR_BYTES)
    data = b"".join(ensure_bytes(block, length=n) for block in inputs)
    bitmask = _mgf1(pub_seed_n + addr_n, len(data))
    masked = xor_bytes(data, bitmask)
    return _truncate_to_n(_sha256(pub_seed_n + addr_n + masked), params)


def _fors_msg_bytes(params: Mapping[str, int | str]) -> int:
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    total_bits = fors_height * fors_trees
    return (total_bits + 0x7) & ~0x7


def F(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    address: bytes,
    message: bytes,
) -> bytes:
    """SPHINCS+ tweakable hash F。"""

    return _thash(params, pub_seed, address, [message])


def H(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    address: bytes,
    left: bytes,
    right: bytes,
) -> bytes:
    """SPHINCS+ tweakable hash H（两输入 Merkle 压缩）。"""

    return _thash(params, pub_seed, address, [left, right])


def thash_multi(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    address: bytes,
    inputs: Sequence[bytes],
) -> bytes:
    """外部可用的多输入 tweakable hash。"""

    return _thash(params, pub_seed, address, inputs)


def PRF(
    params: Mapping[str, int | str],
    key: bytes,
    address: bytes,
) -> bytes:
    """SPHINCS+ PRF(SK.prf, ADR)。"""

    n = int(params["n"])
    key_n = ensure_bytes(key, length=n)
    addr_n = ensure_bytes(address, length=ADR_BYTES)
    block = bytearray(_SHA256_BLOCK_BYTES + ADR_BYTES)
    block[:n] = key_n
    # 其余补零，无需显式处理
    block[_SHA256_BLOCK_BYTES : _SHA256_BLOCK_BYTES + ADR_BYTES] = addr_n
    digest = _sha256(bytes(block))
    return digest[:n]


def PRF_msg(
    params: Mapping[str, int | str],
    key: bytes,
    opt_random: bytes,
    message: bytes,
) -> bytes:
    """SPHINCS+ PRF_msg(SK.prf, optRand, M)。"""

    n = int(params["n"])
    key_n = ensure_bytes(key, length=n)
    opt_rand_n = ensure_bytes(opt_random, length=n)
    msg_bytes = ensure_bytes(message)
    mac = _hmac_sha256(key_n, opt_rand_n + msg_bytes)
    return mac[:n]


def H_msg(
    params: Mapping[str, int | str],
    randomness: bytes,
    public_key: bytes,
    message: bytes,
) -> Tuple[bytes, int, int]:
    """SPHINCS+ H_msg(R, PK, M) -> (digest, tree, leaf_idx)。"""

    n = int(params["n"])
    full_height = int(params["full_height"])
    tree_height = int(params["tree_height"])
    tree_bits = full_height - tree_height
    tree_bytes = (tree_bits + 7) // 8
    leaf_bits = tree_height
    leaf_bytes = (leaf_bits + 7) // 8
    digest_bytes = _fors_msg_bytes(params)

    rand_n = ensure_bytes(randomness, length=n)
    pk_n = ensure_bytes(public_key)
    msg_bytes = ensure_bytes(message)

    seed = _sha256(rand_n + pk_n + msg_bytes)
    buf = _mgf1(seed, digest_bytes + tree_bytes + leaf_bytes)
    digest = buf[:digest_bytes]
    offset = digest_bytes

    tree_slice = buf[offset : offset + tree_bytes]
    offset += tree_bytes
    leaf_slice = buf[offset : offset + leaf_bytes]

    tree = int.from_bytes(tree_slice, "big") & ((1 << tree_bits) - 1 if tree_bits > 0 else 0)
    leaf = int.from_bytes(leaf_slice, "big") & ((1 << leaf_bits) - 1 if leaf_bits > 0 else 0)
    return digest, tree, leaf


__all__ = ["F", "H", "PRF", "PRF_msg", "H_msg", "thash_multi"]
