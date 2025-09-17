#!/usr/bin/env python3
"""Run Kyber NTT/INTT hardware verification against a Python golden model."""
from __future__ import annotations

import math
import random
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

KYBER_Q = 3329
KYBER_N = 256

ROOT = Path(__file__).resolve().parents[2]
NTT_DIR = ROOT / "5.NTT"
TEST_DIR = NTT_DIR / "test"
BUILD_DIR = TEST_DIR / "build"

NTT_INPUT = TEST_DIR / "ntt_input.hex"
NTT_OUTPUT = TEST_DIR / "ntt_output_hw.hex"
INTT_INPUT = TEST_DIR / "intt_input.hex"
INTT_OUTPUT = TEST_DIR / "intt_output_hw.hex"


def ensure_build_dir() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def generate_roots() -> tuple[List[int], List[int]]:
    g = 17
    omega = pow(g, (KYBER_Q - 1) // KYBER_N, KYBER_Q)
    omega_inv = pow(omega, KYBER_N - 1, KYBER_Q)

    zetas: List[int] = []
    len_size = 1
    while len_size < KYBER_N:
        w = 1
        step = pow(omega, KYBER_N // (2 * len_size), KYBER_Q)
        for _ in range(len_size):
            zetas.append(w)
            w = (w * step) % KYBER_Q
        len_size <<= 1

    zetas_inv: List[int] = []
    len_size = KYBER_N // 2
    while len_size >= 1:
        w = 1
        step = pow(omega_inv, KYBER_N // (2 * len_size), KYBER_Q)
        for _ in range(len_size):
            zetas_inv.append(w)
            w = (w * step) % KYBER_Q
        len_size >>= 1

    return zetas, zetas_inv


ZETAS, ZETAS_INV = generate_roots()


def ntt(poly: List[int]) -> List[int]:
    result = list(poly)
    len_size = 1
    k = 0
    while len_size < KYBER_N:
        for start in range(0, KYBER_N, 2 * len_size):
            for j in range(len_size):
                zeta = ZETAS[k + j]
                t = (result[start + j + len_size] * zeta) % KYBER_Q
                u = result[start + j]
                result[start + j] = (u + t) % KYBER_Q
                result[start + j + len_size] = (u - t) % KYBER_Q
        k += len_size
        len_size <<= 1
    return result


def intt(poly: List[int]) -> List[int]:
    result = list(poly)
    len_size = KYBER_N // 2
    k = 0
    while len_size >= 1:
        for start in range(0, KYBER_N, 2 * len_size):
            for j in range(len_size):
                u = result[start + j]
                v = result[start + j + len_size]
                result[start + j] = (u + v) % KYBER_Q
                t = (u - v) % KYBER_Q
                zeta = ZETAS_INV[k + j]
                result[start + j + len_size] = (t * zeta) % KYBER_Q
        k += len_size
        len_size >>= 1
    n_inv = pow(KYBER_N, KYBER_Q - 2, KYBER_Q)
    return [(x * n_inv) % KYBER_Q for x in result]


def pack_words(coeffs: Iterable[int]) -> List[int]:
    coeff_list = list(coeffs)
    if len(coeff_list) != KYBER_N:
        raise ValueError("Expected 256 coefficients")
    words: List[int] = []
    for i in range(0, KYBER_N, 8):
        word = 0
        for j in range(8):
            word |= (coeff_list[i + j] & 0xFFFF) << (16 * j)
        words.append(word)
    return words


def unpack_words(words: Iterable[int]) -> List[int]:
    coeffs: List[int] = []
    for word in words:
        for j in range(8):
            coeffs.append((word >> (16 * j)) & 0xFFFF)
    if len(coeffs) != KYBER_N:
        raise ValueError("Incorrect coefficient count during unpack")
    return coeffs


def write_hex(path: Path, words: Iterable[int]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for word in words:
            handle.write(f"{word:032x}\n")


def read_hex(path: Path) -> List[int]:
    words: List[int] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            words.append(int(line.strip(), 16))
    return words


def build_tb(top: str, sources: Iterable[Path], output: Path) -> None:
    cmd = [
        "iverilog",
        "-g2012",
        "-I",
        str(NTT_DIR),
        "-s",
        top,
        "-o",
        str(output),
    ] + [str(src) for src in sources]
    subprocess.run(cmd, check=True, cwd=ROOT)


def run_vvp(executable: Path, workdir: Path) -> None:
    subprocess.run(["vvp", str(executable)], check=True, cwd=workdir)


def chi_square(values: Iterable[int], bins: int = 16) -> float:
    coeffs = list(values)
    bin_width = math.ceil(KYBER_Q / bins)
    counts = [0 for _ in range(bins)]
    for value in coeffs:
        idx = min(value // bin_width, bins - 1)
        counts[idx] += 1
    expected = len(coeffs) / bins
    return sum(((count - expected) ** 2) / expected for count in counts)


def verify_once(seed: int) -> None:
    rng = random.Random(seed)
    coeffs = [rng.randrange(KYBER_Q) for _ in range(KYBER_N)]

    words = pack_words(coeffs)
    write_hex(NTT_INPUT, words)

    expected_ntt = ntt(coeffs)
    build_tb(
        "ntt_tb",
        [
            NTT_DIR / "kyber_ntt.v",
            NTT_DIR / "kyber_intt.v",
            NTT_DIR / "zetas_rom.v",
            TEST_DIR / "ntt_tb.v",
        ],
        BUILD_DIR / "ntt_tb.out",
    )
    run_vvp(BUILD_DIR / "ntt_tb.out", TEST_DIR)
    hw_ntt_words = read_hex(NTT_OUTPUT)
    hw_ntt = unpack_words(hw_ntt_words)
    if hw_ntt != expected_ntt:
        raise AssertionError("NTT hardware result mismatch")

    write_hex(INTT_INPUT, pack_words(expected_ntt))
    expected_intt = intt(expected_ntt)
    build_tb(
        "intt_tb",
        [
            NTT_DIR / "kyber_ntt.v",
            NTT_DIR / "kyber_intt.v",
            NTT_DIR / "zetas_rom.v",
            TEST_DIR / "intt_tb.v",
        ],
        BUILD_DIR / "intt_tb.out",
    )
    run_vvp(BUILD_DIR / "intt_tb.out", TEST_DIR)
    hw_intt_words = read_hex(INTT_OUTPUT)
    hw_intt = unpack_words(hw_intt_words)
    if hw_intt != expected_intt:
        raise AssertionError("INTT hardware result mismatch")

    recovered = [x % KYBER_Q for x in coeffs]
    if hw_intt != recovered:
        raise AssertionError("Inverse transform failed to recover coefficients")

    chi_val = chi_square(coeffs)
    print(f"Seed {seed}: chi-square statistic for input coefficients = {chi_val:.2f}")


def main() -> int:
    ensure_build_dir()
    seeds = [1, 7, 42]
    for seed in seeds:
        verify_once(seed)
    print("All NTT/INTT hardware checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
