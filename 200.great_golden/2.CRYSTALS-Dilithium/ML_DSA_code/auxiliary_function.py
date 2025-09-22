"""
@Descripttion: ML_DSA 辅助函数
@version: V1.0
@Author: HZW
@Date: 2025-03-11 20:25:00
"""
from Crypto.Hash import SHAKE128, SHAKE256

import math
import collections
import numpy as np

q = 8380417     # 模数
nBits = 8   
zeta = 1753    # NTT变换中使用的单位根
d = 13         # 公钥多项式系数舍弃的bit数``
n = 2**nBits  # 多项式环的维度（256）
inv2 =8347681 # 256^-1mod q

# 通过元组定义不同安全等级的参数集合
params = collections.namedtuple('params', ('tau', 'lambda_1', 'gamma_1', 'gamma_2', 'k', 'l', 'eta', 'beta', 'omega'))

ML_DSA_44 = params(tau=39, lambda_1=128, gamma_1=131072, gamma_2=95232,  k=4, l=4, eta=2, beta=78,  omega=80)
ML_DSA_65 = params(tau=49, lambda_1=192, gamma_1=524288, gamma_2=261888, k=6, l=5, eta=4, beta=196, omega=55)
ML_DSA_87 = params(tau=60, lambda_1=256, gamma_1=524288, gamma_2=261888, k=8, l=7, eta=2, beta=120, omega=75)

################################-数据类型转换函数-########################
# InterToBits
def InterToBits(x, a):
    """
    x: 输入的非负整数
    a: 输出的bit数组长度
    y: 输出的bit数组,小端存储
    """
    y=[0]*a
    for i in range(a):
        y[i] = x%2 
        x=x//2
    return y

# BitsToInter
def BitsToInter(y,a):
    """
    y: 输入的bit数组,小端存储
    a: 输入的bit数组长度
    x: 输出的非负整数
    """
    x=0
    for i in range(0,a):
        x = 2*x+y[a-i-1]
    return x

# InterToBytes
def InterToBytes(x, a):
    """
    x: 输入的非负整数
    a: 输出的byte数组长度
    y: 输出的byte数组,小端存储
    """
    y=[0]*a
    for i in range(a):
        y[i] = x%256 
        x=x//256
    return bytes(y)


#bit流转字节流或者字节数组
def BitsToBytes(y, w):
    '''
    y:bit数组,小端存储
    W:字长,8
    B:字节数组
    '''
    t=math.ceil(len(y)/w)
    B=[0]*t
    for i in range(len(y)):
            byte_index = i // w
            bit_position = i % w
            B[byte_index]+=y[i]*(2**bit_position)
    return B
          

# 字节数组转bit流
def BytesToBits(B, w):
    '''
    B为w字长字节数组
    w:字长,8
    b:bit数组
    '''
    b = [0] * (len(B) * w)
    for i in range(len(B)):
        t=B[i]
        for j in range(w):
            b[w*i+j]=t %2
            t=t>>1
    return b


# CoeffFromThreeBytes(b0,b1,b2)
def CoeffFromThreeBytes(b0, b1, b2, q):
    """
    b0, b1, b2: 三个字节
    用于生成多项式的系数
    """
    if b2 > 127:
        b2 -= 128  # 将b2转换为0-127之间的数
    z = (2 ** 16) * b2 + (2 ** 8) * b1 + b0
    if z < q:
        return z
    else:
        return False  # 表示⊥
    
# CoeffFromHalfBytes(b)
def CoeffFromHalfBytes(b, eta):
    """
    将元素b转换到[−η,η],用于生成多项式系数(拒绝采样)
    """
    if eta == 2 and b < 15:
        return 2 - (b % 5)
    elif b < 9:
        assert eta == 4
        return 4 - b
    return False

#SimpleBitPack
def SimpleBitPack(w,b):
    """
    输入：
        b:整数
        w:多项式系数数组,其中系数的取值范围为[0,b]
    输出：
        32*bitlen(b)的字节数组,bytes类型
    功能:将多项式系数数组w编码为字节数组
    """
    z=[]
    for i in range(256):
        z.extend(InterToBits(w.cs[i],b.bit_length()))
    return bytes(BitsToBytes(z,8))
# 显然，这个b可以是模数q。

#BitPack
def BitPack(w,a,b):
    """
    输入：
        a,b:整数
        w:多项式系数数组，其中系数的取值范围为[-a,b]
    输出：
        32*bitlen(a+b)的字节数组
    功能:将多项式系数数组w编码为字节数组
    """
    z=[]
    for i in range(256):
        z.extend(InterToBits(b-w.cs[i],(a+b).bit_length()))
    return bytes(BitsToBytes(z,8))

