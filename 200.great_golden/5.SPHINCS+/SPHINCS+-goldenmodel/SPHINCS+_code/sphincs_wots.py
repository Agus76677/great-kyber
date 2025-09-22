"""
@Descripttion: SPHINCS+ WOTS+ 基元实现（Stage-2 版本）
@version: V0.3
@Author: GoldenModel-Team
@Date: 2025-03-20 12:00

对齐 CRYSTALS-Kyber / Dilithium 黄金模型的注释与接口风格，
提供链函数、密钥生成、签名与验证流程。
"""

from __future__ import annotations

from typing import List, Mapping

from auxiliary_function import (
    ADR_BYTES,
    address_to_bytes,
    bytes_to_address,
    copy_address,
    ensure_bytes,
    set_chain_addr,
    set_hash_addr,
)
from sphincs_hash import F, PRF


def _log_w(params: Mapping[str, int | str]) -> tuple[int, int]:
    w = int(params["w"])
    if w <= 1:
        raise ValueError("w must be greater than 1")
    log_w = w.bit_length() - 1
    if 1 << log_w != w:
        raise ValueError("Stage 2 implementation assumes power-of-two w")
    return w, log_w


def _base_w(
    params: Mapping[str, int | str],
    data: bytes,
    output_len: int,
) -> List[int]:
    """
    将输入字节转换为 base-w 表示，输出固定长度序列。
    """

    w, log_w = _log_w(params)
    normalized = ensure_bytes(data)
    acc = 0
    bits = 0
    out: List[int] = []
    idx = 0
    for _ in range(output_len):
        if bits < log_w:
            if idx >= len(normalized):
                raise ValueError("insufficient data for base_w conversion")
            acc = (acc << 8) | normalized[idx]
            idx += 1
            bits += 8
        bits -= log_w
        out.append((acc >> bits) & (w - 1))
    if bits > 0 and (acc & ((1 << bits) - 1)) != 0:
        raise ValueError("unused base_w bits must be zero")
    return out


def _chain_lengths(
    params: Mapping[str, int | str],
    message: bytes,
) -> List[int]:
    """
    计算 WOTS+ 链长度（消息 + 校验和）。
    """

    n = int(params["n"])
    len_1 = int(params["len_1"])
    len_2 = int(params["len_2"])
    w, log_w = _log_w(params)
    msg_n = ensure_bytes(message, length=n)
    msg_base = _base_w(params, msg_n, len_1)
    checksum = 0
    for value in msg_base:
        checksum += w - 1 - value
    checksum_bits = len_2 * log_w
    checksum_bytes_len = (checksum_bits + 7) // 8
    shift = checksum_bytes_len * 8 - checksum_bits
    checksum_value = checksum << shift
    checksum_bytes = checksum_value.to_bytes(checksum_bytes_len, "big")
    checksum_base = _base_w(params, checksum_bytes, len_2)
    return msg_base + checksum_base


def wots_chain(
    params: Mapping[str, int | str],
    start_value: bytes,
    start_idx: int,
    steps: int,
    pub_seed: bytes,
    address: bytes,
) -> bytes:
    """
    WOTS+ 链函数：从 start_idx 开始迭代 steps 次 F。输入输出均为 n 字节。
    """

    n = int(params["n"])
    w = int(params["w"])
    if start_idx < 0 or steps < 0:
        raise ValueError("start index and steps must be non-negative")
    if start_idx + steps > w - 1:
        raise ValueError("start_idx + steps exceeds chain length")
    result = ensure_bytes(start_value, length=n)
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    addr_words = copy_address(bytes_to_address(ensure_bytes(address, length=ADR_BYTES)))
    for idx in range(start_idx, start_idx + steps):
        set_hash_addr(addr_words, idx)
        result = F(params, pub_seed_n, address_to_bytes(addr_words), result)
    return result


