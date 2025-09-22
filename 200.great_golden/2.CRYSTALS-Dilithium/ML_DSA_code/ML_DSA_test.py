"""
@Descripttion: ML_DSA 外部组件方案测试
@version: V1.0
@Author: HZW
@Date: 2025-03-14 15:30
"""

from ML_DSA import *

def test_ML_DSA():
 for params in [ML_DSA_44,ML_DSA_65,ML_DSA_87]:
        for _ in range(1):
            ML_DSA1=ML_DSA(params)
            pk,sk= ML_DSA1.KeyGen()
            
            expected_pk_len = 32 + 32 * params.k * ((q - 1).bit_length() - d)
            expected_sk_len = (32+32+64+32*((params.k+params.l)*(2*params.eta).bit_length()+d*params.k))
            
            assert len(pk) == expected_pk_len
            assert len(sk) == expected_sk_len
            
            M=os.urandom(32)
            ctx=os.urandom(54)
            sigma=ML_DSA1.Sign(sk, M, ctx)
            signature_len=(params.lambda_1//4+params.l*32*(1+(params.gamma_1-1).bit_length())+params.omega+params.k)
            
            assert len(sigma)== signature_len
            assert ML_DSA1.Verify(pk, M, sigma,ctx)== True