#SimpleBitUnPack
def SimpleBitUnPack(v,b):
    """
    输入：
       b:整数
       v:字节数组,长度为32 bitlen(b)
    输出：
        多项式w,系数的范围为[0,2^bitlen(b)-1]
    功能:SimpleBitPack的逆过程
    """
    c = b.bit_length()
    z=BytesToBits(v,8)
    w=[0]*256
    for i in range(256):
        w[i]=BitsToInter(z[i*c:(i+1)*c],c)
    return Poly(w)
# 定义到ploy类中的函数
    
#BitUnPack
def BitUnPack(v,a,b):
    """
    输入：
       a,b:整数
       v:字节数组,长度为32 bitlen(a+b)
    输出：
        多项式w,系数的范围为[b-2^bitlen(a+b)+1,b]
    
    """
    c = (a + b).bit_length()
    z=BytesToBits(v,8)
    w=[0]*256
    for i in range(256):
        w[i]=b-BitsToInter(z[i*c:(i+1)*c],c)
    return Poly(w)

#HintBitpack
def HintBitpack(h,w,k):
    """
    功能:将一个具有二进制系数的多项式向量编码为字节数组
    输入:长度为k的多项式向量系数数组(h[0],…,h[k-1]),其中h[i]为长度为256的多项式系数数组。
        其中多项式向量系数数组至多有w个非零系数。
    输出:长度为w+k的字节数组y,前w的元素记录非零位置
         后k个字节用于记录每个h[i]中多少个非零bit
    """
    y=[0]*(w+k)
    index=0
    for i in range(k):
        for j in range(256):
            if(h.ps[i].cs[j]!=0):
                y[index]=j
                index+=1
        y[w+i]=index        
    return y
#h是二维的，需要经历两次索引。

#HintBitUnPack
def HintBitUnPack(y,w,k):
    """
    功能:HintBitpack的逆过程
    """
    h=Vec([Poly() for _ in range(k)])
    index=0
    for i in range(k): 
        if y[w+i]<index or y[w+i]>w:
            return False
        First=index
        while index<y[w+i]:
            if index>First:
                if y[index-1]>=y[index]:
                    return False
            # h.ps[i].cs[y[index]]=1
            current_cs = list(h.ps[i].cs)       # 元组转列表（因为元组不可修改）
            current_cs[y[index]] = 1            # 修改列表元素
            h.ps[i].cs = tuple(current_cs)      # 列表转回元组
            index+=1
    
    for i in range(index,w):
        if(y[i]!=0):
            return False      
    return h 


# 位反序函数
def brv(x):
    """ Reverses a 8-bit number """
    return int(''.join(reversed(bin(x)[2:].zfill(nBits))), 2)

# 可扩展输出函数G
def G(seed):
    '''
    返回一个SHAHE128哈希对象,
    该对象是基于keccak算法的可扩展输出函数,
    可以产生任意长度的输出
    可以通过read方法获取任意长度的输出(h.read(1))
    '''
    h = SHAKE128.new()  
    h.update(seed)
    return h

def H(seed): 
    '''
    B*->B^32
    返回一个SHAHE256哈希对象,
    该对象是基于keccak算法的可扩展输出函数,
    可以产生任意长度的输出
    可以通过read方法获取任意长度的输出(h.read(32))
    '''
    h = SHAKE256.new()
    h.update(seed)
    return h

##########################################-高阶位和低阶位提示-########################################
def mod_pm(x, n):
    """
    结果： r = x % n
    for n odd:
        -(n-1)/2 < r <= (n-1)/2
    for n even:
        - n / 2  <= r <= n / 2
    """
    x = x % n
    if x > (n >> 1):
        x -= n
    return x
#定义了之前正负模的操作。
 
#Power2Round
def Power2Round(r):
    """
    输入：
        整数环上的r
    输出： 
        r1,r0:r同余 r1*2^d+r0 mod q
    """
    rp=r % q
    r0=mod_pm(rp,1<<d)
    r1=(rp-r0)>>d
    return (r1,r0)

#Decompose
def Decompose(r, a):
    """
    a=2*gamma_2
    r = r1*a + r0
    -(a << 1) < r0 <= (a << 1)
    """
    rp = r % q
    r0 = mod_pm(rp, a)
    if rp - r0 == q - 1:
        r1 = 0
        r0 = r0 - 1
    else:
        r1 = (rp - r0) // a
    return (r1, r0)


