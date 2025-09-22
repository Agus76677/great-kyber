"""
@Descripttion: ML_DSA 内部组件方案
@version: V1.0
@Author: HZW
@Date: 2025-03-12 15:02
"""
from auxiliary_function import *

def KeyGen_internal(seed,params):
    """
    生成公钥-私钥对
    输入：
        32字节的种子seed-->xi,bytes类型
    输出：
    公钥pk,长度为32+32k(bitlen(q-1)-d)的字节数组;
    私钥sk,长度为32+32+64+32((l+k)bitlen(2η)+dk)的字节数组
    """
    random_seed = H(seed+InterToBytes(params.k,1)+InterToBytes(params.l,1)).read(128)
    rho, rhop, K = random_seed[:32],  random_seed[32:96],  random_seed[96:]
    
    A_hat = ExpandA(rho,params.k,params.l)
    s1, s2 = ExpandS(rhop,params.k,params.l,params.eta)
    t = A_hat.Matrix_Mul_DotNTT(s1.NTT()).INTT() + s2
    t1, t0 = t.Power2Round()

    pk = pkEncode(rho, t1, params.k)
    tr = H(pk).read(64)
    sk = skEncode(rho, K, tr, s1, s2, t0, params.k, params.l, params.eta)
    return (pk, sk)

def Sign_internal(sk, Mp, rnd, params):
    """
    以编码为字节数组的私钥sk,编码为bit数组的格式化消息M'以及32字节的随机数rnd作为输入,输出编码为字节数组的签名。
    """
    rho, K, tr, s1, s2, t0 = skDecode(sk, params.k, params.l, params.eta)
    s1_hat = s1.NTT()
    s2_hat = s2.NTT()
    t0_hat = t0.NTT()
    
    A_hat = ExpandA(rho, params.k, params.l)
    mu = H(tr+Mp).read(64)
    rhop = H(K+rnd+mu).read(64)
    ka=0
    alpha = params.gamma_2 << 1
    while True:
        y = ExpandMask(rhop, ka, params.l, params.gamma_1)
        w = A_hat.Matrix_Mul_DotNTT(y.NTT()).INTT()
        w1=w.HighBits(alpha)
        #上面这个是什么道理？
        ka+=params.l
        c_tie = H(mu + w1Encode(w1,params.k,params.gamma_2)).read(params.lambda_1//4)
        c =SampleInBall(c_tie, params.tau)
        c_hat = c.NTT()
        c_s1=s1_hat.ScalarVecNTT(c_hat).INTT()
        z = y +c_s1
        c_s2=s2_hat.ScalarVecNTT(c_hat).INTT()
        temp=w-c_s2
        r0=temp.LowBits(alpha)
        if z.Norm()>=(params.gamma_1-params.beta):
            # print("flag1")
            continue
        # print("r0.Norm:",r0.Norm())
        # print("params.gamma_2 - params.beta:",params.gamma_2 - params.beta)
        if r0.Norm()>=(params.gamma_2 -params.beta):
            # print("flag2")
            continue
        c_t0 = t0_hat.ScalarVecNTT(c_hat).INTT()
        if c_t0.Norm()>=(params.gamma_2):
            # print("flag3")
            continue
        temp2=w-c_s2+c_t0

        h = (-c_t0).MakeHint(temp2, alpha)
        if h.SumHint() > params.omega:
            # print("flag4")
            continue
        return sigEncode(c_tie, z.mod_pm(), h, params.k, params.l, params.gamma_1, params.omega)

def Verify_internal(pk, Mp, sigma, params):
    """
    验证来自字节编码的公钥和消息的签名
    """
    rho, t1 = pkDecode(pk, params.k)
    c_tie, z, h = sigDecode(sigma, params.lambda_1, params.gamma_1, params.l, params.omega, params.k)
    if h.SumHint() > params.omega:
        return False
    if z.Norm()>=(params.gamma_1-params.beta):
        return False
    #额外判断了z，为什么呢
    A_hat = ExpandA(rho, params.k, params.l)
    tr = H(pk).read(64)
    mu = H(tr + Mp).read(64)
    c =SampleInBall(c_tie, params.tau)
    temp1=A_hat.Matrix_Mul_DotNTT(z.NTT())
    temp2=t1.ScalarMult(1<<d).NTT().ScalarVecNTT(c.NTT())
    WApprox=(temp1-temp2).INTT()
    
    w1p = h.UseHint(WApprox, 2 * params.gamma_2)
    c_tie_p= H(mu+w1Encode(w1p, params.k, params.gamma_2)).read( params.lambda_1//4)
    return c_tie == c_tie_p