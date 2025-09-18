"""Golden model and stimulus generator for the uniform_sampler module."""
from __future__ import annotations

import random
from pathlib import Path

LANES = 8
CAND_BITS = 16
Q_BITS = 16
BARRETT_WIDTH = CAND_BITS + Q_BITS
FLOOR_WIDTH = CAND_BITS + 1
NUM_ACTIVE = 64
LATENCY = 4
EXTRA_CYCLES = LATENCY + 2
TOTAL_CYCLES = NUM_ACTIVE + EXTRA_CYCLES
MASK_CAND = (1 << CAND_BITS) - 1
EXT_WIDTH = CAND_BITS + Q_BITS + 1

DATA_DIR = Path(__file__).resolve().parent / "data"


def compute_barrett_mu(q_val: int) -> int:
    if q_val == 0:
        return 0
    numerator = 1 << BARRETT_WIDTH
    return numerator // q_val


def compute_floor_factor(q_val: int) -> int:
    if q_val == 0:
        return 0
    numerator = 1 << CAND_BITS
    return numerator // q_val


def barrett_reduce(value: int, q_val: int, mu_val: int) -> int:
    if q_val == 0:
        return 0
    product = value * mu_val
    approx = product >> BARRETT_WIDTH
    approx_mul = approx * q_val
    value_ext = value
    if value_ext < approx_mul:
        value_ext += q_val
        if value_ext < approx_mul:
            value_ext += q_val
    corrected = value_ext - approx_mul
    if corrected >= q_val:
        corrected -= q_val
        if corrected >= q_val:
            corrected -= q_val
    return corrected & MASK_CAND


def generate_vectors(seed: int = 2024) -> None:
    random.seed(seed)
    inputs: list[tuple[int, int]] = []
    for _ in range(NUM_ACTIVE):
        rnd = random.getrandbits(128)
        q_val = random.randint(1, (1 << Q_BITS) - 1)
        inputs.append((rnd, q_val))

    random_stream: list[int] = []
    q_stream: list[int] = []
    valid_stream: list[int] = []
    for cycle in range(TOTAL_CYCLES):
        if cycle < NUM_ACTIVE:
            rnd, q_val = inputs[cycle]
            valid_stream.append(1)
        else:
            rnd, q_val = (0, 1)
            valid_stream.append(0)
        random_stream.append(rnd)
        q_stream.append(q_val)

    expected_vals: list[int] = []
    expected_valid: list[int] = []
    expected_retry: list[int] = []
    for cycle in range(TOTAL_CYCLES):
        if cycle < LATENCY:
            expected_vals.append(0)
            expected_valid.append(0)
            expected_retry.append(0)
            continue

        idx = cycle - LATENCY
        if idx >= NUM_ACTIVE:
            expected_vals.append(0)
            expected_valid.append(0)
            expected_retry.append(0)
            continue

        rnd, q_val = inputs[idx]
        mu_val = compute_barrett_mu(q_val)
        floor_val = compute_floor_factor(q_val)
        threshold = q_val * floor_val

        lane_value = 0
        valid_mask = 0
        retry_mask = 0
        for lane in range(LANES):
            candidate = (rnd >> (lane * CAND_BITS)) & MASK_CAND
            reduced = 0
            accept = 0
            retry = 0
            if q_val != 0:
                reduced = barrett_reduce(candidate, q_val, mu_val)
                if floor_val != 0 and candidate < threshold:
                    accept = 1
                elif floor_val != 0:
                    retry = 1
                else:
                    retry = 1
            if accept:
                lane_value |= (reduced & MASK_CAND) << (lane * CAND_BITS)
                valid_mask |= 1 << lane
            elif retry:
                retry_mask |= 1 << lane
        expected_vals.append(lane_value)
        expected_valid.append(valid_mask)
        expected_retry.append(retry_mask)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "random_in.mem").write_text("\n".join(f"{val:032x}" for val in random_stream) + "\n")
    (DATA_DIR / "q.mem").write_text("\n".join(f"{val:04x}" for val in q_stream) + "\n")
    (DATA_DIR / "random_valid.mem").write_text("\n".join(str(val) for val in valid_stream) + "\n")
    (DATA_DIR / "expected_vals.mem").write_text(
        "\n".join(f"{val:0{LANES * CAND_BITS // 4}x}" for val in expected_vals) + "\n"
    )
    (DATA_DIR / "expected_valid.mem").write_text(
        "\n".join(f"{val:0{(LANES + 3) // 4}x}" for val in expected_valid) + "\n"
    )
    (DATA_DIR / "expected_retry.mem").write_text(
        "\n".join(f"{val:0{(LANES + 3) // 4}x}" for val in expected_retry) + "\n"
    )


if __name__ == "__main__":
    generate_vectors()
