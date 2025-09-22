"""
@Descripttion: SPHINCS+ 主流程实现（Stage-4 版本）
@version: V0.4
@Author: GoldenModel-Team
@Date: 2025-03-30 12:00

实现 SHA256 Level-1 参数下的确定性 KeyGen/Sign/Verify 流程，
复用 Stage 1~3 已完成的哈希、地址与基元模块。
"""

from __future__ import annotations

import secrets
from typing import Dict, Iterable, List, Mapping, Tuple

from auxiliary_function import ADDR_TYPE_WOTSPK, concat_bytes, ensure_bytes
from sphincs_fors import fors_pk_from_sig, fors_sign
from sphincs_hash import H_msg, PRF_msg
from sphincs_merkle import (
    compute_root_from_auth_path,
    compute_subtree_authentication,
    compute_subtree_root,
    l_tree,
)
from sphincs_utils import bind_address_type, derive_fors_tree_address, derive_tree_hash_address, derive_wots_address
from sphincs_wots import wots_gen_pk, wots_pk_from_sig, wots_sign

Params = Mapping[str, int | str]
PublicKey = Dict[str, bytes]
SecretKey = Dict[str, bytes]


def _expand_seed(seed: bytes | None, n: int) -> Tuple[bytes, bytes, bytes]:
    """将外部种子拆分为 (sk_seed, sk_prf, pub_seed)。"""

    if seed is None:
        seed_material = secrets.token_bytes(3 * n)
    else:
        seed_material = ensure_bytes(seed)
        if len(seed_material) < 3 * n:
            raise ValueError("seed length must be at least 3n bytes")
        seed_material = seed_material[: 3 * n]
    return seed_material[:n], seed_material[n : 2 * n], seed_material[2 * n : 3 * n]


def _make_leaf_generator(
    params: Params,
    sk_seed: bytes,
    pub_seed: bytes,
    layer: int,
    tree_idx: int,
):
    """生成用于 Merkle 子树的叶节点闭包。"""

    def leaf_func(leaf_index: int, _leaf_addr: Iterable[int]) -> bytes:
        base_address = derive_wots_address(layer, tree_idx, leaf_index, 0, 0)
        wots_pk = wots_gen_pk(params, sk_seed, pub_seed, base_address)
        pk_address = bind_address_type(base_address, ADDR_TYPE_WOTSPK)
        return l_tree(params, pub_seed, pk_address, wots_pk)

    return leaf_func


def KeyGen(params: Params, seed: bytes | None = None) -> Tuple[PublicKey, SecretKey]:
    """
    生成 SPHINCS+ 公钥与密钥对（确定性，供 Stage-4 测试使用）。
    """

    n = int(params["n"])
    tree_height = int(params["tree_height"])
    d = int(params["d"])
    sk_seed, sk_prf, pub_seed = _expand_seed(seed, n)

    current_root = b"\x00" * n
    for layer in range(d):
        tree_addr = derive_tree_hash_address(layer, 0, 0, 0)
        leaf_generator = _make_leaf_generator(params, sk_seed, pub_seed, layer, 0)
        current_root = compute_subtree_root(
            params,
            pub_seed,
            tree_addr,
            tree_height,
            leaf_generator,
        )

    public_key: PublicKey = {"seed": pub_seed, "root": current_root}
    secret_key: SecretKey = {
        "sk_seed": sk_seed,
        "sk_prf": sk_prf,
        "pub_seed": pub_seed,
        "pub_root": current_root,
    }
    return public_key, secret_key


