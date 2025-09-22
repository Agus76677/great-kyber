import random
from pathlib import Path

LANES = 8
CAND_BITS = 16
INPUT_WIDTH = LANES * CAND_BITS
SHIFT = 2 * CAND_BITS
BARRETT_BASE = 1 << SHIFT
CAND_BASE = 1 << CAND_BITS
VECTORS = 64

random.seed(2024)

root = Path(__file__).parent
rand_path = root / "random_vectors.hex"
q_path = root / "q_values.hex"
exp_path = root / "expected_samples.hex"
acc_path = root / "expected_accept.hex"

with rand_path.open("w", encoding="utf-8") as rand_file, \
        q_path.open("w", encoding="utf-8") as q_file, \
        exp_path.open("w", encoding="utf-8") as exp_file, \
        acc_path.open("w", encoding="utf-8") as acc_file:
    for _ in range(VECTORS):
        q_val = random.randint(2, 2 ** 16 - 1)
        random_value = random.getrandbits(INPUT_WIDTH)
        q_inv = (BARRETT_BASE + q_val - 1) // q_val
        limit = ((CAND_BASE // q_val) * q_val) - 1
        if limit < 0:
            limit = 0

        lanes = []
        accept_mask = 0
        for lane in range(LANES):
            cand = (random_value >> (lane * CAND_BITS)) & ((1 << CAND_BITS) - 1)
            prod = cand * q_inv
            quotient = prod >> SHIFT
            reduced = cand - quotient * q_val
            while reduced < 0:
                reduced += q_val
            while reduced >= q_val:
                reduced -= q_val
            lanes.append(reduced)
            if cand <= limit:
                accept_mask |= 1 << lane

        sample_word = 0
        for lane in range(LANES - 1, -1, -1):
            sample_word = (sample_word << CAND_BITS) | (lanes[lane] & ((1 << CAND_BITS) - 1))

        rand_file.write(f"{random_value:032x}\n")
        q_file.write(f"{q_val:04x}\n")
        exp_file.write(f"{sample_word:032x}\n")
        acc_file.write(f"{accept_mask:02x}\n")
