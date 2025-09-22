"""
@Descripttion: SPHINCS+ Stage-6 演示脚本
@version: V0.6
@Author: GoldenModel-Team
@Date: 2025-04-05 12:00
"""

from __future__ import annotations

from SPHINCS_plus import KeyGen, Sign, Verify
from sphincs_params import get_params


def main() -> None:
    """展示 Stage-6 端到端 KeyGen/Sign/Verify 流程（覆盖 L1/L3/L5）。"""

    for level in (1, 3, 5):
        params = get_params(level=level)
        n = int(params["n"])
        tree_height = int(params["tree_height"])
        d = int(params["d"])
        fors_height = int(params["fors_height"])
        fors_trees = int(params["fors_trees"])
        wots_len = int(params["len"]) * n

        print(f"[Stage6] parameter set: {params['name']} (L{level})")
        print(
            f"  n={n}, full_height={params['full_height']}, d={d}, tree_height={tree_height}"
        )
        print(
            f"  FORS: trees={fors_trees}, height={fors_height}; WOTS len={params['len']}"
        )

        seed = bytes((i % 256) for i in range(3 * n))
        message = f"Stage6 demo message L{level}".encode("utf-8")

        pk, sk = KeyGen(params, seed=seed)
        signature = Sign(sk, message, params)
        verified = Verify(pk, message, signature, params)

        fors_sig_len = fors_trees * (fors_height + 1) * n
        auth_path_len = tree_height * n
        sig_len = len(signature)
        print(f"  public key seed: {pk['seed'].hex()}")
        print(f"  public root: {pk['root'].hex()}")
        print(f"  signature length: {sig_len} bytes")
        print(f"    R: {n} bytes")
        print(f"    FORS: {fors_sig_len} bytes")
        print(f"    WOTS per layer: {wots_len} bytes")
        print(f"    auth path per layer: {auth_path_len} bytes")
        print("  verification:", "success" if verified else "failed")
        print()


if __name__ == "__main__":
    main()
