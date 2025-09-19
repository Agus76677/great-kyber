"""Polynomial arithmetic helpers for Kyber."""
from __future__ import annotations

from typing import Iterable, List

KYBER_Q = 3329


def add(a: Iterable[int], b: Iterable[int]) -> List[int]:
    return [((x + y) % KYBER_Q) for x, y in zip(a, b)]


def sub(a: Iterable[int], b: Iterable[int]) -> List[int]:
    return [((x - y) % KYBER_Q) for x, y in zip(a, b)]


def base_mul(a: Iterable[int], b: Iterable[int], zetas: Iterable[int]) -> List[int]:
    res = []
    for i, (x, y) in enumerate(zip(a, b)):
        zeta = zetas[i % len(zetas)]
        res.append((x * y * zeta) % KYBER_Q)
    return res


def pointwise_accumulate(acc: Iterable[int], vecs: Iterable[Iterable[int]]) -> List[int]:
    acc_list = list(acc)
    for vec in vecs:
        acc_list = [(x + y) % KYBER_Q for x, y in zip(acc_list, vec)]
    return acc_list
