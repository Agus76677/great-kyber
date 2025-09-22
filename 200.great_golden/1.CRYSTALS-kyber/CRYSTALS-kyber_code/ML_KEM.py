"""
@Descripttion: CRYSTALS-kyber KEM封装算法
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

from ML_KEM_internal import *
import os

class ML_KEM:
    def __init__(self, params):
        self.params = params

    def KeyGen(self):
        """
        除安全等级参数params以外,不接受任何输入
        输出:封装密钥ek,解封装密钥dk
        """
        d = os.urandom(32)
        z = os.urandom(32)
        assert len(d) == 32 and len(z) == 32 
        ek, dk = ML_KEM_KeyGen_internal(d+z,self.params)
        return (ek,dk)

    def Encaps(self,ek):
        """
        输入：
            ek:封装密钥,384k+12长度的字节数组
        输出：
            K:32字节共享密钥
            c:密文
        """
        m = os.urandom(32)
        assert len(m) == 32
        K,c=ML_KEM_Encaps_internal(ek,m,self.params)
        return (K,c)

    def Decaps(self, dk, c):
        """
        输入：
            dk:解封装密钥,768k+96长度的字节数组
            c:32(duk+dv)字节
        输出：
            K':32字节共享密钥
        """
        kp=ML_KEM_Decaps_internal(dk,c,self.params)
        return kp
