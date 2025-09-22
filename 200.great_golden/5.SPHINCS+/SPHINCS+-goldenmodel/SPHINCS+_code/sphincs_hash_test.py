"""
@Descripttion: SPHINCS+ 哈希阶段一测试
@version: V0.2
@Author: GoldenModel-Team
@Date: 2025-03-18 12:00
"""

from sphincs_hash import F, H, H_msg, PRF, PRF_msg
from sphincs_params import get_params


def test_f_hash_vector():
    params = get_params()
    pub_seed = bytes.fromhex("00112233445566778899aabbccddeeff")
    address = bytes(range(32))
    message = bytes.fromhex("0f" * params["n"])
    expected = bytes.fromhex("143e7bc0fde18a2326d561d908cbfc22")
    assert F(params, pub_seed, address, message) == expected


def test_h_hash_vector():
    params = get_params()
    pub_seed = bytes.fromhex("ffeeddccbbaa99887766554433221100")
    address = bytes(reversed(range(32)))
    left = bytes.fromhex("aa" * params["n"])
    right = bytes.fromhex("55" * params["n"])
    expected = bytes.fromhex("6407343e353e63245ac1d4c3469d728b")
    assert H(params, pub_seed, address, left, right) == expected


def test_prf_vectors():
    params = get_params()
    key = bytes.fromhex("112233445566778899aabbccddeeff00")
    address = bytes([0x42] * 32)
    expected_prf = bytes.fromhex("cf0602c9fd3213660ab00203507b7fc6")
    assert PRF(params, key, address) == expected_prf

    opt_random = bytes.fromhex("00ff" * 8)
    message = b"stage1-prf"
    expected_prf_msg = bytes.fromhex("15649d176dcbca352c8650e3a2166f4b")
    assert PRF_msg(params, key, opt_random, message) == expected_prf_msg


def test_h_msg_vector():
    params = get_params()
    randomness = bytes.fromhex("aabbccddeeff00112233445566778899")
    public_key = bytes.fromhex("0123456789abcdef0123456789abcdef")
    message = b"SPHINCS+ Stage1"
    digest, tree, leaf = H_msg(params, randomness, public_key, message)
    expected_digest = (
        "363d65a47dc4384064cf58a35e33c8ecae82d4e9bc2c5c2bf609c04dfc8a08f9"
        "ef756dc40c0f28e8cb7112d30eb14ee1260f0cdf040e250713f2d11003b97f57"
        "9f3f5cf1f4d95d3ee613dd8b9688d82251184781eb6fe49704278d3173cd0621e"
        "971b3edc2d736a1c1c73bb3d7b6558af721df9f37188cceba06d7e068f2ab616d"
        "e3d3a3c8040c7270908041dba7da7cedac3c1cfed6f77b"
    )
    assert digest == bytes.fromhex(expected_digest)
    assert tree == 0x0D410EB91FA4B7
    assert leaf == 0x00A3
