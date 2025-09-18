"""Python golden model for the rejection sampler core."""

import argparse
import pathlib
import random
from dataclasses import dataclass
from typing import List

LANES = 4
CAND_BITS = 12
VECTORS = 80
Q_VALUE = 3329  # Kyber modulus for uniform sampling

VECTOR_PATH = pathlib.Path("3.REJECT/test/reject_vectors.txt")
HW_OUTPUT_PATH = pathlib.Path("3.REJECT/test/hw_output.txt")

random.seed(2024)


@dataclass
class Stimulus:
    random_valid: int
    q: int
    cand: List[int]
    urnd: List[int]
    threshold: List[int]
    mode: List[int]
    random_in: int


@dataclass
class StageState:
    cand: List[int]
    urnd: List[int]
    threshold: List[int]
    mode: List[int]
    q: int


@dataclass
class PipelineRegs:
    stage0: StageState
    stage1: StageState
    random_valid_d0: int
    random_valid_d1: int


def default_stage() -> StageState:
    return StageState([0] * LANES, [0] * LANES, [0] * LANES, [0] * LANES, 0)


def generate_vectors() -> List[Stimulus]:
    vectors: List[Stimulus] = []
    for _ in range(VECTORS):
        random_valid = random.randint(0, 1)
        cand = [random.randrange(0, 1 << CAND_BITS) for _ in range(LANES)]
        urnd = [random.randrange(0, 1 << CAND_BITS) for _ in range(LANES)]
        threshold = [random.randrange(0, 1 << CAND_BITS) for _ in range(LANES)]
        mode = [random.randint(0, 1) for _ in range(LANES)]
        random_in = random.getrandbits(128)
        vectors.append(
            Stimulus(
                random_valid=random_valid,
                q=Q_VALUE,
                cand=cand,
                urnd=urnd,
                threshold=threshold,
                mode=mode,
                random_in=random_in,
            )
        )
    return vectors


def write_vector_file(vectors: List[Stimulus]) -> None:
    with VECTOR_PATH.open("w", encoding="utf-8") as f:
        for item in vectors:
            packed_cand = sum(
                value << (idx * CAND_BITS) for idx, value in enumerate(item.cand)
            )
            packed_urnd = sum(
                value << (idx * CAND_BITS) for idx, value in enumerate(item.urnd)
            )
            packed_threshold = sum(
                value << (idx * CAND_BITS) for idx, value in enumerate(item.threshold)
            )
            packed_mode = sum(bit << idx for idx, bit in enumerate(item.mode))
            f.write(
                f"{item.random_valid} {item.q:04x} {packed_cand:0{LANES*CAND_BITS//4}x} "
                f"{packed_urnd:0{LANES*CAND_BITS//4}x} {packed_threshold:0{LANES*CAND_BITS//4}x} "
                f"{packed_mode:0{LANES//4+1}x} {item.random_in:032x}\n"
            )


