"""Utility to generate simulation vectors for Kyber hardware modules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

from . import kyber_ref, sample_golden


def generate_cbd_vectors(seed: bytes, eta: int) -> Dict[str, Iterable[int]]:
    stream = sample_golden.shake128(seed, 256)
    coeffs = sample_golden.cbd(stream, eta)
    return {"seed": list(seed), "coeffs": coeffs}


def generate_uniform_vectors(seed: bytes, bound: int) -> Dict[str, Iterable[int]]:
    stream = sample_golden.shake128(seed, 512)
    coeffs = sample_golden.uniform(stream, bound)
    return {"seed": list(seed), "coeffs": coeffs}


def dump_vectors(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def main() -> None:
    base = Path(__file__).resolve().parents[1] / "test" / "data"
    seed = bytes(range(48))
    dump_vectors(base / "cbd_eta2.json", generate_cbd_vectors(seed, eta=2))
    dump_vectors(base / "uniform_q.json", generate_uniform_vectors(seed, bound=3329))
    artifacts = kyber_ref.full_flow(2)
    dump_vectors(
        base / "mlkem512.json",
        {
            "pk": list(artifacts.public_key),
            "sk": list(artifacts.secret_key),
            "ct": list(artifacts.ciphertext),
            "ss": list(artifacts.shared_secret),
        },
    )


if __name__ == "__main__":
    main()
