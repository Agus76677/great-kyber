"""
@Descripttion: ML_DSA 外部组件方案(external)
@version: V1.0
@Author: HZW
@Date: 2025-03-14 15:16
"""

from ML_DSA_internal import *
import os

class ML_DSA:
    def __init__(self, params):
        self.params = params
    
    def KeyGen(self):
        """
        除安全等级参数params以外,不接受任何输入
        输出:公钥pk,私钥sk
        """
        seed=os.urandom(32)
        if seed is None:
            return False
        pk, sk = KeyGen_internal(seed, self.params)
        return (pk, sk)
    
    def Sign(self,sk, M, ctx): 
        """
        输入:消息M,上下文ctx(小于等于255字节),bytes类型,sk私钥
        输出:签名sigma
        """
        if len(ctx)>255:
            return False
        
        rnd=os.urandom(32)
        if rnd is None:
            return False
        
        Mp=InterToBytes(0,1)+InterToBytes(len(ctx),1)+M
        sigma = Sign_internal(sk, Mp, rnd, self.params)
        return sigma

    def Verify(self, pk, M, sigma, ctx):
        """
        输入:消息M,上下文ctx(小于等于255字节),bytes类型,pk公钥,sigma签名
        输出:True/False
        """
        if len(ctx)>255:
            return False

        Mp=InterToBytes(0,1)+InterToBytes(len(ctx),1)+M
        return Verify_internal(pk, Mp, sigma, self.params)