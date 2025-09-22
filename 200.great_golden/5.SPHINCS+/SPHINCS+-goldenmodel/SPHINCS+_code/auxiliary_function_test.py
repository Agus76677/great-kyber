"""
@Descripttion: SPHINCS+ 辅助函数阶段一测试
@version: V0.2
@Author: GoldenModel-Team
@Date: 2025-03-18 12:00
"""

import random

import pytest

from auxiliary_function import (
    ADR_BYTES,
    ADDR_TYPE_HASHTREE,
    ADDR_TYPE_WOTS,
    ADR_WORDS,
    MODULE_VERSION,
    address_to_bytes,
    bytes_to_address,
    bytes_to_int,
    bytes_to_u32,
    concat_bytes,
    copy_keypair_addr,
    copy_subtree_addr,
    ensure_bytes,
    get_module_metadata,
    int_to_bytes,
    new_address,
    set_chain_addr,
    set_hash_addr,
    set_keypair_addr,
    set_layer_addr,
    set_tree_addr,
    set_type,
    split_bytes,
    u32_to_bytes,
    xor_bytes,
)


def test_metadata_shape():
    metadata = get_module_metadata()
    assert metadata["name"] == "sphincs_auxiliary"
    assert metadata["version"] == MODULE_VERSION


def test_ensure_bytes_and_concat():
    payload = b"stage1"
    assert ensure_bytes(payload) == payload
    with pytest.raises(TypeError):
        ensure_bytes("stage1")
    assert concat_bytes(b"a", b"b", b"c") == b"abc"


def test_int_encoding_roundtrip():
    values = [0, 1, 255, 256, 2**32 - 1]
    for value in values:
        encoded = u32_to_bytes(value)
        assert bytes_to_u32(encoded) == value
    with pytest.raises(ValueError):
        u32_to_bytes(-1)
    with pytest.raises(ValueError):
        u32_to_bytes(2**32)


def test_split_bytes_and_xor():
    data = bytes(range(8))
    chunks = split_bytes(data, 2)
    assert chunks == [b"\x00\x01", b"\x02\x03", b"\x04\x05", b"\x06\x07"]
    with pytest.raises(ValueError):
        split_bytes(data, 3)
    with pytest.raises(ValueError):
        split_bytes(data, 0)
    lhs = bytes([0xAA, 0x55, 0xFF])
    rhs = bytes([0x0F, 0xF0, 0x0F])
    assert xor_bytes(lhs, rhs) == bytes([0xA5, 0xA5, 0xF0])


def test_address_encoding_roundtrip():
    addr = new_address()
    set_layer_addr(addr, 2)
    set_tree_addr(addr, 0x0123_4567_89AB_CDEF)
    set_type(addr, ADDR_TYPE_WOTS)
    set_keypair_addr(addr, 5)
    set_chain_addr(addr, 9)
    set_hash_addr(addr, 3)
    encoded = address_to_bytes(addr)
    assert len(encoded) == ADR_BYTES
    decoded = bytes_to_address(encoded)
    assert decoded[0] == 2
    assert decoded[1] == 0
    assert decoded[2] == 0x0123_4567
    assert decoded[3] == 0x89AB_CDEF
    assert decoded[4] == ADDR_TYPE_WOTS
    assert decoded[5] == 5
    assert decoded[6] == 9
    assert decoded[7] == 3


def test_copy_helpers_preserve_selected_fields():
    src = new_address()
    set_layer_addr(src, 4)
    set_tree_addr(src, 0x0102030405060708)
    set_keypair_addr(src, 11)
    dst = new_address()
    copy_subtree_addr(dst, src)
    assert dst[0:4] == src[0:4]
    assert dst[5] == 0
    copy_keypair_addr(dst, src)
    assert dst[5] == src[5]


def test_hashtree_alias_helpers():
    addr = new_address()
    set_type(addr, ADDR_TYPE_HASHTREE)
    set_chain_addr(addr, 4)
    set_hash_addr(addr, 7)
    encoded = address_to_bytes(addr)
    decoded = bytes_to_address(encoded)
    assert decoded[4] == ADDR_TYPE_HASHTREE
    assert decoded[6] == 4
    assert decoded[7] == 7


def test_random_address_integrity():
    rng = random.Random(20240318)
    for _ in range(4):
        words = [rng.getrandbits(32) for _ in range(ADR_WORDS)]
        encoded = address_to_bytes(words)
        assert bytes_to_address(encoded) == words


def test_bytes_to_int_helpers():
    data = bytes(range(16))
    assert bytes_to_int(data[:4]) == 0x00010203
    assert int_to_bytes(0x0A0B0C0D, 4) == b"\x0a\x0b\x0c\x0d"
