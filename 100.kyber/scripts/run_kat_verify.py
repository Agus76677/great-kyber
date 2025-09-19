#!/usr/bin/env python3
"""System-level NIST KAT verification harness."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from golden import kem_golden

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "test" / "data"


def load_vectors(path: Path) -> kem_golden.KatVector:
    payload = json.loads(path.read_text())
    return kem_golden.KatVector(
        seed=bytes(payload["seed"]),
        pk=bytes(payload["pk"]),
        sk=bytes(payload["sk"]),
        ct=bytes(payload["ct"]),
        ss=bytes(payload["ss"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kat", default="mlkem512.json", help="KAT file name")
    args = parser.parse_args()

    kat_db = kem_golden.KatDatabase()
    path = DATA_DIR / args.kat
    vector = load_vectors(path)
    kat_db.register(2, vector)
    artifacts = kem_golden.run_reference_flow(2)
    if artifacts.ciphertext != vector.ct or artifacts.shared_secret != vector.ss:
        raise SystemExit("Reference mismatch against supplied KAT")
    print("[PASS] Reference implementation matches KAT")


if __name__ == "__main__":
    main()
