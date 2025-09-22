"""
@Descripttion: SPHINCS+ Merkle/Hypertree 工具（Stage-4 实装版）
@version: V0.4
@Author: GoldenModel-Team
@Date: 2025-03-30 12:00

对齐 CRYSTALS-Kyber / Dilithium 黄金模型的注释与函数风格，
提供 Merkle 树节点压缩、认证路径计算与多层聚合基础能力。
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Mapping, Sequence, Tuple

from auxiliary_function import (
    ADDR_TYPE_HASHTREE,
    ADDR_TYPE_WOTSPK,
    ADR_BYTES,
    address_to_bytes,
    bytes_to_address,
    copy_address,
    ensure_bytes,
    set_tree_height,
    set_tree_index,
    set_type,
)
from sphincs_hash import H, thash_multi

LeafFunc = Callable[[int, Sequence[int]], bytes]


def _normalize_address(address: bytes) -> List[int]:
    """将字节形式的地址标准化为 8×32-bit 列表副本。"""

    words = copy_address(bytes_to_address(ensure_bytes(address, length=ADR_BYTES)))
    return words


def _ensure_leaf_count(tree_height: int) -> int:
    if tree_height < 0:
        raise ValueError("tree_height must be non-negative")
    return 1 << tree_height if tree_height > 0 else 1


def l_tree(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    base_address: bytes,
    wots_pk: bytes,
) -> bytes:
    """
    使用 L-tree 结构压缩 WOTS+ 公钥，输出单个 n 字节节点。

    输入：
        params: 参数字典，至少包含 n。
        pub_seed: 公钥种子（n 字节）。
        base_address: WOTS 公钥地址（type=ADDR_TYPE_WOTSPK）。
        wots_pk: WOTS 公钥（len × n 字节）。
    输出：
        bytes: 压缩后的叶节点（n 字节）。
    """

    n = int(params["n"])
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    pk_bytes = ensure_bytes(wots_pk)
    if len(pk_bytes) % n != 0:
        raise ValueError("wots_pk length must be a multiple of n")
    nodes: List[bytes] = [pk_bytes[i : i + n] for i in range(0, len(pk_bytes), n)]
    if not nodes:
        raise ValueError("wots_pk must contain at least one chunk")
    base_words = _normalize_address(base_address)
    set_type(base_words, ADDR_TYPE_WOTSPK)
    # Stage-5（SHA256-L1）直接使用 tweakable hash 压缩整个 WOTS+ 公钥，
    # 与参考实现的 thash 调用保持一致。
    return thash_multi(params, pub_seed_n, address_to_bytes(base_words), nodes)


def compute_subtree_authentication(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    tree_address: bytes,
    leaf_idx: int,
    tree_height: int,
    leaf_func: LeafFunc,
    *,
    addr_type: int = ADDR_TYPE_HASHTREE,
    leaf_offset: int = 0,
) -> Tuple[List[bytes], bytes]:
    """
    构造 Merkle 子树，返回指定叶子的认证路径与根节点。

    输入：
        params: 参数集合。
        pub_seed: 公钥种子（n 字节）。
        tree_address: 树地址（type 字段将在函数内部覆盖为 addr_type）。
        leaf_idx: 目标叶子索引（0 <= leaf_idx < 2^tree_height）。
        tree_height: 子树高度。
        leaf_func: 回调函数，生成叶子节点内容。
        addr_type: 地址类型（默认 HASHTREE，可用于 FORS/HT 层）。
        leaf_offset: 叶索引全局偏移，用于地址去重。
    输出：
        Tuple[List[bytes], bytes]: (认证路径列表, 根节点)。
    """

    n = int(params["n"])
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    base_words = _normalize_address(tree_address)
    set_type(base_words, addr_type)
    set_tree_height(base_words, 0)
    set_tree_index(base_words, 0)

    leaf_count = _ensure_leaf_count(tree_height)
    if not 0 <= leaf_idx < leaf_count:
        raise ValueError("leaf_idx out of range for tree height")

    nodes: List[bytes] = []
    for idx in range(leaf_count):
        leaf_addr = copy_address(base_words)
        set_tree_height(leaf_addr, 0)
        set_tree_index(leaf_addr, leaf_offset + idx)
        leaf_value = leaf_func(idx, leaf_addr)
        nodes.append(ensure_bytes(leaf_value, length=n))

    auth_path: List[bytes] = []
    current_idx = leaf_idx
    level = 0
    current_offset = leaf_offset
    while len(nodes) > 1:
        sibling_idx = current_idx ^ 1
        auth_path.append(nodes[sibling_idx])
        parents: List[bytes] = []
        parent_offset = current_offset >> 1
        for idx in range(0, len(nodes), 2):
            parent_addr = copy_address(base_words)
            set_tree_height(parent_addr, level + 1)
            set_tree_index(parent_addr, parent_offset + idx // 2)
            parents.append(
                H(
                    params,
                    pub_seed_n,
                    address_to_bytes(parent_addr),
                    nodes[idx],
                    nodes[idx + 1],
                )
            )
        nodes = parents
        current_idx >>= 1
        level += 1
        current_offset >>= 1
    root = nodes[0]
    return auth_path, root


def compute_subtree_root(
    params: Mapping[str, int | str],
    pub_seed: bytes,
    tree_address: bytes,
    tree_height: int,
    leaf_func: LeafFunc,
    *,
    addr_type: int = ADDR_TYPE_HASHTREE,
    leaf_offset: int = 0,
) -> bytes:
    """仅计算子树根节点，复用认证路径生成逻辑。"""

    _, root = compute_subtree_authentication(
        params,
        pub_seed,
        tree_address,
        0,
        tree_height,
        leaf_func,
        addr_type=addr_type,
        leaf_offset=leaf_offset,
    )
    return root


def compute_root_from_auth_path(
    params: Mapping[str, int | str],
    leaf: bytes,
    leaf_idx: int,
    auth_path: Iterable[bytes],
    pub_seed: bytes,
    tree_address: bytes,
    *,
    addr_type: int = ADDR_TYPE_HASHTREE,
    leaf_offset: int = 0,
) -> bytes:
    """
    根据叶节点与认证路径恢复 Merkle 根。

    输入：
        params: 参数集合。
        leaf: 叶节点内容（n 字节）。
        leaf_idx: 叶索引。
        auth_path: 认证路径（从底层到顶层的节点列表）。
        pub_seed: 公钥种子。
        tree_address: 树地址。
    输出：
        bytes: 计算得到的根节点。
    """

    n = int(params["n"])
    node = ensure_bytes(leaf, length=n)
    pub_seed_n = ensure_bytes(pub_seed, length=n)
    path_nodes = [ensure_bytes(chunk, length=n) for chunk in auth_path]
    base_words = _normalize_address(tree_address)
    set_type(base_words, addr_type)

    current_idx = leaf_idx
    current_offset = leaf_offset + leaf_idx
    for level, sibling in enumerate(path_nodes, start=1):
        parent_addr = copy_address(base_words)
        set_tree_height(parent_addr, level)
        set_tree_index(parent_addr, current_offset >> 1)
        if current_idx % 2 == 0:
            node = H(params, pub_seed_n, address_to_bytes(parent_addr), node, sibling)
        else:
            node = H(params, pub_seed_n, address_to_bytes(parent_addr), sibling, node)
        current_idx >>= 1
        current_offset >>= 1
    return node


__all__ = [
    "l_tree",
    "compute_subtree_authentication",
    "compute_subtree_root",
    "compute_root_from_auth_path",
]
