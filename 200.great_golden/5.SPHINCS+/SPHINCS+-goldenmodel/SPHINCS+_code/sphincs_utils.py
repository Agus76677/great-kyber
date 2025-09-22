"""
@Descripttion: SPHINCS+ 工具函数（Stage-3 扩展版）
@version: V0.3
@Author: GoldenModel-Team
@Date: 2025-03-25 12:00
"""

from __future__ import annotations

from typing import List, Mapping, Tuple

from auxiliary_function import (
    ADDR_TYPE_HASHTREE,
    ADDR_TYPE_WOTS,
    ADDR_TYPE_FORSPK,
    ADDR_TYPE_FORSTREE,
    ADR_WORDS,
    address_to_bytes,
    bytes_to_address,
    ensure_bytes,
    new_address,
    set_chain_addr,
    set_hash_addr,
    set_keypair_addr,
    set_layer_addr,
    set_tree_addr,
    set_tree_height,
    set_tree_index,
    set_type,
)


def derive_wots_address(
    layer: int,
    tree: int,
    keypair: int,
    chain: int,
    hash_idx: int,
) -> bytes:
    """
    构造 WOTS+ 链地址并编码为 32 字节序列。
    """

    addr = new_address()
    set_layer_addr(addr, layer)
    set_tree_addr(addr, tree)
    set_type(addr, ADDR_TYPE_WOTS)
    set_keypair_addr(addr, keypair)
    set_chain_addr(addr, chain)
    set_hash_addr(addr, hash_idx)
    return address_to_bytes(addr)


def derive_tree_hash_address(
    layer: int,
    tree: int,
    tree_height: int,
    tree_index: int,
) -> bytes:
    """
    构造 Merkle 树节点地址。
    """

    addr = new_address()
    set_layer_addr(addr, layer)
    set_tree_addr(addr, tree)
    set_type(addr, ADDR_TYPE_HASHTREE)
    set_chain_addr(addr, tree_height)
    set_hash_addr(addr, tree_index)
    return address_to_bytes(addr)


def derive_fors_tree_address(
    layer: int,
    tree: int,
    keypair: int,
    tree_index: int = 0,
) -> bytes:
    """派生 FORS 叶节点地址，默认树高为 0。"""

    addr = new_address()
    set_layer_addr(addr, layer)
    set_tree_addr(addr, tree)
    set_type(addr, ADDR_TYPE_FORSTREE)
    set_keypair_addr(addr, keypair)
    set_tree_height(addr, 0)
    set_tree_index(addr, tree_index)
    return address_to_bytes(addr)


def compute_auth_path_siblings(leaf_idx: int, tree_height: int) -> List[int]:
    """
    计算每层的兄弟节点索引，用于认证路径。
    """

    if leaf_idx < 0 or tree_height < 0:
        raise ValueError("indices must be non-negative")
    siblings: List[int] = []
    idx = leaf_idx
    for _ in range(tree_height):
        siblings.append(idx ^ 1)
        idx >>= 1
    return siblings


def digest_to_tree_leaf_indices(
    digest: bytes,
    params: Mapping[str, int | str],
) -> Tuple[int, int]:
    """
    将 H_msg 生成的缓冲区解析为 (tree, leaf)。
    """

    n = int(params["n"])
    full_height = int(params["full_height"])
    tree_height = int(params["tree_height"])
    tree_bits = full_height - tree_height
    tree_bytes = (tree_bits + 7) // 8
    leaf_bits = tree_height
    leaf_bytes = (leaf_bits + 7) // 8
    normalized = ensure_bytes(digest)
    if len(normalized) < n + tree_bytes + leaf_bytes:
        raise ValueError("digest buffer too short for parameter set")
    tree_slice = normalized[n : n + tree_bytes]
    leaf_slice = normalized[n + tree_bytes : n + tree_bytes + leaf_bytes]
    tree = int.from_bytes(tree_slice, "big") & ((1 << tree_bits) - 1 if tree_bits > 0 else 0)
    leaf = int.from_bytes(leaf_slice, "big") & ((1 << leaf_bits) - 1 if leaf_bits > 0 else 0)
    return tree, leaf


def expand_address(address: bytes) -> Tuple[int, ...]:
    """
    将字节编码的地址展开为 8 个 32-bit 整数元组。
    """

    words = bytes_to_address(address)
    if len(words) != ADR_WORDS:
        raise ValueError("decoded address length mismatch")
    return tuple(words)


def fors_message_to_indices(
    message: bytes,
    params: Mapping[str, int | str],
) -> List[int]:
    """将消息映射为 FORS 叶索引序列。"""

    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    total_bits = fors_height * fors_trees
    min_bytes = (total_bits + 7) // 8
    normalized = ensure_bytes(message)
    if len(normalized) < min_bytes:
        raise ValueError("message too short for FORS index extraction")
    indices: List[int] = []
    offset = 0
    for _ in range(fors_trees):
        value = 0
        for _ in range(fors_height):
            byte = normalized[offset >> 3]
            bit = (byte >> (offset & 0x7)) & 0x1
            value = (value << 1) | bit
            offset += 1
        indices.append(value)
    return indices


def bind_address_type(address: bytes, addr_type: int) -> bytes:
    """将地址的 type 字段重写为目标类型。"""

    words = list(bytes_to_address(ensure_bytes(address)))
    set_type(words, addr_type)
    return address_to_bytes(words)


__all__ = [
    "derive_wots_address",
    "derive_tree_hash_address",
    "derive_fors_tree_address",
    "compute_auth_path_siblings",
    "digest_to_tree_leaf_indices",
    "expand_address",
    "fors_message_to_indices",
    "bind_address_type",
]
