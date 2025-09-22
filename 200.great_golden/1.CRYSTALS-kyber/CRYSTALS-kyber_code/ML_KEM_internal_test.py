"""
@Descripttion: CRYSTALS-kyber KEM内部算法测试
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

from ML_KEM_internal import *
from Crypto.Cipher import AES
import pytest
import binascii
import hashlib

def test_sizes():
    for params, ek_len, dk_len, c_len in (
            (params512,  800,  1632  ,768 ),
            (params768,  1184, 2400 ,1088),
            (params1024, 1568, 3168 ,1568),
        ):

        ek, dk= ML_KEM_KeyGen_internal(b'\0'*64, params)
        m = H(b'\0'*32)
        K,c=ML_KEM_Encaps_internal(ek, m, params)
        assert len(ek) == ek_len
        assert len(dk) == dk_len
        assert len(c)==c_len
        assert len(K)==32

def test_Encaps_Decaps_internal():
   for params, ek_len, dk_len, c_len in (
            (params512,  800,  1632  ,768 ),
            (params768,  1184, 2400 ,1088),
            (params1024, 1568, 3168 ,1568),
        ):

        ek, dk= ML_KEM_KeyGen_internal(b'\0'*64, params)
        K,c=ML_KEM_Encaps_internal(ek,b'\0'*32, params)
        Kp=ML_KEM_Decaps_internal(dk, c, params)
        assert K== Kp
        
        
# # NIST Known Answer Test (KAT) 测试向量

# class NistDRBG:
#     """
#     类实现了 NIST 的确定性随机比特生成器(DRBG)，用于生成 NIST 的已知答案测试(KAT),
#     详见see PQCgenKAT.c. 
#     """
#     def __init__(self, seed):
#         self.key = b'\0'*32
#         self.v = 0
#         assert len(seed) == 48
#         self._update(seed)
#     def _update(self, seed):
#         b = AES.new(self.key, AES.MODE_ECB)
#         buf = b''
#         for i in range(3):
#             self.v += 1
#             buf += b.encrypt(self.v.to_bytes(16, 'big'))
#         if seed is not None:
#             buf = bytes([x ^ y for x, y in zip(seed, buf)])
#         self.key = buf[:32]
#         self.v = int.from_bytes(buf[32:], 'big')
#     def read(self, length):
#         b = AES.new(self.key, AES.MODE_ECB)
#         ret = b''
#         while len(ret) < length:
#             self.v += 1
#             block = b.encrypt(self.v.to_bytes(16, 'big'))
#             ret += block
#         self._update(None)
#         return ret[:length]

# @pytest.mark.parametrize("name,params,want", [
#             (b"Kyber512", params512, "e9c2bd37133fcb40772f81559f14b1f58dccd1c816701be9ba6214d43baf4547"),
#             (b"Kyber768", params768, "a1e122cad3c24bc51622e4c242d8b8acbcd3f618fee4220400605ca8f9ea02c2"),
#             (b"Kyber1024", params1024, "89248f2f33f7f4f7051729111f3049c409a933ec904aedadf035f30fa5646cd5"),
#         ])
# def test_nist_kat(name, params, want):
#     seed = bytes(range(48))
#     g = NistDRBG(seed)
#     f = hashlib.sha256()
#     f.update(b"# %s\n\n" % name)
#     for i in range(100):
#         seed = g.read(48)
#         f.update(b"count = %d\n" % i)
#         f.update(b"seed = %s\n" % binascii.hexlify(seed).upper())
#         g2 = NistDRBG(seed)

#         kseed = g2.read(32) +  g2.read(32)
#         m = g2.read(32)

#         ek, dk = ML_KEM_KeyGen_internal(kseed, params)
#         K, c = ML_KEM_Encaps_internal(ek, m, params)
#         Kp = ML_KEM_Decaps_internal(dk, c, params)
#         assert K == Kp
#         f.update(b"pk = %s\n" % binascii.hexlify(ek).upper())
#         f.update(b"sk = %s\n" % binascii.hexlify(dk).upper())
#         f.update(b"ct = %s\n" % binascii.hexlify(c).upper())
#         f.update(b"ss = %s\n\n" % binascii.hexlify(K).upper())

#     assert f.hexdigest() == want