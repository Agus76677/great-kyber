"""End-to-end Kyber golden model helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from . import kyber_ref


@dataclass
class KatVector:
    seed: bytes
    pk: bytes
    sk: bytes
    ct: bytes
    ss: bytes


class KatDatabase:
    """Minimal container for NIST Known Answer Tests."""

    def __init__(self) -> None:
        self._vectors: Dict[int, KatVector] = {}

    def register(self, k: int, vector: KatVector) -> None:
        self._vectors[k] = vector

    def get(self, k: int) -> KatVector:
        try:
            return self._vectors[k]
        except KeyError as exc:  # pragma: no cover - configuration error
            raise RuntimeError(f"KAT for k={k} not loaded") from exc


def run_reference_flow(k: int) -> kyber_ref.KyberArtifacts:
    return kyber_ref.full_flow(k)
