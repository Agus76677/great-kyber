"""
@Descripttion: CRYSTALS-kyber 辅助函数
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

from Crypto.Hash import SHAKE128, SHAKE256

import hashlib
import collections
from math import floor

q = 3329     # 模数
nBits = 8   
zeta = 17    # NTT变换中使用的单位根
eta2 = 2     # 噪声参数

n = 2**nBits  # 多项式环的维度（256）
inv2 = 3303  # inverse of 2

# 通过元组定义不同安全等级的参数集合
params = collections.namedtuple('params', ('k', 'du', 'dv', 'eta1'))

params512  = params(k = 2, du = 10, dv = 4, eta1 = 3)
params768  = params(k = 3, du = 10, dv = 4, eta1 = 2)
params1024 = params(k = 4, du = 11, dv = 5, eta1 = 2)
##########################################-辅助函数定义-########################################
# 定义smod,即mod_+，输出结果在[-q/2,q/2]之间
def smod(x):
    r = x % q      
    if r > (q-1)//2:
        r -= q
    return r

# 舍入函数,[1.5,2.5) -> 2
def Round(x):
    return int(floor(x + 0.5))

# 压缩函数,将x压缩为d字长的整数，降低通信带宽
def Compress(x, d):
    return Round((2**d / q) * x) % (2**d)

# 解压缩函数
def Decompress(y, d):
    assert 0 <= y and y <= 2**d
    return Round((q / 2**d) * y)

#bit流转字节流或者字节数组
def BitsToBytes(b, w):
    '''
    b:bit数组,小端存储
    W:字长,8
    B:字节数组
    '''
    assert len(b) % w == 0
    t=len(b)//w
    B=[0]*t
    for i in range(t):
        for j in range(w):
            B[i]+=b[i*w+j] * 2**j
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

# 编码
def ByteEncode(F, d):
    '''
    F:256长度的整数列表,元素位宽为d bit
    d:压缩参数
    B:32d的字节数组,输出为字节序列
    '''
    return BitsToBytes(BytesToBits(F, d), 8)

def ByteEncode_bytes(F, d):
    '''
    F:256长度的整数列表,元素位宽为d bit
    d:压缩参数
    B:32d的字节数组,输出为字节序列,bytes类型
    '''
    return bytes(BitsToBytes(BytesToBits(F, d), 8))

#解码 
def ByteDecode(B, d):
    '''
    B:32d的字节数组
    d:压缩参数
    F:256长度的整数列表,元素位宽为d bit
    '''
    return BitsToBytes(BytesToBits(B, 8), d)

# 位反序函数
def brv(x):
    """ Reverses a 7-bit number """
    return int(''.join(reversed(bin(x)[2:].zfill(nBits-1))), 2)


# 均匀采样
def sampleNTT(stream):
    """
    从stream获取字节流生成12bit字长的数据,作为多项式系数
    返回值:返回一个长度为n的多项式对象的NTT形式
    """
    cs = []
    while True:
        C = stream.read(3)  #获取3个字节的数据
        d1 = C[0] + 256*(C[1] % 16)
        d2 = (C[1] >> 4) + 16*C[2]
        assert d1 + 2**12 * d2 == C[0] + 2**8 * C[1] + 2**16*C[2]
        for d in [d1, d2]:
            if d >= q:
                continue#退回到while
            cs.append(d)
            if len(cs) == n:
                return Poly(cs)

# 中心二项分布采样
def samplePolyCBD(B, eta):
    """
    由64*eta长度的B字节数组返回一个多项式对象
    B:64eta长度的字节数组
    f:多项式
    """
    assert len(B) == 64*eta
    b = BytesToBits(B, 8)
    cs = []
    for i in range(n):
        cs.append((sum(b[:eta]) - sum(b[eta:2*eta])) % q)
        b = b[2*eta:]
    return Poly(cs)

# 可扩展输出函数，XOF，B*xBxB->B*
def XOF(seed, j, i):
    '''
    返回一个SHAHE128哈希对象,
    该对象是基于keccak算法的可扩展输出函数,
    可以产生任意长度的输出
    可以通过read方法获取任意长度的输出(h.read(12))
    '''
    h = SHAKE128.new()  
    h.update(seed + bytes([j, i]))
    return h

# 伪随机函数，PRF，B^32XB->B*
def PRF(seed, nonce):
    '''
    返回一个SHAHE256哈希对象,
    该对象是基于keccak算法的可扩展输出函数,
    可以产生任意长度的输出
    可以通过read方法获取任意长度的输出(h.read(12))
    '''
    assert len(seed) == 32
    h = SHAKE256.new()
    h.update(seed + bytes([nonce]))
    return h

def J(seed): 
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

def G(seed):
    h = hashlib.sha3_512(seed).digest()
    return h[:32], h[32:]
#没啥用的哈希生成函数
def H(msg): return hashlib.sha3_256(msg).digest()
#没啥用的哈希生成函数
def KDF(msg): return hashlib.shake_256(msg).digest(length=32)

##########################################-定义多项式函数类-########################################
class Poly: #操作的数据结构为Rq或者Z_q^256
    # 初始化一个
    def __init__(self, cs=None):
        self.cs = (0,)*n if cs is None else tuple(cs)
        assert len(self.cs) == n
    
    # 定义多项式加法
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
        i = 1
        while len >= 2:
            for start in range(0, n, 2*len):
                zeta1 = pow(zeta, brv(i), q)
                i += 1

                for j in range(start, start+len):
                    t = (zeta1 * f[j + len]) % q
                    f[j + len] = (f[j] - t) % q
                    f[j] = (f[j] + t) % q
            len //= 2
        return Poly(f)
    

    def RefNTT(self):
        # Slower, but simpler, version of the NTT.
        cs = [0]*n
        for i in range(0, n, 2):
            for j in range(n // 2):
                z = pow(zeta, (2*brv(i//2)+1)*j, q)
                cs[i] = (cs[i] + self.cs[2*j] * z) % q
                cs[i+1] = (cs[i+1] + self.cs[2*j+1] * z) % q
        return Poly(cs)

    def INTT(self):
        """
        输入:多项式NTT形式系数向量f_hat元组
        输出:多项式系数f元组
        """
        f_hat = list(self.cs)
        len = 2
        i = n//2-1
        while len <= n//2:
            for start in range(0, n, 2*len):
                
                zeta1 = pow(zeta, brv(i), q)
                i -= 1
                
                for j in range(start, start+len):
                    t = f_hat[j]
                    f_hat[j] = (t + f_hat[j+len]) % q
                    f_hat[j+len] = (zeta1*(f_hat[j+len]-t)) % q
            len *= 2
        for i in range(n):
            f_hat[i]=f_hat[i]*inv2 %q
        return Poly(f_hat)

    def PWM(self, other):
        """
        执行PWM
        输入:两个多项式的NTT形式 
        输出:多项式乘积的NTT形式 
        """
        h_hat = [None]*n
        for i in range(0, n, 2):
            a1 = self.cs[i]
            a2 = self.cs[i+1]
            b1 = other.cs[i]
            b2 = other.cs[i+1]
            gama = pow(zeta, 2*brv(i//2)+1, q)
            h_hat[i] = (a1 * b1 + gama * a2 * b2) % q
            h_hat[i+1] = (a2 * b1 + a1 * b2) % q
        return Poly(h_hat)

    def Compress(self, d):
        """
        重载压缩函数，对每个系数进行压缩 
        输入:多项式系数向量,压缩比例d
        输出:压缩后的多项式系数向量,压缩比例d
        """
        return Poly(Compress(c, d) for c in self.cs)

    def Decompress(self, d):
        """
        重载解压缩函数，对每个系数进行解压缩 
        输入:压缩后的多项式系数向量,压缩比例d
        输出:多项式系数向量,压缩比例d
        """
        return Poly(Decompress(c, d) for c in self.cs)

    def ByteEncode(self, d):
        return ByteEncode_bytes(self.cs, d)

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

    def Vec_DotNTT(self, other):
        """ 计算PWM<self, other> in NTT domain. """
        return sum((a.PWM(b) for a, b in zip(self.ps, other.ps)),
                   Poly())

    def __add__(self, other):
        return Vec(a+b for a,b in zip(self.ps, other.ps))

    def Compress(self, d):
        return Vec(p.Compress(d) for p in self.ps)

    def Decompress(self, d):
        return Vec(p.Decompress(d) for p in self.ps)

    def ByteEncode(self, d):
        return ByteEncode_bytes(sum((p.cs for p in self.ps), ()), d)

    def __eq__(self, other):
        return self.ps == other.ps
    
    def __str__(self):
        # 直接调用每个 Poly 对象的 __str__ 方法，生成 "Poly(...)" 格式的字符串
        poly_strings = [str(p) for p in self.ps]
        return f"Vec({', '.join(poly_strings)})"

def EncodeVec(vec, d):
    return ByteEncode_bytes(sum([p.cs for p in vec.ps], ()), d)

def DecodeVec(B, k, d):
    F = ByteDecode(B, d)
    return Vec(Poly(F[n*i:n*(i+1)]) for i in range(k))

def DecodePoly(B, d):
    return Poly(ByteDecode(B, d))

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

#通过均匀采样生成多项式矩阵A_hat
def sampleMatrix(rho, k):
    return Matrix([[sampleNTT(XOF(rho, j, i))
            for j in range(k)] for i in range(k)])

#通过中心二项采样生成噪声多项式或噪声多项式向量
def sampleNoise(sigma, eta, offset, k):
    return Vec(samplePolyCBD(PRF(sigma, i+offset).read(64*eta), eta)
               for i in range(k))

def constantTimeSelectOnEquality(a, b, ifEq, ifNeq):
    # WARNING! In production code this must be done in a
    # data-independent constant-time manner, which this implementation
    # is not. In fact, many more lines of code in this
    # file are not constant-time.
    return ifEq if a == b else ifNeq