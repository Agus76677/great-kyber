"""Golden models for Kyber samplers."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Tuple

KYBER_Q = 3329


@dataclass
class SamplerConfig:
    eta: int
    du: int
    dv: int


def shake128(data: bytes, outlen: int) -> bytes:
    shake = hashlib.shake_128()
    shake.update(data)
    return shake.digest(outlen)


def cbd(bytes_in: bytes, eta: int) -> List[int]:
    """Center binomial distribution sampler."""
    n_coeffs = 256
    coeffs: List[int] = []
    buf_idx = 0
    while len(coeffs) < n_coeffs:
        if eta == 2:
            if buf_idx + 3 > len(bytes_in):
                raise ValueError("Insufficient randomness for CBD")
            t = int.from_bytes(bytes_in[buf_idx : buf_idx + 3], "little")
            buf_idx += 3
            for j in range(0, 24, 6):
                a = (t >> j) & 0x7
                b = (t >> (j + eta)) & 0x7
                coeffs.append((a - b) % KYBER_Q)
        else:
            raise NotImplementedError("Eta other than 2 not yet supported")
    return coeffs[:n_coeffs]


def uniform(bytes_in: bytes, bound: int) -> List[int]:
    coeffs: List[int] = []
    idx = 0
    while len(coeffs) < 256 and idx + 2 <= len(bytes_in):
        val = bytes_in[idx] | ((bytes_in[idx + 1] & 0x0F) << 8)
        idx += 2
        if val < bound:
            coeffs.append(val)
    if len(coeffs) < 256:
        raise ValueError("Reject sampler would request more bytes")
    return coeffs


def decompress(values: Iterable[int], d: int) -> List[int]:
    return [((v << (13 - d)) + 1) >> 1 for v in values]


def compress(values: Iterable[int], d: int) -> List[int]:
    return [((v << d) + (1 << 12)) >> 13 for v in values]
