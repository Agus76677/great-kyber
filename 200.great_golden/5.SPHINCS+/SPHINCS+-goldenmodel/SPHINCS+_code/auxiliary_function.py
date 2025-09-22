"""
@Descripttion: SPHINCS+ 辅助函数（Stage-1 实装版）
@version: V0.2
@Author: GoldenModel-Team
@Date: 2025-03-18 12:00

本模块的函数命名、注释与 CRYSTALS-Kyber/Dilithium 黄金模型保持一致，
用于提供哈希与地址相关的通用辅助能力。
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

MODULE_VERSION = "0.1.0-stage1"

ADR_WORDS = 8
ADR_WORD_BYTES = 4
ADR_BYTES = ADR_WORDS * ADR_WORD_BYTES

ADDR_TYPE_WOTS = 0
ADDR_TYPE_WOTSPK = 1
ADDR_TYPE_HASHTREE = 2
ADDR_TYPE_FORSTREE = 3
ADDR_TYPE_FORSPK = 4

_UINT32_MASK = 0xFFFFFFFF
_UINT64_MASK = 0xFFFFFFFFFFFFFFFF


def get_module_metadata() -> Dict[str, str]:
    """
    获取当前模块的基础元信息。

    返回：
        Dict[str, str]: 包含名称与版本号的字典。
    """

    return {
        "name": "sphincs_auxiliary",
        "version": MODULE_VERSION,
    }


def ensure_bytes(data: bytes | bytearray | memoryview, *, length: int | None = None) -> bytes:
    """
    确保输入对象为 bytes 类型并进行长度校验。

    输入：
        data (Union[bytes, bytearray, memoryview]): 待校验数据。
        length (Optional[int]): 如提供则要求输出长度固定。
    输出：
        bytes: 标准化后的字节序列副本。
    """

    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    normalized = bytes(data)
    if length is not None and len(normalized) != length:
        raise ValueError(f"expected length {length}, got {len(normalized)}")
    return normalized


def concat_bytes(*chunks: bytes | bytearray | memoryview) -> bytes:
    """
    将多个字节序列按顺序拼接。

    输入：
        *chunks: 任意数量的字节序列。
    输出：
        bytes: 拼接后的字节序列。
    """

    return b"".join(ensure_bytes(chunk) for chunk in chunks)


def split_bytes(data: bytes | bytearray | memoryview, size: int) -> List[bytes]:
    """
    将字节序列按固定大小切分。

    输入：
        data: 待切分的字节序列。
        size: 块大小（字节）。
    输出：
        List[bytes]: 均匀切分后的块列表。
    """

    if size <= 0:
        raise ValueError("size must be positive")
    normalized = ensure_bytes(data)
    if len(normalized) % size != 0:
        raise ValueError("data length must be a multiple of chunk size")
    return [normalized[i : i + size] for i in range(0, len(normalized), size)]


def int_to_bytes(value: int, length: int, *, byteorder: str = "big") -> bytes:
    """
    将整数转换为固定长度的字节序列。

    输入：
        value (int): 非负整数。
        length (int): 输出字节长度。
        byteorder (str): 字节序，默认为 big endian。
    输出：
        bytes: 对应的字节表示。
    """

    if value < 0:
        raise ValueError("value must be non-negative")
    return value.to_bytes(length, byteorder)


def bytes_to_int(data: bytes | bytearray | memoryview, *, byteorder: str = "big") -> int:
    """
    将字节序列还原为整数。

    输入：
        data: 字节序列。
        byteorder (str): 字节序。
    输出：
        int: 对应的整数值。
    """

    return int.from_bytes(ensure_bytes(data), byteorder)


def u32_to_bytes(value: int, *, byteorder: str = "big") -> bytes:
    """
    32 位无符号整数编码。
    """

    if not 0 <= value <= _UINT32_MASK:
        raise ValueError("value out of 32-bit range")
    return int_to_bytes(value, ADR_WORD_BYTES, byteorder=byteorder)


def bytes_to_u32(data: bytes | bytearray | memoryview, *, byteorder: str = "big") -> int:
    """
    32 位无符号整数解码。
    """

    normalized = ensure_bytes(data, length=ADR_WORD_BYTES)
    return bytes_to_int(normalized, byteorder=byteorder)


def u64_to_bytes(value: int, *, byteorder: str = "big") -> bytes:
    """
    64 位无符号整数编码。
    """

    if not 0 <= value <= _UINT64_MASK:
        raise ValueError("value out of 64-bit range")
    return int_to_bytes(value, 8, byteorder=byteorder)


def bytes_to_u64(data: bytes | bytearray | memoryview, *, byteorder: str = "big") -> int:
    """
    64 位无符号整数解码。
    """

    normalized = ensure_bytes(data, length=8)
    return bytes_to_int(normalized, byteorder=byteorder)


def new_address() -> List[int]:
    """
    生成零初始化的地址表示（8×32-bit）。
    """

    return [0] * ADR_WORDS


def copy_address(addr: Sequence[int]) -> List[int]:
    """
    创建地址列表的浅拷贝并执行基本校验。
    """

    if len(addr) != ADR_WORDS:
        raise ValueError("address must contain eight 32-bit words")
    return [value & _UINT32_MASK for value in addr]


def copy_subtree_addr(dst: List[int], src: Sequence[int]) -> None:
    """按照 NIST 实现复制 layer/tree 字段。"""

    if len(dst) != ADR_WORDS or len(src) != ADR_WORDS:
        raise ValueError("address must contain eight 32-bit words")
    dst[0] = src[0] & _UINT32_MASK
    dst[1] = src[1] & _UINT32_MASK
    dst[2] = src[2] & _UINT32_MASK
    dst[3] = src[3] & _UINT32_MASK


def copy_keypair_addr(dst: List[int], src: Sequence[int]) -> None:
    """复制 layer/tree/keypair 字段。"""

    copy_subtree_addr(dst, src)
    dst[5] = src[5] & _UINT32_MASK


def clear_address(addr: List[int]) -> None:
    """
    就地清零地址列表。
    """

    for index in range(ADR_WORDS):
        addr[index] = 0


def _set_word(addr: List[int], index: int, value: int) -> None:
    if not 0 <= index < ADR_WORDS:
        raise IndexError("address word index out of range")
    if not 0 <= value <= _UINT32_MASK:
        raise ValueError("address word must be a 32-bit unsigned integer")
    addr[index] = value & _UINT32_MASK


def set_layer_addr(addr: List[int], layer: int) -> None:
    """
    设置地址的 layer 字段。
    """

    _set_word(addr, 0, layer)


def set_tree_addr(addr: List[int], tree: int) -> None:
    """
    设置地址的 tree 字段（与 NIST 参考实现一致的 96-bit 布局）。
    """

    if not 0 <= tree <= _UINT64_MASK:
        raise ValueError("tree index must be 64-bit unsigned")
    upper = (tree >> 64) & _UINT32_MASK
    high = (tree >> 32) & _UINT32_MASK
    low = tree & _UINT32_MASK
    _set_word(addr, 1, upper)
    _set_word(addr, 2, high)
    _set_word(addr, 3, low)


def set_type(addr: List[int], addr_type: int) -> None:
    """
    设置地址的类型字段。
    """

    _set_word(addr, 4, addr_type)


def set_keypair_addr(addr: List[int], keypair: int) -> None:
    """
    设置 keypair / leaf 编号字段。
    """

    _set_word(addr, 5, keypair)


def set_chain_addr(addr: List[int], chain: int) -> None:
    """
    设置 WOTS 链索引或树高度字段（取决于地址类型）。
    """

    _set_word(addr, 6, chain)


def set_hash_addr(addr: List[int], hash_idx: int) -> None:
    """
    设置哈希索引或树节点索引字段。
    """

    _set_word(addr, 7, hash_idx)


def set_tree_height(addr: List[int], height: int) -> None:
    """
    语义化的树高度写入（底层复用 word[5]）。
    """

    set_chain_addr(addr, height)


def set_tree_index(addr: List[int], index: int) -> None:
    """
    语义化的树节点索引写入（底层复用 word[6]）。
    """

    set_hash_addr(addr, index)


def address_to_bytes(addr: Sequence[int]) -> bytes:
    """
    将地址（8×32-bit）编码为 32 字节数组。
    """

    if len(addr) != ADR_WORDS:
        raise ValueError("address must contain eight 32-bit words")
    return b"".join(u32_to_bytes(word) for word in addr)


def bytes_to_address(data: bytes | bytearray | memoryview) -> List[int]:
    """
    将 32 字节编码解码为地址列表。
    """

    normalized = ensure_bytes(data, length=ADR_BYTES)
    return [bytes_to_u32(normalized[i : i + ADR_WORD_BYTES]) for i in range(0, ADR_BYTES, ADR_WORD_BYTES)]


def xor_bytes(lhs: bytes | bytearray | memoryview, rhs: bytes | bytearray | memoryview) -> bytes:
    """
    对等长字节序列执行按位异或。
    """

    left = ensure_bytes(lhs)
    right = ensure_bytes(rhs, length=len(left))
    return bytes(a ^ b for a, b in zip(left, right))


__all__ = [
    "MODULE_VERSION",
    "ADR_WORDS",
    "ADR_WORD_BYTES",
    "ADR_BYTES",
    "ADDR_TYPE_WOTS",
    "ADDR_TYPE_WOTSPK",
    "ADDR_TYPE_HASHTREE",
    "ADDR_TYPE_FORSTREE",
    "ADDR_TYPE_FORSPK",
    "get_module_metadata",
    "ensure_bytes",
    "concat_bytes",
    "split_bytes",
    "int_to_bytes",
    "bytes_to_int",
    "u32_to_bytes",
    "bytes_to_u32",
    "u64_to_bytes",
    "bytes_to_u64",
    "new_address",
    "copy_address",
    "copy_subtree_addr",
    "copy_keypair_addr",
    "clear_address",
    "set_layer_addr",
    "set_tree_addr",
    "set_type",
    "set_keypair_addr",
    "set_chain_addr",
    "set_hash_addr",
    "set_tree_height",
    "set_tree_index",
    "address_to_bytes",
    "bytes_to_address",
    "xor_bytes",
]
