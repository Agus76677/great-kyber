"""
@Descripttion: SPHINCS+ Stage-4 演示脚本
@version: V0.5
@Author: GoldenModel-Team
@Date: 2025-03-30 12:00
"""

from __future__ import annotations

from SPHINCS_plus import KeyGen, Sign, Verify
from sphincs_params import get_params


def main() -> None:
    """展示 Stage-4 端到端 KeyGen/Sign/Verify 流程。"""

    params = get_params()
    n = int(params["n"])
    tree_height = int(params["tree_height"])
    d = int(params["d"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    wots_len = int(params["len"]) * n

    print("[SPHINCS+ Stage4] parameter set:", params["name"])
    print(f"n={n}, full_height={params['full_height']}, d={d}, tree_height={tree_height}")
    print(f"FORS: trees={fors_trees}, height={fors_height}; WOTS len={params['len']}")

    seed_hex = "00112233445566778899aabbccddeeff" * 3
    seed = bytes.fromhex(seed_hex)
    message = b"Stage4 end-to-end demo message"

    pk, sk = KeyGen(params, seed=seed)
    signature = Sign(sk, message, params)
    verified = Verify(pk, message, signature, params)

    fors_sig_len = fors_trees * (fors_height + 1) * n
    auth_path_len = tree_height * n
    sig_len = len(signature)
    print(f"public key seed: {pk['seed'].hex()}")
    print(f"public root: {pk['root'].hex()}")
    print(f"signature length: {sig_len} bytes")
    print(f"  R: {n} bytes")
    print(f"  FORS: {fors_sig_len} bytes")
    print(f"  WOTS per layer: {wots_len} bytes")
    print(f"  auth path per layer: {auth_path_len} bytes")
    print("verification:", "success" if verified else "failed")


if __name__ == "__main__":
    main()