def _generate_secret_element(
    params: Mapping[str, int | str],
    sk_seed: bytes,
    address_words: List[int],
) -> bytes:
    n = int(params["n"])
    sk_seed_n = ensure_bytes(sk_seed, length=n)
    return PRF(params, sk_seed_n, address_to_bytes(address_words))


def wots_gen_pk(
    params: Mapping[str, int | str],
    sk_seed: bytes,
    pub_seed: bytes,
    base_address: bytes,
) -> bytes:
    """
    基于种子生成 WOTS+ 公钥（len × n 字节）。
    """

    length = int(params["len"])
    base_words = copy_address(bytes_to_address(ensure_bytes(base_address, length=ADR_BYTES)))
    pk_chunks: List[bytes] = []
    for chain_idx in range(length):
        addr_words = copy_address(base_words)
        set_chain_addr(addr_words, chain_idx)
        set_hash_addr(addr_words, 0)
        sk_element = _generate_secret_element(params, sk_seed, addr_words)
        pk_chunks.append(
            wots_chain(
                params,
                sk_element,
                0,
                int(params["w"]) - 1,
                pub_seed,
                address_to_bytes(addr_words),
            )
        )
    return b"".join(pk_chunks)


def wots_sign(
    params: Mapping[str, int | str],
    message: bytes,
    sk_seed: bytes,
    pub_seed: bytes,
    base_address: bytes,
) -> bytes:
    """
    使用消息摘要生成 WOTS+ 签名，输出 len × n 字节。
    """

    chain_lengths = _chain_lengths(params, message)
    base_words = copy_address(bytes_to_address(ensure_bytes(base_address, length=ADR_BYTES)))
    signature_chunks: List[bytes] = []
    for chain_idx, steps in enumerate(chain_lengths):
        addr_words = copy_address(base_words)
        set_chain_addr(addr_words, chain_idx)
        set_hash_addr(addr_words, 0)
        sk_element = _generate_secret_element(params, sk_seed, addr_words)
        signature_chunks.append(
            wots_chain(
                params,
                sk_element,
                0,
                steps,
                pub_seed,
                address_to_bytes(addr_words),
            )
        )
    return b"".join(signature_chunks)


def wots_pk_from_sig(
    params: Mapping[str, int | str],
    signature: bytes,
    message: bytes,
    pub_seed: bytes,
    base_address: bytes,
) -> bytes:
    """
    根据签名与消息恢复 WOTS+ 公钥。
    """

    n = int(params["n"])
    length = int(params["len"])
    if len(signature) != length * n:
        raise ValueError("invalid signature length")
    chain_lengths = _chain_lengths(params, message)
    base_words = copy_address(bytes_to_address(ensure_bytes(base_address, length=ADR_BYTES)))
    pk_chunks: List[bytes] = []
    for chain_idx in range(length):
        start_idx = chain_lengths[chain_idx]
        steps = int(params["w"]) - 1 - start_idx
        addr_words = copy_address(base_words)
        set_chain_addr(addr_words, chain_idx)
        set_hash_addr(addr_words, start_idx)
        element = ensure_bytes(signature[chain_idx * n : (chain_idx + 1) * n], length=n)
        pk_chunks.append(
            wots_chain(
                params,
                element,
                start_idx,
                steps,
                pub_seed,
                address_to_bytes(addr_words),
            )
        )
    return b"".join(pk_chunks)


def wots_verify(
    params: Mapping[str, int | str],
    message: bytes,
    signature: bytes,
    pub_seed: bytes,
    base_address: bytes,
    expected_pk: bytes,
) -> bool:
    """
    验证签名是否匹配期望的 WOTS+ 公钥。
    """

    derived_pk = wots_pk_from_sig(params, signature, message, pub_seed, base_address)
    return derived_pk == ensure_bytes(expected_pk, length=len(derived_pk))


__all__ = [
    "wots_chain",
    "wots_gen_pk",
    "wots_sign",
    "wots_pk_from_sig",
    "wots_verify",
]