def HighBits(r, a):
    r1, _ = Decompose(r, a)
    return r1


def LowBits(r, a):
    _, r0 = Decompose(r, a)
    return r0


def MakeHint(z, r, a):
    """
    用于判断向r中添加z是否改变r的高位
    """
    r1 = HighBits(r, a)
    v1 = HighBits(r + z, a)
    return int(r1 != v1)

#直接计算提示位，而不是实际的高位bit计算，提高运行效率
def make_hint_optimised(z0, r1, a):
    gamma2 = a >> 1
    if z0 <= gamma2 or z0 > (q - gamma2) or (z0 == (q - gamma2) and r1 == 0):
        return 0
    return 1


def UseHint(h, r, a):
    m = (q - 1) // a
    r1, r0 = Decompose(r, a)
    if h == 1:
        if r0 > 0:
            return (r1 + 1) % m
        return (r1 - 1) % m
    return r1


def CheckNormBound(n, b):
    """
    x ∈ {0,        ...,                    ...,     q-1}
    x ∈ {-(q-1)/2, ...,       -1,       0, ..., (q-1)/2}
    x ∈ { (q-3)/2, ...,        0,       0, ..., (q-1)/2}
    x ∈ {0, 1,     ...,  (q-1)/2, (q-1)/2, ...,       1}
    """
    x = n % q
    x = ((q - 1) >> 1) - x
    x = x ^ (x >> 31)
    x = ((q - 1) >> 1) - x
    return x >= b

#求解无穷范数
def Norm(x,q):
    x=mod_pm(x,q)
    return abs(x)

##########################################-定义多项式函数类-########################################
class Poly: #操作的数据结构为Rq或者Z_q^256
    # 初始化一个
    def __init__(self, cs=None):
        self.cs = (0,)*n if cs is None else tuple(cs)
        assert len(self.cs) == n
    
    # 定义多项式加法（AddNTT）
    def __add__(self, other):
        return Poly((a+b) % q for a,b in zip(self.cs, other.cs))
    
    # 多项式系数取反
    def __neg__(self):
        return Poly(q-a for a in self.cs)
    
    # 多项式减法
    def __sub__(self, other):
        return self + -other

    # 返回多项式字符串
    def __str__(self):
        return f"Poly{self.cs}"

    # 比较两个多项式是否相等
    def __eq__(self, other):
        return self.cs == other.cs

    # 定义数论变换
    def NTT(self):
        """
        输入:多项式系数f元组
        输出:多项式NTT形式系数向量f_hat元组
        """
        f = list(self.cs) # 元组不可修改，把元组转为列表
        len = n // 2
        i = 0
        while len >= 1:
            for start in range(0, n, 2*len):
                i += 1
                zeta1 = pow(zeta, brv(i), q)
                
                for j in range(start, start+len):
                    t = (np.int64(zeta1) * np.int64(f[j + len])) % q
                    f[j + len] = (f[j] - t) % q
                    f[j] = (f[j] + t) % q
            len //= 2
        return Poly(f)

    def INTT(self):
        """
        输入:多项式NTT形式系数向量f_hat元组
        输出:多项式系数f元组
        """
        f_hat = list(self.cs)
        len = 1
        i = n
        while len <n:
            for start in range(0, n, 2*len):
                i -= 1
                zeta1 = pow(zeta, brv(i), q)
                
                for j in range(start, start+len):
                    t = f_hat[j]
                    f_hat[j] = (t + f_hat[j+len]) % q
                    f_hat[j+len] = (np.int64(zeta1)*np.int64(f_hat[j+len]-t)) % q
            len *= 2
        for i in range(n):
            f_hat[i]=np.int64(f_hat[i])*np.int64(inv2) %q
        return Poly(f_hat)

    def MultiplyNTT(self, other):
        """
        输入:两个多项式的NTT形式 
        输出 C:多项式NTT形式的PWM点乘结果
        """
        c=[0]*256
        for i in range(n):
            c[i] = (self.cs[i] * other.cs[i]) % q
        return Poly(c)
    
    
    def ScalarMult(self, a):
        """
        a:为常数
        """
        return Poly(r*a for r in self.cs)
        
    
    def Power2Round(self):
        r0=[]
        r1=[]
        for r in self.cs:
            t1,t0=Power2Round(r)
            r0.append(t0)
            r1.append(t1)
        return Poly(r1),Poly(r0)
    #拆分成了两个多项式
    
    def HighBits(self, a):
        return Poly(HighBits(r, a) for r in self.cs)
    
    def LowBits(self,a):
        return Poly(LowBits(r, a) for r in self.cs)
    
    def MakeHint(self,other,a):
        return Poly(MakeHint(r, z, a) for r,z in zip(self.cs,other.cs))
    
    def UseHint(self,other,a):
        return Poly(UseHint(h, r, a) for h,r in zip(self.cs,other.cs))
    
    def CheckNormBound(self, bound):
        """
        任何一个系数超过边界则返回true
        """
        return any(CheckNormBound(r, bound) for r in self.cs)
    
    def SumHint(self):
        return sum(self.cs)
    
    #求解多项式的无穷范数
    def Norm(self):
        max_norm=0
        for r in self.cs:
            current_norm = Norm(r,q)
            max_norm = max(max_norm, current_norm)  # 递推更新
        return max_norm
    
    # 定义一个函数mod_pm
    def mod_pm(self):
        return Poly(mod_pm(r,q) for r in self.cs)
