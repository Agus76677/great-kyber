import random
from typing import List

Q = 3329
N = 256
GENERATOR = 3
OMEGA = pow(GENERATOR, (Q - 1) // N, Q)

stage_roots: List[int] = []
len_val = N // 2
while len_val >= 1:
    stage_roots.append(pow(OMEGA, N // (2 * len_val), Q))
    len_val //= 2

inv_stage_roots: List[int] = [pow(root, Q - 2, Q) for root in reversed(stage_roots)]
INV_N = pow(N, Q - 2, Q)

BARRETT_FACTOR = ((1 << 26) + Q // 2) // Q


def barrett_reduce(value: int) -> int:
    tmp = ((value * BARRETT_FACTOR) + (1 << 25)) >> 26
    reduced = value - tmp * Q
    if reduced < 0:
        reduced += Q
    if reduced >= Q:
        reduced -= Q
    return reduced


def mod_add(a: int, b: int) -> int:
    tmp = a + b
    if tmp >= Q:
        tmp -= Q
    return tmp


def mod_sub(a: int, b: int) -> int:
    tmp = a - b
    if tmp < 0:
        tmp += Q
    return tmp


def mod_mul(a: int, b: int) -> int:
    return barrett_reduce(a * b)


def ntt(poly: List[int]) -> List[int]:
    a = poly[:]
    len_val = N // 2
    stage = 0
    while len_val >= 1:
        root = stage_roots[stage]
        for start in range(0, N, 2 * len_val):
            w = 1
            for j in range(len_val):
                idx = start + j
                u = a[idx]
                v = mod_mul(a[idx + len_val], w)
                a[idx] = mod_add(u, v)
                a[idx + len_val] = mod_sub(u, v)
                w = mod_mul(w, root)
        len_val //= 2
        stage += 1
    return a


def intt(poly: List[int]) -> List[int]:
    a = poly[:]
    len_val = 1
    stage = 0
    while len_val < N:
        root = inv_stage_roots[stage]
        for start in range(0, N, 2 * len_val):
            w = 1
            for j in range(len_val):
                idx = start + j
                u = a[idx]
                v = a[idx + len_val]
                a[idx] = mod_add(u, v)
                t = mod_sub(u, v)
                a[idx + len_val] = mod_mul(t, w)
                w = mod_mul(w, root)
        len_val *= 2
        stage += 1
    for i in range(N):
        a[i] = mod_mul(a[i], INV_N)
    return a


def chunk_words(values: List[int]) -> List[int]:
    assert len(values) % 8 == 0
    words: List[int] = []
    for base in range(0, len(values), 8):
        word = 0
        for lane in range(8):
            word |= (values[base + lane] & 0xFFFF) << (16 * lane)
        words.append(word)
    return words


def main() -> None:
    random.seed(2025)
    num_tests = 4
    input_words: List[int] = []
    ntt_words: List[int] = []
    intt_words: List[int] = []

    for _ in range(num_tests):
        poly = [random.randrange(Q) for _ in range(N)]
        ntt_res = ntt(poly)
        intt_res = intt(ntt_res)
        assert intt_res == [x % Q for x in poly]
        input_words.extend(chunk_words(poly))
        ntt_words.extend(chunk_words(ntt_res))
        intt_words.extend(chunk_words(intt_res))

    def write_hex(path: str, data: List[int]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for word in data:
                f.write(f"{word:032x}\n")

    write_hex("5.NTT/test/input_poly.hex", input_words)
    write_hex("5.NTT/test/ntt_expected.hex", ntt_words)
    write_hex("5.NTT/test/intt_expected.hex", intt_words)

    # store reference constants for documentation/debugging
    with open("5.NTT/test/stage_roots.txt", "w", encoding="utf-8") as f:
        f.write("Forward stage roots:\n")
        f.write(", ".join(str(x) for x in stage_roots) + "\n")
        f.write("Inverse stage roots:\n")
        f.write(", ".join(str(x) for x in inv_stage_roots) + "\n")


if __name__ == "__main__":
    main()
