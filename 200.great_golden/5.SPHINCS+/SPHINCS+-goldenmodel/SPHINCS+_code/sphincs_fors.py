"""
@Descripttion: SPHINCS+ FORS 基元实现（Stage-3 版本）
@version: V0.4
@Author: GoldenModel-Team
@Date: 2025-03-25 12:00

参考 CRYSTALS-Kyber / Dilithium 黄金模型的注释与结构，实现 FORS 多树签名、
公钥恢复与验证逻辑，复用 Stage-1 的 SHA256 基元与地址工具。
"""

from __future__ import annotations

from typing import List, Mapping, Sequence, Tuple

from auxiliary_function import (
    ADDR_TYPE_FORSPK,
    ADDR_TYPE_FORSTREE,
    ADR_BYTES,
    address_to_bytes,
    bytes_to_address,
    copy_address,
    copy_keypair_addr,
    copy_subtree_addr,
    ensure_bytes,
    new_address,
    set_keypair_addr,
    set_tree_height,
    set_tree_index,
    set_type,
)
from sphincs_hash import F, H, PRF, thash_multi
from sphincs_utils import fors_message_to_indices


def _ensure_params(params: Mapping[str, int | str]) -> Tuple[int, int, int]:
    n = int(params["n"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    if fors_height <= 0:
        raise ValueError("fors_height must be positive")
    if fors_trees <= 0:
        raise ValueError("fors_trees must be positive")
    return n, fors_height, fors_trees


def _copy_base_address(address: bytes) -> Tuple[List[int], int]:
    words = bytes_to_address(ensure_bytes(address, length=ADR_BYTES))
    base = new_address()
    copy_subtree_addr(base, words)
    keypair = words[5]
    set_keypair_addr(base, keypair)
    return base, keypair


def _fors_gen_leaf(
    params: Mapping[str, int | str],
    sk_seed: bytes,
    pub_seed: bytes,
    addr_idx: int,
    base_tree_addr: Sequence[int],
) -> bytes:
    leaf_addr = new_address()
    copy_keypair_addr(leaf_addr, base_tree_addr)
    set_type(leaf_addr, ADDR_TYPE_FORSTREE)
    set_tree_height(leaf_addr, 0)
    set_tree_index(leaf_addr, addr_idx)
    sk = PRF(params, sk_seed, address_to_bytes(leaf_addr))
    return F(params, pub_seed, address_to_bytes(leaf_addr), sk)


def _treehash(
    params: Mapping[str, int | str],
    sk_seed: bytes,
    pub_seed: bytes,
    leaf_idx: int,
    idx_offset: int,
    tree_height: int,
    base_tree_addr: Sequence[int],
) -> Tuple[List[bytes], bytes]:
    n = int(params["n"])
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    sk_seed_n = ensure_bytes(sk_seed, length=n)
    stack: List[bytes] = []
    heights: List[int] = []
    auth_path: List[bytes] = [b"\x00" * n for _ in range(tree_height)]
    for idx in range(1 << tree_height):
        leaf = _fors_gen_leaf(params, sk_seed_n, pub_seed_n, idx + idx_offset, base_tree_addr)
        stack.append(leaf)
        heights.append(0)
        if tree_height > 0 and (leaf_idx ^ 0x1) == idx:
            auth_path[0] = leaf
        while len(stack) >= 2 and heights[-1] == heights[-2]:
            current_height = heights[-1]
            parent_addr = copy_address(base_tree_addr)
            set_tree_height(parent_addr, current_height + 1)
            set_tree_index(
                parent_addr,
                (idx >> (current_height + 1)) + (idx_offset >> (current_height + 1)),
            )
            right = stack.pop()
            left = stack.pop()
            heights.pop()
            heights.pop()
            parent = H(params, pub_seed_n, address_to_bytes(parent_addr), left, right)
            stack.append(parent)
            heights.append(current_height + 1)
            new_height = heights[-1]
            tree_idx = idx >> (current_height + 1)
            if new_height < tree_height and (((leaf_idx >> new_height) ^ 0x1) == tree_idx):
                auth_path[new_height] = parent
    root = stack[-1] if stack else b"\x00" * n
    return auth_path, root


def _compute_root(
    params: Mapping[str, int | str],
    leaf: bytes,
    leaf_idx: int,
    idx_offset: int,
    auth_path: Sequence[bytes],
    pub_seed: bytes,
    base_tree_addr: Sequence[int],
) -> bytes:
    """Match the reference compute_root semantics byte-for-byte."""

    n = int(params["n"])
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    auth_nodes = [ensure_bytes(node, length=n) for node in auth_path]
    leaf_bytes = ensure_bytes(leaf, length=n)

    if not auth_nodes:
        return leaf_bytes

    buffer = bytearray(2 * n)

    # Initial left/right placement mirrors the reference implementation logic.
    if leaf_idx & 0x1:
        buffer[:n] = auth_nodes[0]
        buffer[n:] = leaf_bytes
    else:
        buffer[:n] = leaf_bytes
        buffer[n:] = auth_nodes[0]

    current_leaf_idx = leaf_idx
    current_idx_offset = idx_offset

    for level in range(len(auth_nodes) - 1):
        current_leaf_idx >>= 1
        current_idx_offset >>= 1

        parent_addr = copy_address(base_tree_addr)
        set_tree_height(parent_addr, level + 1)
        set_tree_index(parent_addr, current_leaf_idx + current_idx_offset)

        parent = H(
            params,
            pub_seed_n,
            address_to_bytes(parent_addr),
            bytes(buffer[:n]),
            bytes(buffer[n:]),
        )

        next_auth = auth_nodes[level + 1]
        if current_leaf_idx & 0x1:
            buffer[:n] = next_auth
            buffer[n:] = parent
        else:
            buffer[:n] = parent
            buffer[n:] = next_auth

    current_leaf_idx >>= 1
    current_idx_offset >>= 1

    final_addr = copy_address(base_tree_addr)
    set_tree_height(final_addr, len(auth_nodes))
    set_tree_index(final_addr, current_leaf_idx + current_idx_offset)

    return H(
        params,
        pub_seed_n,
        address_to_bytes(final_addr),
        bytes(buffer[:n]),
        bytes(buffer[n:]),
    )


def fors_sign(
    params: Mapping[str, int | str],
    message: bytes,
    sk_seed: bytes,
    pub_seed: bytes,
    base_address: bytes,
) -> Tuple[bytes, bytes]:
    n, fors_height, fors_trees = _ensure_params(params)
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    sk_seed_n = ensure_bytes(sk_seed, length=n)
    base_tree_addr, keypair = _copy_base_address(base_address)
    indices = fors_message_to_indices(message, params)
    if len(indices) != fors_trees:
        raise ValueError("index extraction mismatch with fors_trees")
    signature_parts: List[bytes] = []
    roots: List[bytes] = []
    leaf_count = 1 << fors_height
    for tree_num, index in enumerate(indices):
        if index >= leaf_count:
            raise ValueError("FORS index out of range for tree height")
        idx_offset = tree_num * leaf_count
        tree_addr = copy_address(base_tree_addr)
        set_type(tree_addr, ADDR_TYPE_FORSTREE)
        set_keypair_addr(tree_addr, keypair)
        set_tree_height(tree_addr, 0)
        set_tree_index(tree_addr, idx_offset + index)
        leaf_addr = copy_address(tree_addr)
        set_tree_index(leaf_addr, idx_offset + index)
        secret_element = PRF(params, sk_seed_n, address_to_bytes(leaf_addr))
        signature_parts.append(secret_element)
        auth_path, root = _treehash(
            params,
            sk_seed_n,
            pub_seed_n,
            index,
            idx_offset,
            fors_height,
            tree_addr,
        )
        signature_parts.extend(auth_path)
        roots.append(root)
    signature = b"".join(signature_parts)
    pk_addr = copy_address(base_tree_addr)
    set_type(pk_addr, ADDR_TYPE_FORSPK)
    set_keypair_addr(pk_addr, keypair)
    set_tree_height(pk_addr, 0)
    set_tree_index(pk_addr, 0)
    aggregated_pk = thash_multi(params, pub_seed_n, address_to_bytes(pk_addr), roots)
    return signature, aggregated_pk


def fors_pk_from_sig(
    params: Mapping[str, int | str],
    signature: bytes,
    message: bytes,
    pub_seed: bytes,
    base_address: bytes,
) -> bytes:
    n, fors_height, fors_trees = _ensure_params(params)
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    base_tree_addr, keypair = _copy_base_address(base_address)
    indices = fors_message_to_indices(message, params)
    if len(indices) != fors_trees:
        raise ValueError("index extraction mismatch with fors_trees")
    expected_len = fors_trees * (1 + fors_height) * n
    sig_bytes = ensure_bytes(signature, length=expected_len)
    roots: List[bytes] = []
    leaf_count = 1 << fors_height
    offset = 0
    for tree_num, index in enumerate(indices):
        idx_offset = tree_num * leaf_count
        tree_addr = copy_address(base_tree_addr)
        set_type(tree_addr, ADDR_TYPE_FORSTREE)
        set_keypair_addr(tree_addr, keypair)
        set_tree_height(tree_addr, 0)
        set_tree_index(tree_addr, idx_offset + index)
        secret = sig_bytes[offset : offset + n]
        offset += n
        leaf_addr = copy_address(tree_addr)
        set_tree_index(leaf_addr, idx_offset + index)
        leaf = F(params, pub_seed_n, address_to_bytes(leaf_addr), secret)
        auth_path = [
            sig_bytes[offset + level * n : offset + (level + 1) * n]
            for level in range(fors_height)
        ]
        offset += fors_height * n
        root = _compute_root(
            params,
            leaf,
            index,
            idx_offset,
            auth_path,
            pub_seed_n,
            tree_addr,
        )
        roots.append(root)
    pk_addr = copy_address(base_tree_addr)
    set_type(pk_addr, ADDR_TYPE_FORSPK)
    set_keypair_addr(pk_addr, keypair)
    set_tree_height(pk_addr, 0)
    set_tree_index(pk_addr, 0)
    return thash_multi(params, pub_seed_n, address_to_bytes(pk_addr), roots)


def fors_verify(
    params: Mapping[str, int | str],
    signature: bytes,
    message: bytes,
    pub_seed: bytes,
    base_address: bytes,
    expected_pk: bytes,
) -> bool:
    derived_pk = fors_pk_from_sig(params, signature, message, pub_seed, base_address)
    return derived_pk == ensure_bytes(expected_pk, length=len(derived_pk))


__all__ = ["fors_sign", "fors_pk_from_sig", "fors_verify"]
