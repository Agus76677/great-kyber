"""High-level Kyber reference wrapper.

This module exposes helpers to run ML-KEM key generation, encapsulation, and
decapsulation using the reference PQClean implementation.  It is intentionally
light-weight so that hardware verification scripts can import without pulling in
full Python dependencies unless needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

try:
    from pqclean import mlkem512, mlkem768, mlkem1024  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    mlkem512 = mlkem768 = mlkem1024 = None


@dataclass
class KyberArtifacts:
    public_key: bytes
    secret_key: bytes
    ciphertext: bytes
    shared_secret: bytes


def _select_impl(k: int):
    if k == 2:
        return mlkem512
    if k == 3:
        return mlkem768
    if k == 4:
        return mlkem1024
    raise ValueError(f"Unsupported security level k={k}")


def keygen(k: int) -> Tuple[bytes, bytes]:
    impl = _select_impl(k)
    if impl is None:
        raise RuntimeError("PQClean Kyber implementation not available")
    return impl.keypair()


def encapsulate(k: int, public_key: bytes) -> Tuple[bytes, bytes]:
    impl = _select_impl(k)
    if impl is None:
        raise RuntimeError("PQClean Kyber implementation not available")
    return impl.enc(public_key)


def decapsulate(k: int, secret_key: bytes, ciphertext: bytes) -> bytes:
    impl = _select_impl(k)
    if impl is None:
        raise RuntimeError("PQClean Kyber implementation not available")
    return impl.dec(ciphertext, secret_key)


def full_flow(k: int) -> KyberArtifacts:
    pk, sk = keygen(k)
    ct, ss_enc = encapsulate(k, pk)
    ss_dec = decapsulate(k, sk, ct)
    assert ss_enc == ss_dec, "Reference stack self-check failed"
    return KyberArtifacts(public_key=pk, secret_key=sk, ciphertext=ct, shared_secret=ss_enc)
