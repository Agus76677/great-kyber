"""
@Descripttion: CRYSTALS-kyber KEM封装算法测试
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

from ML_KEM import *

def test_sizes():
    for params, ek_len, dk_len, c_len in (
            (params512,  800,  1632  ,768 ),
            (params768,  1184, 2400 ,1088),
            (params1024, 1568, 3168 ,1568),
        ):
        
        ML_KEM1=ML_KEM(params)

        ek, dk= ML_KEM1.KeyGen()
        K,c=ML_KEM1.Encaps(ek)
        assert len(ek) == ek_len
        assert len(dk) == dk_len
        assert len(c)==c_len
        assert len(K)==32

def test_Encaps_Decaps():
   for params, ek_len, dk_len, c_len in (
            (params512,  800,  1632  ,768 ),
            (params768,  1184, 2400 ,1088),
            (params1024, 1568, 3168 ,1568),
        ):
        ML_KEM1=ML_KEM(params)
        ek, dk= ML_KEM1.KeyGen()
        K,c=ML_KEM1.Encaps(ek)
        Kp=ML_KEM1.Decaps(dk, c)
        assert K== Kp