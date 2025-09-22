"""
@Descripttion: ML_DSA 内部组件方案测试
@version: V1.0
@Author: HZW
@Date: 2025-03-12 18:00
"""


from ML_DSA_internal import *
import os

def test_KeyGen_internal():
    for params in [ML_DSA_44,ML_DSA_65,ML_DSA_87]:
        for _ in range(100):
            seed = os.urandom(32)
            # Generate key pair
            pk, sk = KeyGen_internal(seed, params)
            
            # Test output types
            assert isinstance(pk, bytes)
            assert isinstance(sk, bytes)
            
            # Test output lengths based on params
            expected_pk_len = 32 + 32 * params.k * ((q - 1).bit_length() - d)
            expected_sk_len = (32+32+64+32*((params.k+params.l)*(2*params.eta).bit_length()+d*params.k))
            
            assert len(pk) == expected_pk_len
            assert len(sk) == expected_sk_len
            
            # Test deterministic output
            pk2, sk2 = KeyGen_internal(seed, params)
            assert pk == pk2
            assert sk == sk2
            
            # Test different seeds produce different keys
            different_seed = os.urandom(32)
            pk3, sk3 = KeyGen_internal(different_seed, params)
            assert pk != pk3
            assert sk != sk3
    
    
def test_Sign_internal():
    for params in [ML_DSA_44,ML_DSA_65,ML_DSA_87]:
        for _ in range(100):
            seed = os.urandom(32)
            pk, sk = KeyGen_internal(seed, params)

            test_message = os.urandom(32)
            rnd = os.urandom(32)

            signature = Sign_internal(sk, test_message, rnd, params)
            print("signature:",signature)
            assert isinstance(signature, bytes)
            signature_len=(params.lambda_1//4+params.l*32*(1+(params.gamma_1-1).bit_length())+params.omega+params.k)
            print(signature_len)
            print(len(signature))
            assert len(signature)== signature_len

            # Test deterministic signing with same inputs
            signature2 = Sign_internal(sk, test_message, rnd, params)
            assert signature == signature2

            # Test different random values produce different signatures
            rnd2 = os.urandom(32)
            signature3 = Sign_internal(sk, test_message, rnd2, params)
            assert signature != signature3

            # Test different messages produce different signatures
            test_message2 = bytes([2] * 32)
            signature4 = Sign_internal(sk, test_message2, rnd, params)
            assert signature != signature4

    

def test_Verify_internal(): 
    for params in [ML_DSA_44,ML_DSA_65,ML_DSA_87]:
        for _ in range(100):
            seed = os.urandom(32)
            pk, sk = KeyGen_internal(seed, params)

            test_message = bytes([1] * 32) 
            rnd = os.urandom(32) 
            
            signature = Sign_internal(sk, test_message, rnd, params)
            # print("signature:",signature)
            assert isinstance(signature, bytes)
            signature_len=(params.lambda_1//4+params.l*32*(1+(params.gamma_1-1).bit_length())+params.omega+params.k)
            assert len(signature)== signature_len
            
            t=Verify_internal(pk, test_message, signature, params)
            print(t)
            assert t==True
            
    
test_Verify_internal()
    