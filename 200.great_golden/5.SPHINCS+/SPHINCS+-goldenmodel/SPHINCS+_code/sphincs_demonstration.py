"""
@Descripttion: SPHINCS+ Stage-6 演示脚本
@version: V0.6
@Author: GoldenModel-Team
@Date: 2025-04-05 12:00
"""

from __future__ import annotations

from SPHINCS_plus import KeyGen, Sign, Verify
from sphincs_params import get_params


def _signature_breakdown(params: dict[str, int | str], signature: bytes) -> None:
    n = int(params["n"])
    tree_height = int(params["tree_height"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    wots_len = int(params["len"]) * n
    fors_sig_len = fors_trees * (fors_height + 1) * n
    auth_path_len = tree_height * n
    sig_len = len(signature)
    print(f"signature length: {sig_len} bytes")
    print(f"  R: {n} bytes")
    print(f"  FORS: {fors_sig_len} bytes")
    print(f"  WOTS per layer: {wots_len} bytes")
    print(f"  auth path per layer: {auth_path_len} bytes")


def main() -> None:
    """展示 Stage-6 端到端 KeyGen/Sign/Verify 流程，并遍历三种安全等级。"""

    for level in (1, 3, 5):
        params = get_params(level=level)
        n = int(params["n"])
        tree_height = int(params["tree_height"])
        d = int(params["d"])
        fors_height = int(params["fors_height"])
        fors_trees = int(params["fors_trees"])
        message = f"Stage6 demo message L{level}".encode()
        seed = bytes(range(3 * n))

        print("=" * 60)
        print(f"[SPHINCS+ Stage6] parameter set: {params['name']} (Level-{level})")
        print(f"n={n}, full_height={params['full_height']}, d={d}, tree_height={tree_height}")
        print(f"FORS: trees={fors_trees}, height={fors_height}; WOTS len={params['len']}")

        pk, sk = KeyGen(params, seed=seed)
        signature = Sign(sk, message, params)
        verified = Verify(pk, message, signature, params)

        print(f"public key seed: {pk['seed'].hex()}")
        print(f"public root: {pk['root'].hex()}")
        _signature_breakdown(params, signature)
        print("verification:", "success" if verified else "failed")


if __name__ == "__main__":
    main()
