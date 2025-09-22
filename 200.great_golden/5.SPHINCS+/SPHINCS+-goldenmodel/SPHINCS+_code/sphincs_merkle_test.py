"""
@Descripttion: SPHINCS+ Merkle 工具测试（Stage-4）
@version: V0.4
@Author: GoldenModel-Team
@Date: 2025-03-30 12:00
"""

from __future__ import annotations

import pytest

from sphincs_merkle import compute_root_from_auth_path, compute_subtree_authentication
from sphincs_params import get_params
from sphincs_utils import derive_tree_hash_address


def _leaf_factory(value: int, n: int) -> bytes:
    return value.to_bytes(n, "big")


def test_merkle_auth_path_roundtrip() -> None:
    params = get_params()
    n = int(params["n"])
    pub_seed = bytes(range(n))
    tree_addr = derive_tree_hash_address(0, 0, 0, 0)
    tree_height = 4
    leaf_idx = 6

    def leaf_func(idx: int, _addr) -> bytes:
        return _leaf_factory(idx, n)

    auth_path, root = compute_subtree_authentication(
        params,
        pub_seed,
        tree_addr,
        leaf_idx,
        tree_height,
        leaf_func,
    )
    assert len(auth_path) == tree_height
    leaf_value = leaf_func(leaf_idx, None)
    recovered = compute_root_from_auth_path(
        params,
        leaf_value,
        leaf_idx,
        auth_path,
        pub_seed,
        tree_addr,
    )
    assert recovered == root


def test_merkle_invalid_index() -> None:
    params = get_params()
    pub_seed = bytes(int(params["n"]))
    tree_addr = derive_tree_hash_address(0, 0, 0, 0)

    with pytest.raises(ValueError):
        compute_subtree_authentication(
            params,
            pub_seed,
            tree_addr,
            leaf_idx=8,
            tree_height=2,
            leaf_func=lambda _idx, _addr: b"".ljust(int(params["n"]), b"\x00"),
        )
