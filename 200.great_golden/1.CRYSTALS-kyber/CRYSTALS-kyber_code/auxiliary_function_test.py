"""
@Descripttion: CRYSTALS-kyber 辅助函数测试
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

import pytest
import numpy as np
import io
import random
from auxiliary_function import *

def test_smod():
    assert smod(3325) == -4
    assert smod(-3320) == 9

def test_round():
    assert Round(0.4) == 0
    assert Round(0.5) == 1
    assert Round(-0.5) == 0
    assert Round(-0.6) == -1
    
    
def test_compress_decompress():
    x = 1023
    d = 10
    decompressed = Decompress(x, d)
    compressed = Compress(decompressed, d)
    assert compressed == x

def test_bits_to_bytes_and_back():
    bits = [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1]
    bytes_ = BitsToBytes(bits, 8)
    assert bytes_ == [85,220] 
    assert BytesToBits(bytes_, 8) == bits
    

def test_byte_encode_decode():
    F = np.random.randint(0, 3329, size=256)
    d = 12
    encoded = ByteEncode(F, d)
    decoded = ByteDecode(encoded, d)
    count=0
    for i in range(256):
       if F[i] == decoded[i]:
           count=count+1
    assert count == 256
           
def test_brv():
    assert brv(91) == 109
    assert brv(1) == 64


def test_poly_operations():
    poly1 = Poly([1, 2, 3] + [0]*253)
    poly2 = Poly([3, 2, 1] + [0]*253)
    assert poly1 + poly2 == Poly([4, 4, 4] + [0]*253)
    
    result = poly1 - poly2
    expected = Poly([3327, 0, 2] + [0]*253)
    assert result == expected
    
def test_ntt_intt():
    for i in range(100):
        array3 = np.random.randint(0, 3329, size=256)
        Poly1 = Poly(array3)
        Poly2 = Poly1
        result = Poly1.NTT().INTT()
        
        assert Poly2 == result
        
    Poly1=Poly([1,384,0]+[0]*253) #384x^1+1
    Poly2=Poly([1,2,0]+[0]*253) #2x^1+1
    Poly3=Poly([1,386,768]+[0]*253) #768x^2+386x^1+1
    Poly2=Poly2.NTT()
    assert Poly1.NTT().PWM(Poly2).INTT()==Poly3

def test_sampling():
    p = sampleNTT(io.BytesIO(hashlib.shake_128(b'').digest(1344)))  
    assert p.cs[:4] == (3199, 697, 2212, 2302)
    assert p.cs[-3:] == (255, 846, 1)

    p = samplePolyCBD(range(64*2), 2)
    assert p.cs[:6] == (0, 0, 1, 0, 1, 0)
    assert p.cs[-4:] == (3328, 1, 0, 1)

    p = samplePolyCBD(range(64*3), 3)
    assert p.cs[:5] == (0, 1, 3328, 0, 2)
    assert p.cs[-4:] == (3328, 3327, 3328, 1)

    noise3Test = Poly(x%q for x in [
        0, 0, 1, -1, 0, 2, 0, -1, -1, 3, 0, 1, -2, -2, 0, 1, -2,
        1, 0, -2, 3, 0, 0, 0, 1, 3, 1, 1, 2, 1, -1, -1, -1, 0, 1,
        0, 1, 0, 2, 0, 1, -2, 0, -1, -1, -2, 1, -1, -1, 2, -1, 1,
        1, 2, -3, -1, -1, 0, 0, 0, 0, 1, -1, -2, -2, 0, -2, 0, 0,
        0, 1, 0, -1, -1, 1, -2, 2, 0, 0, 2, -2, 0, 1, 0, 1, 1, 1,
        0, 1, -2, -1, -2, -1, 1, 0, 0, 0, 0, 0, 1, 0, -1, -1, 0,
        -1, 1, 0, 1, 0, -1, -1, 0, -2, 2, 0, -2, 1, -1, 0, 1, -1,
        -1, 2, 1, 0, 0, -2, -1, 2, 0, 0, 0, -1, -1, 3, 1, 0, 1, 0,
        1, 0, 2, 1, 0, 0, 1, 0, 1, 0, 0, -1, -1, -1, 0, 1, 3, 1,
        0, 1, 0, 1, -1, -1, -1, -1, 0, 0, -2, -1, -1, 2, 0, 1, 0,
        1, 0, 2, -2, 0, 1, 1, -3, -1, -2, -1, 0, 1, 0, 1, -2, 2,
        2, 1, 1, 0, -1, 0, -1, -1, 1, 0, -1, 2, 1, -1, 1, 2, -2,
        1, 2, 0, 1, 2, 1, 0, 0, 2, 1, 2, 1, 0, 2, 1, 0, 0, -1, -1,
        1, -1, 0, 1, -1, 2, 2, 0, 0, -1, 1, 1, 1, 1, 0, 0, -2, 0,
        -1, 1, 2, 0, 0, 1, 1, -1, 1, 0, 1
    ])
    assert noise3Test ==samplePolyCBD(PRF(bytes(range(32)), 37).read(3*64), 3)
    noise2Test = Poly(x%q for x in [
        1, 0, 1, -1, -1, -2, -1, -1, 2, 0, -1, 0, 0, -1,
        1, 1, -1, 1, 0, 2, -2, 0, 1, 2, 0, 0, -1, 1, 0, -1,
        1, -1, 1, 2, 1, 1, 0, -1, 1, -1, -2, -1, 1, -1, -1,
        -1, 2, -1, -1, 0, 0, 1, 1, -1, 1, 1, 1, 1, -1, -2,
        0, 1, 0, 0, 2, 1, -1, 2, 0, 0, 1, 1, 0, -1, 0, 0,
        -1, -1, 2, 0, 1, -1, 2, -1, -1, -1, -1, 0, -2, 0,
        2, 1, 0, 0, 0, -1, 0, 0, 0, -1, -1, 0, -1, -1, 0,
        -1, 0, 0, -2, 1, 1, 0, 1, 0, 1, 0, 1, 1, -1, 2, 0,
        1, -1, 1, 2, 0, 0, 0, 0, -1, -1, -1, 0, 1, 0, -1,
        2, 0, 0, 1, 1, 1, 0, 1, -1, 1, 2, 1, 0, 2, -1, 1,
        -1, -2, -1, -2, -1, 1, 0, -2, -2, -1, 1, 0, 0, 0,
        0, 1, 0, 0, 0, 2, 2, 0, 1, 0, -1, -1, 0, 2, 0, 0,
        -2, 1, 0, 2, 1, -1, -2, 0, 0, -1, 1, 1, 0, 0, 2,
        0, 1, 1, -2, 1, -2, 1, 1, 0, 2, 0, -1, 0, -1, 0,
        1, 2, 0, 1, 0, -2, 1, -2, -2, 1, -1, 0, -1, 1, 1,
        0, 0, 0, 1, 0, -1, 1, 1, 0, 0, 0, 0, 1, 0, 1, -1,
        0, 1, -1, -1, 2, 0, 0, 1, -1, 0, 1, -1, 0,
    ])
    assert noise2Test == samplePolyCBD(PRF(bytes(range(32)), 37).read(2*64), 2)