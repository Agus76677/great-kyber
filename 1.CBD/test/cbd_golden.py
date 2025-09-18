#!/usr/bin/env python3
"""CBD sampler golden model and verification utilities.

This script serves two purposes:

1. Generate stimulus vectors for the hardware testbench together with the
   corresponding golden results computed in software.
2. Verify that the hardware output produced by the Verilog testbench matches
   the expected results and perform a basic chi-squared goodness of fit test on
   the accepted samples.
"""

import argparse
import pathlib
import random
from collections import Counter

LANES = 4
RAND_WIDTH = 128
ETA = 3
CAND_BITS = 4
BERN_WIDTH = 8
REJ_WIDTH = 8
BASE_LIMIT = 200
SHIFT_FACTOR = 4

INPUT_FILE = pathlib.Path(__file__).with_name("cbd_input.txt")
EXPECTED_FILE = pathlib.Path(__file__).with_name("cbd_expected.txt")
HW_OUTPUT_FILE = pathlib.Path(__file__).with_name("hw_output.txt")

print(f"当前工作目录: {pathlib.Path.cwd()}")
print(f"脚本所在目录: {pathlib.Path(__file__).parent}")
print(f"输入文件绝对路径: {INPUT_FILE.absolute()}")

def generate_vectors(vectors: int, seed: int) -> None:
    print(f"开始生成 {vectors} 个向量，种子: {seed}")
    print(f"输入文件路径: {INPUT_FILE}")
    print(f"期望文件路径: {EXPECTED_FILE}")
    rng = random.Random(seed)
    max_rand = 1 << RAND_WIDTH
    with INPUT_FILE.open("w", encoding="utf-8") as input_fp, EXPECTED_FILE.open(
        "w", encoding="utf-8"
    ) as expected_fp:
        input_fp.write(f"{vectors}\n")
        for _ in range(vectors):
            threshold = rng.randrange(1 << BERN_WIDTH)
            random_value = rng.randrange(max_rand)
            input_fp.write(f"{threshold:02x} {random_value:032x}\n")
            accept_mask, sample_value = compute_lane_outputs(threshold, random_value)
            expected_fp.write(f"{accept_mask:0{LANES // 4 + (1 if LANES % 4 else 0)}x} {sample_value:0{(LANES*CAND_BITS + 3)//4}x}\n")


def compute_lane_outputs(threshold: int, random_value: int) -> tuple[int, int]:
    lane_width = RAND_WIDTH // LANES
    accept_mask = 0
    packed_samples = 0
    for lane in range(LANES):
        lane_slice = (random_value >> (lane * lane_width)) & ((1 << lane_width) - 1)
        sample, accepted = cbd_lane_model(threshold, lane_slice)
        if accepted:
            accept_mask |= 1 << lane
        packed_samples |= (sample & ((1 << CAND_BITS) - 1)) << (lane * CAND_BITS)
    return accept_mask, packed_samples


def cbd_lane_model(threshold: int, lane_random: int) -> tuple[int, bool]:
    mask_eta = (1 << ETA) - 1
    a_bits = lane_random & mask_eta
    b_bits = (lane_random >> ETA) & mask_eta
    bern_random = (lane_random >> (2 * ETA)) & ((1 << BERN_WIDTH) - 1)
    rej_random = (lane_random >> (2 * ETA + BERN_WIDTH)) & ((1 << REJ_WIDTH) - 1)

    count_a = bin(a_bits).count("1")
    count_b = bin(b_bits).count("1")
    diff = count_a - count_b
    signed_value = diff if bern_random < threshold else -diff
    magnitude = abs(signed_value)

    dynamic_limit = BASE_LIMIT - (magnitude << SHIFT_FACTOR)
    if dynamic_limit < 0:
        dynamic_limit = 0
    accept = rej_random < (dynamic_limit & ((1 << REJ_WIDTH) - 1))

    # Convert to two's complement representation within CAND_BITS bits
    mask = (1 << CAND_BITS) - 1
    sample_encoded = signed_value & mask
    return sample_encoded, accept


