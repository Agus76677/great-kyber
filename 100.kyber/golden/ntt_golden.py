"""Reference Number-Theoretic Transform for Kyber."""
from __future__ import annotations

from typing import Iterable, List

KYBER_Q = 3329
KYBER_N = 256

# Precomputed twiddle factors from reference implementation (Montgomery domain).
# The list is intentionally partial; populate during bring-up using PQClean tables.
ZETAS = [
    2285,  2571,  2647,  1425,  573,  2004,  1730,  3009,
    3289,  264,   2456,  1846,  3113,  652,   908,   2298,
]


def montgomery_reduce(a: int) -> int:
    """Perform Montgomery reduction in software."""
    u = (a * 62209) & 0xFFFF
    t = (u * KYBER_Q)
    return (a - t) >> 16


def barrett_reduce(a: int) -> int:
    """Perform Barrett reduction."""
    v = ((1 << 26) + KYBER_Q // 2) // KYBER_Q
    t = (v * a) >> 26
    t *= KYBER_Q
    return a - t


def ntt(poly: Iterable[int]) -> List[int]:
    """Compute the forward NTT of a polynomial."""
    vec = list(poly)
    if len(vec) != KYBER_N:
        raise ValueError("Polynomial length must be 256")
    k = 0
    length = 128
    while length >= 1:
        for start in range(0, KYBER_N, 2 * length):
            zeta = ZETAS[k]
            k += 1
            for j in range(start, start + length):
                t = montgomery_reduce(zeta * vec[j + length])
                vec[j + length] = barrett_reduce(vec[j] - t)
                vec[j] = barrett_reduce(vec[j] + t)
        length //= 2
    return [x % KYBER_Q for x in vec]


def intt(poly: Iterable[int]) -> List[int]:
    """Compute the inverse NTT (normalized)."""
    vec = list(poly)
    if len(vec) != KYBER_N:
        raise ValueError("Polynomial length must be 256")
    k = len(ZETAS) - 1
    length = 1
    while length < KYBER_N:
        for start in range(0, KYBER_N, 2 * length):
            zeta = ZETAS[k]
            k -= 1
            for j in range(start, start + length):
                t = vec[j]
                vec[j] = barrett_reduce(t + vec[j + length])
                vec[j + length] = montgomery_reduce(zeta * (t - vec[j + length]))
        length *= 2
    # Multiply by n^{-1} = 1441 mod q
    inv_n = 1441
    return [montgomery_reduce(x * inv_n) % KYBER_Q for x in vec]