def simulate_pipeline(vectors: List[Stimulus]) -> List[dict]:
    regs = PipelineRegs(default_stage(), default_stage(), 0, 0)
    outputs: List[dict] = []

    for item in vectors:
        # Output corresponds to stage1 registers and delayed valid signal.
        accept_flags = []
        for lane in range(LANES):
            if regs.stage1.mode[lane]:
                accept = regs.stage1.urnd[lane] < regs.stage1.threshold[lane]
            else:
                accept = regs.stage1.cand[lane] < regs.stage1.q
            accept_flags.append(1 if (accept and regs.random_valid_d1) else 0)

        sample_values = [regs.stage1.cand[lane] if accept_flags[lane] else 0 for lane in range(LANES)]
        sample_valid = 1 if regs.random_valid_d1 else 0
        packed_sample = sum(value << (lane * CAND_BITS) for lane, value in enumerate(sample_values))
        packed_accept = sum(flag << lane for lane, flag in enumerate(accept_flags))
        outputs.append({"accept": packed_accept, "sample": packed_sample, "valid": sample_valid})

        # Sequential updates (stage1 gets previous stage0, valid shifts)
        prev_stage0 = regs.stage0
        prev_random_valid_d0 = regs.random_valid_d0

        regs.stage1 = StageState(
            prev_stage0.cand[:],
            prev_stage0.urnd[:],
            prev_stage0.threshold[:],
            prev_stage0.mode[:],
            prev_stage0.q,
        )
        regs.random_valid_d1 = prev_random_valid_d0

        # Update stage0 only when random_valid asserted
        if item.random_valid:
            regs.stage0 = StageState(
                item.cand[:],
                item.urnd[:],
                item.threshold[:],
                item.mode[:],
                item.q,
            )
        regs.random_valid_d0 = item.random_valid

    # Final drain cycle
    accept_flags = []
    for lane in range(LANES):
        if regs.stage1.mode[lane]:
            accept = regs.stage1.urnd[lane] < regs.stage1.threshold[lane]
        else:
            accept = regs.stage1.cand[lane] < regs.stage1.q
        accept_flags.append(1 if (accept and regs.random_valid_d1) else 0)
    sample_values = [regs.stage1.cand[lane] if accept_flags[lane] else 0 for lane in range(LANES)]
    sample_valid = 1 if regs.random_valid_d1 else 0
    packed_sample = sum(value << (lane * CAND_BITS) for lane, value in enumerate(sample_values))
    packed_accept = sum(flag << lane for lane, flag in enumerate(accept_flags))
    outputs.append({"accept": packed_accept, "sample": packed_sample, "valid": sample_valid})

    return outputs


def verify_outputs(vectors: List[Stimulus]) -> None:
    if not HW_OUTPUT_PATH.exists():
        raise FileNotFoundError("Hardware output file was not produced")

    expected = simulate_pipeline(vectors)
    with HW_OUTPUT_PATH.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < len(expected):
        raise AssertionError("Hardware output file has fewer entries than expected")

    for idx, (line, exp) in enumerate(zip(lines, expected)):
        _, acc_hex, sample_hex, valid_str = line.split()
        hw_accept = int(acc_hex)
        hw_sample = int(sample_hex, 16)
        hw_valid = int(valid_str)

        if hw_accept != exp["accept"] or hw_sample != exp["sample"] or hw_valid != exp["valid"]:
            raise AssertionError(
                f"Mismatch at line {idx}: HW=(acc={hw_accept}, sample=0x{hw_sample:x}, valid={hw_valid}) "
                f"Expected=(acc={exp['accept']}, sample=0x{exp['sample']:x}, valid={exp['valid']})"
            )
    print("Hardware outputs match the golden model.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rejection sampler golden model")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify hardware output against the golden model using the existing vectors.",
    )
    args = parser.parse_args()

    if args.verify:
        if not VECTOR_PATH.exists():
            raise FileNotFoundError("Vector file missing. Generate vectors before verification.")
        vectors = []
        with VECTOR_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                fields = line.strip().split()
                random_valid = int(fields[0])
                q_val = int(fields[1], 16)
                packed_cand = int(fields[2], 16)
                packed_urnd = int(fields[3], 16)
                packed_threshold = int(fields[4], 16)
                packed_mode = int(fields[5], 16)
                random_in = int(fields[6], 16)
                cand = [(packed_cand >> (idx * CAND_BITS)) & ((1 << CAND_BITS) - 1) for idx in range(LANES)]
                urnd = [(packed_urnd >> (idx * CAND_BITS)) & ((1 << CAND_BITS) - 1) for idx in range(LANES)]
                threshold = [
                    (packed_threshold >> (idx * CAND_BITS)) & ((1 << CAND_BITS) - 1)
                    for idx in range(LANES)
                ]
                mode = [(packed_mode >> idx) & 1 for idx in range(LANES)]
                vectors.append(
                    Stimulus(
                        random_valid=random_valid,
                        q=q_val,
                        cand=cand,
                        urnd=urnd,
                        threshold=threshold,
                        mode=mode,
                        random_in=random_in,
                    )
                )
        verify_outputs(vectors)
    else:
        vectors = generate_vectors()
        write_vector_file(vectors)
        print("Vector file generated. Run the Verilog simulation next.")


if __name__ == "__main__":
    main()