def verify_results() -> None:
    if not EXPECTED_FILE.exists():
        raise FileNotFoundError("Expected results missing, run with --generate first")
    if not HW_OUTPUT_FILE.exists():
        raise FileNotFoundError("Hardware output missing, run the simulator first")

    expected_lines = EXPECTED_FILE.read_text(encoding="utf-8").strip().splitlines()
    hw_lines = HW_OUTPUT_FILE.read_text(encoding="utf-8").strip().splitlines()

    if len(expected_lines) != len(hw_lines):
        raise ValueError(
            f"Line count mismatch between expected ({len(expected_lines)}) and hardware ({len(hw_lines)})"
        )

    mismatches = []
    accepted_samples = []

    for idx, (exp_line, hw_line) in enumerate(zip(expected_lines, hw_lines)):
        exp_accept_hex, exp_sample_hex = exp_line.split()
        hw_accept_hex, hw_sample_hex = hw_line.split()
        if exp_accept_hex.lower() != hw_accept_hex.lower() or exp_sample_hex.lower() != hw_sample_hex.lower():
            mismatches.append((idx, exp_line, hw_line))
        accept_mask = int(hw_accept_hex, 16)
        sample_value = int(hw_sample_hex, 16)
        accepted_samples.extend(extract_samples(accept_mask, sample_value))

    if mismatches:
        mismatch_str = "\n".join(
            f"Vector {idx}: expected {exp} got {hw}" for idx, exp, hw in mismatches
        )
        raise AssertionError(f"Hardware results mismatch expected values:\n{mismatch_str}")

    if not accepted_samples:
        raise AssertionError("No accepted samples produced by the hardware")

    distribution_summary(accepted_samples)


def extract_samples(accept_mask: int, packed_samples: int) -> list[int]:
    samples = []
    mask = (1 << CAND_BITS) - 1
    for lane in range(LANES):
        if accept_mask & (1 << lane):
            value = packed_samples >> (lane * CAND_BITS)
            decoded = twos_complement(value & mask, CAND_BITS)
            samples.append(decoded)
    return samples


def twos_complement(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    return (value ^ sign_bit) - sign_bit


def distribution_summary(samples: list[int]) -> None:
    counts = Counter(samples)
    total = sum(counts.values())
    pmf = cbd_pmf(ETA)
    chi2 = 0.0
    for value, probability in pmf.items():
        expected = probability * total
        observed = counts.get(value, 0)
        if expected > 0:
            chi2 += ((observed - expected) ** 2) / expected
    print("Accepted sample distribution summary:")
    for value in sorted(pmf):
        observed = counts.get(value, 0)
        probability = pmf[value]
        print(
            f"  value {value:2d}: observed {observed:5d} ({observed/total:6.3%}), expected {probability:6.3%}"
        )
    dof = len(pmf) - 1
    print(f"Chi-squared statistic: {chi2:.3f} with {dof} degrees of freedom")
    mean = sum(value * count for value, count in counts.items()) / total
    variance = sum((value ** 2) * count for value, count in counts.items()) / total - mean ** 2
    print(f"Sample mean: {mean:.4f}, variance: {variance:.4f}")


def cbd_pmf(eta: int) -> dict[int, float]:
    pmf = Counter()
    for a in range(1 << eta):
        pop_a = bin(a).count("1")
        for b in range(1 << eta):
            pop_b = bin(b).count("1")
            diff = pop_a - pop_b
            pmf[diff] += 1
    total = 1 << (2 * eta)
    for key in list(pmf.keys()):
        pmf[key] /= total
    return dict(pmf)


def main() -> None:
    parser = argparse.ArgumentParser(description="CBD sampler golden model")
    parser.add_argument("--vectors", type=int, default=64, help="Number of stimulus vectors")
    parser.add_argument("--seed", type=int, default=2024, help="PRNG seed for reproducibility")
    parser.add_argument("--generate", action="store_true", help="Generate stimulus and expected results")
    parser.add_argument("--verify", action="store_true", help="Verify hardware output and report statistics")
    args = parser.parse_args()

    # 如果没有指定任何操作，默认执行生成操作
    if not args.generate and not args.verify:
        args.generate = True  # 默认生成
    
    if args.generate:
        generate_vectors(args.vectors, args.seed)
        print(f"Generated {args.vectors} vectors and golden results using seed {args.seed}.")

    if args.verify:
        verify_results()
        print("Hardware output matches golden model.")

if __name__ == "__main__":
    main()
