#!/usr/bin/env python3
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MESSAGE = bytes(range(32))

TARGET_OUTPUTS = {
    "shake128": {
        "mode": "shake_128",
        "length": 32,
        "file": ROOT / "shake128_output.hex",
    },
    "shake256": {
        "mode": "shake_256",
        "length": 32,
        "file": ROOT / "shake256_output.hex",
    },
}


def load_output(path, length):
    data = bytearray()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        data.append(int(line, 16))
    if len(data) < length:
        raise ValueError(f"Output {path} shorter than expected length {length} (got {len(data)})")
    return bytes(data[:length])


def chi_square_statistic(data: bytes) -> float:
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    expected = len(data) / 256.0
    if expected == 0:
        return 0.0
    total = 0.0
    for count in counts:
        diff = count - expected
        total += (diff * diff) / expected
    return total


def run_test():
    success = True
    for name, cfg in TARGET_OUTPUTS.items():
        mode = cfg["mode"]
        length = cfg["length"]
        output_file = cfg["file"]
        if mode == "shake_128":
            expected = hashlib.shake_128(MESSAGE).digest(length)
        else:
            expected = hashlib.shake_256(MESSAGE).digest(length)

        if not output_file.exists():
            raise FileNotFoundError(f"Missing simulation output file: {output_file}")
        observed = load_output(output_file, length)

        if observed != expected:
            print(f"[FAIL] {name}: output mismatch")
            print(f"Expected: {expected.hex()}")
            print(f"Observed: {observed.hex()}")
            success = False
        else:
            print(f"[PASS] {name}: output matches Python hashlib reference")

        chi2 = chi_square_statistic(observed)
        mean = 255.0
        sigma = math.sqrt(2 * 255.0)
        lower = mean - 3 * sigma
        upper = mean + 3 * sigma
        if chi2 < lower or chi2 > upper:
            print(f"[WARN] {name}: chi-square statistic {chi2:.2f} outside 3-sigma band [{lower:.2f}, {upper:.2f}]")
        else:
            print(f"[INFO] {name}: chi-square statistic {chi2:.2f} within expected range")

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    run_test()
