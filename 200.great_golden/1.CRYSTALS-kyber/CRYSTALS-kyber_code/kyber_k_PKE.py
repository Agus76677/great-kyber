"""
@Descripttion: CRYSTALS-kyber PKE组件方案
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""
from auxiliary_function import *

def k_PKE_KeyGen(seed, params):
    """
    输入：
        seed:32字节的种子d
        params:安全等级相关参数
    输出: 加密密钥ek_pke,解密密钥dk_pke
    """
    assert len(seed) == 32
    rho, sigma = G(seed+bytes(params.k))
    A_hat= sampleMatrix(rho, params.k)
    s = sampleNoise(sigma, params.eta1, 0, params.k) 
    e = sampleNoise(sigma, params.eta1, params.k, params.k) #N在内部变换，offset为params.k
    s_Hat = s.NTT() #多项式向量
    e_Hat = e.NTT() #多项式向量
    t_Hat =A_hat.Matrix_Mul_DotNTT(s_Hat) + e_Hat
    ek_pke = EncodeVec(t_Hat, 12) + rho
    dk_pke = EncodeVec(s_Hat, 12)
    return (ek_pke, dk_pke)

def k_PKE_Encrypt(ek_pke, m, r, params):
    """
    输入：
        ek_pke:加密密钥,384k+12长度的字节数组
        m:明文,32字节长度的字节数组 ,bytes类型
        r:随机参数,32字节长度的字节数组,bytes类型
    输出：
        c:密文,32(kdu+dv)字节长度的字节数组
    """
    assert len(m) == 32
    t_Hat = DecodeVec(ek_pke[:-32], params.k, 12)
    rho = ek_pke[-32:]
    A_hat = sampleMatrix(rho, params.k)  #多项式矩阵
    y = sampleNoise(r, params.eta1, 0, params.k)   #多项式向量，这些参数，从公式中看不出区别。但是是怎么选取的？
    e1 = sampleNoise(r, eta2, params.k, params.k)  #多项式向量
    e2 = sampleNoise(r, eta2, 2*params.k, 1).ps[0] #多项式，可能因为是单独生成多项式？
    y_Hat = y.NTT()
    u = A_hat.T().Matrix_Mul_DotNTT(y_Hat).INTT() + e1
    mu = Poly(ByteDecode(m, 1)).Decompress(1)
    v = t_Hat.Vec_DotNTT(y_Hat).INTT() + e2 + mu
    c1 = u.Compress(params.du).ByteEncode(params.du)
    c2 = v.Compress(params.dv).ByteEncode(params.dv)
    return c1 + c2

def k_PKE_Decrypt(dk_pke, c, params):
    """
    输入：
        dk_pke:解密密钥,384k
        c:密文,32(kdu+dv)字节长度的字节数组
    输出：
        m:明文,32字节长度的字节数组
    """
    split = params.du * params.k * n // 8
    c1, c2 = c[:split], c[split:]
    u = DecodeVec(c1, params.k, params.du).Decompress(params.du)# 注意这里有个k times
    v = DecodePoly(c2, params.dv).Decompress(params.dv)
    s_Hat = DecodeVec(dk_pke, params.k, 12)
    w = v - s_Hat.Vec_DotNTT(u.NTT()).INTT()
    m = w.Compress(1).ByteEncode(1)
    return m