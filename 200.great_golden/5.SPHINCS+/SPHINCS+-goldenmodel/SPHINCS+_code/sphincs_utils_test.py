"""
@Descripttion: SPHINCS+ 工具函数阶段三测试
@version: V0.3
@Author: GoldenModel-Team
@Date: 2025-03-25 12:00
"""

import random

from auxiliary_function import (
    ADDR_TYPE_FORSPK,
    ADDR_TYPE_FORSTREE,
    ADDR_TYPE_HASHTREE,
    ADDR_TYPE_WOTS,
    bytes_to_address,
)
from sphincs_params import get_params
from sphincs_utils import (
    bind_address_type,
    compute_auth_path_siblings,
    derive_fors_tree_address,
    derive_tree_hash_address,
    derive_wots_address,
    digest_to_tree_leaf_indices,
    expand_address,
    fors_message_to_indices,
)


def test_derive_wots_address_structure():
    addr_bytes = derive_wots_address(1, 0x123456789ABCDEF0, 7, 5, 2)
    words = bytes_to_address(addr_bytes)
    assert words[0] == 1
    assert words[1] == 0
    assert (words[2] << 32) | words[3] == 0x123456789ABCDEF0
    assert words[4] == ADDR_TYPE_WOTS
    assert words[5] == 7
    assert words[6] == 5
    assert words[7] == 2


def test_derive_tree_hash_address_structure():
    addr_bytes = derive_tree_hash_address(3, 0x0102030405060708, 6, 12)
    words = expand_address(addr_bytes)
    assert words[0] == 3
    assert words[1] == 0
    assert words[4] == ADDR_TYPE_HASHTREE
    assert (words[2] << 32) | words[3] == 0x0102030405060708
    assert words[6] == 6
    assert words[7] == 12


def test_compute_auth_path_siblings():
    siblings = compute_auth_path_siblings(leaf_idx=5, tree_height=3)
    assert siblings == [4, 3, 0]
    siblings_zero = compute_auth_path_siblings(leaf_idx=0, tree_height=2)
    assert siblings_zero == [1, 1]


def test_derive_fors_tree_address_structure():
    addr_bytes = derive_fors_tree_address(0, 0xDEADBEEFCAFEBABE, 5, 7)
    words = bytes_to_address(addr_bytes)
    assert words[0] == 0
    assert words[1] == 0
    assert (words[2] << 32) | words[3] == 0xDEADBEEFCAFEBABE
    assert words[4] == ADDR_TYPE_FORSTREE
    assert words[5] == 5
    assert words[6] == 0  # tree height preset to 0
    assert words[7] == 7


def test_digest_to_tree_leaf_indices():
    params = get_params()
    n = params["n"]
    tree_bits = params["full_height"] - params["tree_height"]
    tree_bytes = (tree_bits + 7) // 8
    leaf_bytes = (params["tree_height"] + 7) // 8
    rng = random.Random(20240318)
    buffer = bytes([0xAB] * n) + rng.randbytes(tree_bytes + leaf_bytes)
    tree_expected = int.from_bytes(buffer[n : n + tree_bytes], "big") & ((1 << tree_bits) - 1)
    leaf_expected = int.from_bytes(buffer[n + tree_bytes : n + tree_bytes + leaf_bytes], "big") & ((1 << params["tree_height"]) - 1)
    tree, leaf = digest_to_tree_leaf_indices(buffer, params)
    assert tree == tree_expected
    assert leaf == leaf_expected


def test_expand_address_roundtrip():
    rng = random.Random(7)
    words = [rng.getrandbits(32) for _ in range(8)]
    addr_bytes = derive_wots_address(
        words[0] & 0xFF,
        (words[2] << 32) | words[3],
        words[4],
        words[5],
        words[6],
    )
    expanded = expand_address(addr_bytes)
    assert len(expanded) == 8


def test_fors_message_to_indices_properties():
    params = get_params()
    message = bytes(range(24))
    indices = fors_message_to_indices(message, params)
    assert len(indices) == int(params["fors_trees"])
    max_index = max(indices)
    assert max_index < (1 << int(params["fors_height"]))


def test_bind_address_type_updates_field():
    original = derive_fors_tree_address(1, 2, 3, 4)
    bound = bind_address_type(original, ADDR_TYPE_FORSPK)
    original_words = bytes_to_address(original)
    bound_words = bytes_to_address(bound)
    assert original_words[:4] == bound_words[:4]
    assert bound_words[4] == ADDR_TYPE_FORSPK
    assert original_words[7] == bound_words[7]