##########################################-定义多项式向量类，将多项式操作重载为多项式向量操作-########################################
#操作的数据结构为Rq^k或者(Z_q^256)^k
class Vec:
    """
    变量说明：
    ps:多项式向量([1,2,0,...,100],[1,4,0,...,101],.......,[1,5,0,...,105])
    p:多项式[1,2,0,...,100]
    """
    def __init__(self, ps):
        self.ps = tuple(ps)

    def NTT(self):
        return Vec(p.NTT() for p in self.ps)

    def INTT(self):
        return Vec(p.INTT() for p in self.ps)
    
    def ScalarVecNTT(self, other):
        """ 计算多项式和多项式向量的标量乘法. """
        return Vec([a.MultiplyNTT(other) for a in self.ps])
    
    def ScalarMult(self,a):
        return Vec(r.ScalarMult(a) for r in self.ps)
        

    def Vec_DotNTT(self, other):
        """ 计算PWM<self, other> in NTT domain. """
        return sum((a.MultiplyNTT(b) for a, b in zip(self.ps, other.ps)),
                   Poly())

    def __add__(self, other): ##(AddVectorNTT)
        return Vec(a+b for a,b in zip(self.ps, other.ps))
    
    def __sub__(self, other): ##(SubVectorNTT)
        return Vec(a-b for a,b in zip(self.ps, other.ps))
    
    # 多项式向量系数取反
    def __neg__(self):
        return Vec([-a for a in self.ps])
    
    
    def __eq__(self, other):
        return self.ps == other.ps
    
    def __str__(self):
        # 直接调用每个 Poly 对象的 __str__ 方法，生成 "Poly(...)" 格式的字符串
        poly_strings = [str(p) for p in self.ps]
        return f"Vec({', '.join(poly_strings)})"
    
    def Power2Round(self):
        r0=[]
        r1=[]
        for r in self.ps:
            t1,t0=r.Power2Round()
            r0.append(t0)
            r1.append(t1)
        return Vec(r1),Vec(r0)
    
    def HighBits(self, a):
        return Vec(r.HighBits(a) for r in self.ps)
    
    def LowBits(self,a):
        return Vec(r.LowBits(a) for r in self.ps)
    
    def MakeHint(self,other,a):
        return Vec(r.MakeHint(z, a) for r,z in zip(self.ps,other.ps))
    
    def UseHint(self,other,a):
        return Vec(h.UseHint(r, a) for h,r in zip(self.ps,other.ps))
    
    def CheckNormBound(self, bound):
        """
        任何一个系数超过边界则返回true
        """
        for r in self.ps:
            if r.CheckNormBound(bound):
                return True
        return False 
    
    def SumHint(self):
        return sum(r.SumHint() for r in self.ps)
    
    def Norm(self):
        max_norm=0
        for r in self.ps:
            current_norm = r.Norm()
            max_norm = max(max_norm, current_norm)  # 递推更新
        return max_norm  
    
    # 定义一个函数mod_pm
    def mod_pm(self):
        return Vec(r.mod_pm() for r in self.ps)
