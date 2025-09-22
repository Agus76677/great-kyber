"""
@Descripttion: CRYSTALS-kyber KEM内部算法
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""
from kyber_k_PKE import *

def ML_KEM_KeyGen_internal(seed, params):
    """
    输入：
        seed=d||Z,32字节的种子d,bytes类型,以及32字节的随机数Z
        params:安全等级相关参数
    输出: 封装密钥ek,解封装密钥dk
    """
    assert len(seed) == 64
    z = seed[32:]
    ek_pke, dk_pke = k_PKE_KeyGen(seed[:32], params)
    ek=ek_pke
    dk=dk_pke + ek + H(ek) + z
    return (ek,dk)

def ML_KEM_Encaps_internal(ek, m, params):
    """
    输入：
        ek:封装密钥,384k+12长度的字节数组
        m:32字节,随机性参数,bytes类型
    输出：
        K:32字节共享密钥
        c:密文
    """
    assert len(m) == 32
    K, r = G(m + H(ek))
    c =k_PKE_Encrypt(ek, m, r, params)
    return (K,c)

def ML_KEM_Decaps_internal(dk, c, params):
    """
    输入：
        dk:解封装密钥,768k+96长度的字节数组
        c:32(duk+dv)字节
    输出：
        K':32字节共享密钥
    """
    dk_pke = dk[:384 * params.k]
    ek_pke = dk[384 * params.k: 768 * params.k  + 32]
    h = dk[768 * params.k  + 32 : 768 * params.k  + 64]
    z = dk[768 * params.k  + 64 : 768 * params.k  + 96]
    mp = k_PKE_Decrypt(dk_pke, c, params)
    Kp, rp = G(mp + h)
    Kbar=J(z+bytes(c))
    cp = k_PKE_Encrypt(ek_pke, mp, rp, params)
    if c!=cp:
        Kp=Kbar
    return Kp