def Sign(
    secret_key: SecretKey,
    message: bytes,
    params: Params,
    *,
    optrand: bytes | None = None,
) -> bytes:
    """
    生成确定性 SPHINCS+ 签名（Stage-4：固定 optrand=0 以便回归测试）。
    """

    n = int(params["n"])
    tree_height = int(params["tree_height"])
    d = int(params["d"])

    sk_seed = ensure_bytes(secret_key["sk_seed"], length=n)
    sk_prf = ensure_bytes(secret_key["sk_prf"], length=n)
    pub_seed = ensure_bytes(secret_key["pub_seed"], length=n)
    pub_root = ensure_bytes(secret_key["pub_root"], length=n)

    opt_random = b"\x00" * n if optrand is None else ensure_bytes(optrand, length=n)
    randomness = PRF_msg(params, sk_prf, opt_random, message)
    pk_bytes = concat_bytes(pub_seed, pub_root)
    digest, tree_idx, leaf_idx = H_msg(params, randomness, pk_bytes, message)

    fors_address = derive_fors_tree_address(0, tree_idx, leaf_idx)
    fors_sig, fors_pk = fors_sign(params, digest, sk_seed, pub_seed, fors_address)

    signature_parts: List[bytes] = [randomness, fors_sig]
    current_root = fors_pk
    current_leaf = leaf_idx
    current_tree = tree_idx

    for layer in range(d):
        wots_address = derive_wots_address(layer, current_tree, current_leaf, 0, 0)
        wots_signature = wots_sign(params, current_root, sk_seed, pub_seed, wots_address)
        signature_parts.append(wots_signature)

        leaf_generator = _make_leaf_generator(params, sk_seed, pub_seed, layer, current_tree)
        tree_address = derive_tree_hash_address(layer, current_tree, 0, 0)
        auth_path, root = compute_subtree_authentication(
            params,
            pub_seed,
            tree_address,
            current_leaf,
            tree_height,
            leaf_generator,
        )
        signature_parts.extend(auth_path)
        current_root = root

        if layer < d - 1:
            next_leaf = current_tree & ((1 << tree_height) - 1)
            current_tree >>= tree_height
            current_leaf = next_leaf

    return b"".join(signature_parts)


def Verify(public_key: PublicKey, message: bytes, signature: bytes, params: Params) -> bool:
    """验证签名是否与给定公钥、消息匹配。"""

    n = int(params["n"])
    tree_height = int(params["tree_height"])
    d = int(params["d"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])

    pk_seed = ensure_bytes(public_key["seed"], length=n)
    pk_root = ensure_bytes(public_key["root"], length=n)
    sig_bytes = ensure_bytes(signature)

    wots_len = int(params["len"]) * n
    auth_len = tree_height * n
    fors_len = fors_trees * (fors_height + 1) * n
    expected_len = n + fors_len + d * (wots_len + auth_len)
    if len(sig_bytes) != expected_len:
        return False

    offset = 0
    randomness = sig_bytes[offset : offset + n]
    offset += n
    fors_sig = sig_bytes[offset : offset + fors_len]
    offset += fors_len

    pk_bytes = concat_bytes(pk_seed, pk_root)
    digest, tree_idx, leaf_idx = H_msg(params, randomness, pk_bytes, message)
    fors_address = derive_fors_tree_address(0, tree_idx, leaf_idx)
    fors_pk = fors_pk_from_sig(params, fors_sig, digest, pk_seed, fors_address)

    current_root = fors_pk
    current_leaf = leaf_idx
    current_tree = tree_idx

    for layer in range(d):
        wots_sig = sig_bytes[offset : offset + wots_len]
        offset += wots_len
        auth_path = [
            sig_bytes[offset + level * n : offset + (level + 1) * n]
            for level in range(tree_height)
        ]
        offset += auth_len

        wots_address = derive_wots_address(layer, current_tree, current_leaf, 0, 0)
        wots_pk = wots_pk_from_sig(params, wots_sig, current_root, pk_seed, wots_address)
        pk_address = bind_address_type(wots_address, ADDR_TYPE_WOTSPK)
        leaf = l_tree(params, pk_seed, pk_address, wots_pk)

        tree_address = derive_tree_hash_address(layer, current_tree, 0, 0)
        current_root = compute_root_from_auth_path(
            params,
            leaf,
            current_leaf,
            auth_path,
            pk_seed,
            tree_address,
        )

        if layer < d - 1:
            next_leaf = current_tree & ((1 << tree_height) - 1)
            current_tree >>= tree_height
            current_leaf = next_leaf

    return current_root == pk_root


__all__ = ["KeyGen", "Sign", "Verify"]
