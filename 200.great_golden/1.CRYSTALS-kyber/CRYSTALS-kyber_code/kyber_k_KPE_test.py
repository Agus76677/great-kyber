"""
@Descripttion: CRYSTALS-kyber PKE测试
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

import pytest
from kyber_k_PKE import *

def test_sizes():
    for params, ek_pke_len, dk_pke_len, c_len in (
            (params512,  800,  768  ,768 ),
            (params768,  1184, 1152 ,1088),
            (params1024, 1568, 1536 ,1568),
        ):

        ek_pke, dk_pke = k_PKE_KeyGen(b'\0'*32, params)
        m = H(b'\0'*32)
        _ ,r = G(m + H(ek_pke))
        c=k_PKE_Encrypt(ek_pke, m, r, params)
        assert len(ek_pke) == ek_pke_len
        assert len(dk_pke) == dk_pke_len
        assert len(c)==c_len

def test_encrypt_decrypt():
    for params, ek_pke_len, dk_pke_len, c_len in (
            (params512,  800,  768  ,768 ),
            (params768,  1184, 1152 ,1088),
            (params1024, 1568, 1536 ,1568),
        ):

        ek_pke, dk_pke = k_PKE_KeyGen(b'\0'*32, params)
        m = b'\x9eb\x91\x97\x0c\xb4M\xd9@\x08\xc7\x9b\xca\xf9\xd8o\x18\xb4\xb4\x9b\xa5\xb2\xa0G\x81\xdbq\x99\xed;\x9eN'
        _ ,r = G(m + H(ek_pke))
        c=k_PKE_Encrypt(ek_pke, m, r, params)
        decrypted_message = k_PKE_Decrypt(dk_pke, c, params)
        assert m == decrypted_message