##########################################-定义多项式矩阵类，将多项式操作重载为多项式矩阵操作-########################################
#操作的数据结构为Rq^(k*k)或者(Z_q^256)^(k*k）
class Matrix:
    """
    cs: [
        [[1, 2, 0], [1, 2, 0]],  
        [[1, 5, 0], [2, 1, 0]]
        ]
    """
    def __init__(self, cs):
        """ 
        将多项式式矩阵A_hat转换为元组
        """
        self.cs = tuple(tuple(row) for row in cs)
    
    def __str__(self):
        # 获取矩阵的行数和列数
        rows = len(self.cs)
        cols = len(self.cs[0]) if rows > 0 else 0

        # 生成每一行的字符串表示
        matrix_rows = []
        for row in self.cs:
            poly_strings = [f"Poly({', '.join(map(str, p.cs))})" for p in row]
            matrix_rows.append(" ".join(poly_strings))

        # 将所有行组合成一个字符串
        matrix_str = "Matrix(\n"
        matrix_str += "  " + ",\n  ".join(matrix_rows) + "\n)"
        return matrix_str

    def Matrix_Mul_DotNTT(self, vec):
        """计算矩阵向量乘法 A*vec in the NTT domain. """
        return Vec(Vec(row).Vec_DotNTT(vec) for row in self.cs)

    def T(self):
        """ Returns transpose of matrix """
        k = len(self.cs)
        return Matrix((self.cs[j][i] for j in range(k))
                      for i in range(k))

##########################################-ML_DSA密钥和签名的编码函数-########################################
#pkEncode
def pkEncode(rho,t_1,k):
    """
    将公钥编码为字节数组
    rho:长度为32的字节数组,t_1长度为k的多项式向量,系数范围为[0,2^(bitlen(q-1)-d)-1]
    pk:公钥字节数组
    """
    pk=rho
    b=2**((q-1).bit_length()-d)-1
    for i in range(k):
        pk+=SimpleBitPack(t_1.ps[i],b)
    return pk

#pkDecode
def pkDecode(pk,k):
    """
    将编码后的公钥解码出来
    输入：
        pk:公钥字节数组
    输出：
        rho:长度为32的字节数组
        t_1:长度为k的多项式向量,系数范围为[0,2^(bitlen(q-1)-d)-1]
    """
    pk=list(pk)
    temp=((q-1).bit_length()-d)
    b=2**temp-1
    rho=bytes(pk[0:32])
    t_1=Vec([SimpleBitUnPack(pk[32+32*i*temp:32+32*(i+1)*temp],b) for i in range(k)])
    return (rho,t_1)

#skEncode
def skEncode(rho,K,tr,s1,s2,t0,k,l,eta):
    """
    Args:
        rho:长度为32的字节数组,bytes类型
        K  :长度为32的字节数组,bytes类型
        tr :长度为64的字节数组,bytes类型
        s1 :长度为l的多项式向量,系数范围为[-eta,eta]
        s2 :长度为k的多项式向量,系数范围为[-eta,eta]
        t0 :长度为k的多项式向量,系数范围为[-2^(d-1)+1,2^(d-1)]
    Returns:
        sk:编码的私钥,字节数组
    """
    sk=rho+K+tr
    temp=2**(d-1)
    for i in range(l):
        sk+=BitPack(s1.ps[i],eta,eta)
    for i in range(k):
        sk+=BitPack(s2.ps[i],eta,eta)
    for i in range(k):
        sk+=BitPack(t0.ps[i],temp-1,temp)
    return sk

#skDecode
def skDecode(sk,k,l,eta):
    """
    skEncode的逆过程
    """
    temp=32*(2*eta).bit_length()
    temp1=2**(d-1)
    sk=list(sk)
    rho=bytes(sk[0:32])
    K=bytes(sk[32:64])
    tr=bytes(sk[64:128])
    y=sk[128:128+temp*l]
    z=sk[128+temp*l:128+temp*(l+k)]
    w=sk[128+temp*(l+k):]
    s1=Vec([BitUnPack(y[i*temp:(i+1)*temp],eta,eta) for i in range(l)])
    s2=Vec([BitUnPack(z[i*temp:(i+1)*temp],eta,eta) for i in range(k)])
    t0=Vec([BitUnPack(w[i*32*d:(i+1)*32*d],temp1-1,temp1) for i in range(k)])
    return (rho,K,tr,s1,s2,t0)

#sigEncode
def sigEncode(c_tie,z,h,k,l,gamma_1,omega):
    """
    输入：
        c_tie:lambda/4长度的字节数组
        z:长度为l的多项式向量,系数范围为[-gamma_1+1,gamma_1]
        h:长度为l的多项式向量提示,系数取值可能为{0,1}
        k,l,gamma_1,omega:安全参数
    输出:
        sigma:签名,字节数组,bytes类型
    功能:对前面和提示进行编码
    """
    sigma=c_tie
    for i in range(l):
        sigma+=BitPack(z.ps[i],gamma_1-1,gamma_1)
    sigma+=bytes(HintBitpack(h,omega,k))
    return sigma

