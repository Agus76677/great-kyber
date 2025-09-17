#!/usr/bin/env python3
"""Test vector generator and golden model for the reject_sampler module."""

from __future__ import annotations

import argparse
import pathlib
import random
from typing import List

LANES = 4
CAND_BITS = 12
NUM_VECTORS = 64
Q_VALUE = 3329
PIPELINE_LATENCY = 2
RESET_CYCLES = 4
FINAL_FLUSH_CYCLES = 4  # idle cycles while the pipeline drains
OUT_BITS = LANES * CAND_BITS
BASE_DIR = pathlib.Path(__file__).resolve().parent


def pack_words(words: List[int], width: int) -> int:
    """Pack little-endian lane words into a single integer."""
    value = 0
    mask = (1 << width) - 1
    for idx, word in enumerate(words):
        value |= (word & mask) << (idx * width)
    return value


def format_hex(value: int, width_bits: int) -> str:
    if value == 0:
        return "0"
    return f"{value:x}"


def bernoulli_sample(accepted: int) -> int:
    if CAND_BITS == 1:
        return accepted & 0x1
    return accepted & 0x1


def generate_vectors(seed: int = 2024) -> None:
    rng = random.Random(seed)

    cand_lines: List[str] = []
    urnd_lines: List[str] = []
    mode_lines: List[str] = []

    expected_valid: List[int] = []
    expected_acc: List[int] = []
    expected_samples: List[int] = []

    for vec_idx in range(NUM_VECTORS):
        cand_lane = [rng.getrandbits(CAND_BITS) for _ in range(LANES)]
        urnd_lane = [rng.getrandbits(CAND_BITS) for _ in range(LANES)]

        mode = 0 if vec_idx < NUM_VECTORS // 2 else 1

        cand_lines.append(format_hex(pack_words(cand_lane, CAND_BITS), OUT_BITS))
        urnd_lines.append(format_hex(pack_words(urnd_lane, CAND_BITS), OUT_BITS))
        mode_lines.append(f"{mode:x}")

        if mode == 0:
            accept = [1 if cand < Q_VALUE else 0 for cand in cand_lane]
            sample_words = [cand if acc else 0 for cand, acc in zip(cand_lane, accept)]
        else:
            accept = [1 if urnd < cand else 0 for urnd, cand in zip(urnd_lane, cand_lane)]
            sample_words = [bernoulli_sample(acc) for acc in accept]

        acc_value = pack_words(accept, 1)
        sample_value = pack_words(sample_words, CAND_BITS)

        expected_acc.append(acc_value)
        expected_samples.append(sample_value)
        expected_valid.append(1 if acc_value != 0 else 0)

    total_cycles = RESET_CYCLES + NUM_VECTORS + FINAL_FLUSH_CYCLES - 1
    expected_lines: List[str] = []

    for cycle in range(total_cycles):
        if (
            RESET_CYCLES + PIPELINE_LATENCY
            <= cycle
            < RESET_CYCLES + PIPELINE_LATENCY + NUM_VECTORS
        ):
            idx = cycle - (RESET_CYCLES + PIPELINE_LATENCY)
            valid = expected_valid[idx]
            acc = expected_acc[idx]
            sample = expected_samples[idx]
        else:
            valid = 0
            acc = 0
            sample = 0
        expected_lines.append(
            f"{valid:d} {format_hex(acc, LANES):s} {format_hex(sample, OUT_BITS):s}"
        )

    (BASE_DIR / "cand.mem").write_text("\n".join(cand_lines) + "\n", encoding="utf-8")
    (BASE_DIR / "urnd.mem").write_text("\n".join(urnd_lines) + "\n", encoding="utf-8")
    (BASE_DIR / "mode.mem").write_text("\n".join(mode_lines) + "\n", encoding="utf-8")
    (BASE_DIR / "expected_output.txt").write_text(
        "\n".join(expected_lines) + "\n", encoding="utf-8"
    )

    print("Generated test vectors and golden reference.")


def verify_results() -> None:
    rtl_path = BASE_DIR / "rtl_output.txt"
    expected_path = BASE_DIR / "expected_output.txt"

    if not rtl_path.exists():
        raise FileNotFoundError(f"RTL output {rtl_path} not found. Run the simulation first.")
    if not expected_path.exists():
        raise FileNotFoundError("Expected output file is missing. Generate vectors first.")

    rtl_lines = [line.strip() for line in rtl_path.read_text(encoding="utf-8").splitlines()]
    expected_lines = [
        line.strip() for line in expected_path.read_text(encoding="utf-8").splitlines()
    ]

    if len(rtl_lines) != len(expected_lines):
        raise AssertionError(
            f"Line count mismatch: RTL={len(rtl_lines)} Expected={len(expected_lines)}"
        )

    mismatches = [
        (idx, rtl_line, golden_line)
        for idx, (rtl_line, golden_line) in enumerate(zip(rtl_lines, expected_lines))
        if rtl_line != golden_line
    ]

    if mismatches:
        for idx, rtl_line, golden_line in mismatches[:10]:
            print(f"Mismatch at line {idx}: RTL={rtl_line} Golden={golden_line}")
        raise AssertionError(f"Found {len(mismatches)} mismatching lines between RTL and golden.")

    print("RTL output matches the golden model.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reject sampler test utilities")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify RTL output against the golden model instead of generating vectors.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2024,
        help="Seed for pseudo-random vector generation",
    )
    args = parser.parse_args()

    if args.verify:
        verify_results()
    else:
        generate_vectors(seed=args.seed)


if __name__ == "__main__":
    main()