#sigDecode
def sigDecode(sigma,lambda_1,gamma_1,l,omega,k):
    """
    sigEncode的逆过程
    """
    temp=32*(1+(gamma_1-1).bit_length())
    temp1=lambda_1//4
    c_tie=sigma[0:temp1]
    x=sigma[temp1:temp1+temp*l]
    y=sigma[temp1+temp*l:]
    z=Vec([BitUnPack(x[i*temp:(i+1)*temp],gamma_1-1,gamma_1) for i in range(l)])
    h=HintBitUnPack(y,omega,k)
    return (c_tie,z,h)
    
#w1Encode
def w1Encode(w1,k,gamma_2):
    """
    输入：
        w1:长度为k的多项式向量,系数范围为[0,(q-1)/2*gamma_1-1]
    输出：
        w1_tie:编码后的字节数组,bytes类型
    """
    temp=(q-1)//(2*gamma_2)-1
    w1_tie=b'' # 初始化空白的字节
    for i in range(k):
         w1_tie+=SimpleBitPack(w1.ps[i],temp)
    return w1_tie
##########################################-定义采样函数-########################################
# SampleInBall
def SampleInBall(rho, tau):
    """
    rho: 用于生成多项式的种子,长度为lambda_1/4
    tau: 碰撞强度
    c: 多项式系数,长度为256,每个系数为0或者1或者-1
    """
    c = [0] * 256
    ctx=H(rho)
    s=ctx.read(8)
    h=BytesToBits(s,8)
    
    #拒绝采样
    for i in range(256 - tau, 256):
        j=ctx.read(1)[0]
        while j>i:
            j=ctx.read(1)[0]
        c[i]=c[j]
        c[j]=(-1)**h[i+tau-256]
    return Poly(c)

#RejNTTPoly
def RejNTTPoly(rho):
    """
    rho: 用于生成多项式的种子,长度为34字节,32字节为随机种子,2字节为位置索引
    a_hat:多项式的NTT形式系数表示
    """
    a_hat = [0] * 256
    ctx=G(rho) 
    #拒绝采样
    j=0
    while j<256:
        s=ctx.read(3)
        a_hat[j]=CoeffFromThreeBytes(s[0],s[1],s[2],q)
        if a_hat[j] != False:
            j+=1
    return Poly(a_hat)


#RejBoundedPoly
def RejBoundedPoly(rho, eta):
    """
    rho: 用于生成多项式的种子,长度为66字节
    a:多项式的系数表示
    """
    a = [0] * 256
    ctx=H(rho)
    j=0
    while j < 256:
        z = ctx.read(1)[0]
        z0 = CoeffFromHalfBytes(z % 16, eta)
        z1 = CoeffFromHalfBytes(z // 16, eta)
        if z0 is not False:
            a[j] = z0
            j += 1
            
        if z1 is not False and j < 256:
            a[j] = z1
            j += 1
    return Poly(a)

#ExpandA
def ExpandA(rho,k,l):
    """
    rho: 用于生成多项式的种子,长度为32字节
    k,l: 矩阵的行列数
    A_hat:多项式矩阵的NTT形式系数表示
    """
    return Matrix([[RejNTTPoly(rho+bytes(s)+bytes(r)) for s in range(l)]  
                   for r in range(k)])  ##用不上InterToBytes
    
#ExpandS
def ExpandS(rho,k,l,eta):
    """
    rho: 用于生成多项式的种子,长度为64字节
    s_1:长度为l多项式向量的系数表示
    s_2:长度为k多项式向量的系数表示
    """
    s_1=Vec([RejBoundedPoly(rho+InterToBytes(r,2),eta) for r in range(l)])
    s_2=Vec([RejBoundedPoly(rho+InterToBytes(r+l,2),eta) for r in range(k)])
    return (s_1,s_2) 

#ExpandMask
def ExpandMask(rho,mu,l,gamma_1):
    """
    rho: 用于生成多项式的种子,长度为64字节
    mu:非负整数
    y:长度为l多项式向量的系数表示,系数范围为[-gama_1+1,gama_1]
    """
    y = []
    c=1+(gamma_1-1).bit_length()
    for r in range(l):
        rho_p=rho+InterToBytes(mu+r,2)
        v=H(rho_p).read(32*c)
        y.append(BitUnPack(v,gamma_1-1,gamma_1))
    return Vec(y)