import pytest
import numpy as np

import io
import random
from auxiliary_function import *

x = 1000
d = 10
compressed = Compress(x, d)
decompressed = Decompress(compressed, d)
print(compressed)
print(decompressed)
bits = [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1]
bytes_ = BitsToBytes(bits, 8)
print(bits)
print(bytes_)
F = np.random.randint(0, 3329, size=4)
d = 12
encoded = ByteEncode(F, d)
decoded = ByteDecode(encoded, d)
print(F)
print(encoded)
print(decoded)
tmp = hashlib.shake_128(b'').digest(1344) # 生成1344字节长度的哈希值
tmp2 = io.BytesIO(hashlib.shake_128(b'').digest(1344)) # 创建字节流对象
p = sampleNTT(io.BytesIO(hashlib.shake_128(b'').digest(1344)))  #256长度的对象。买个元素为12bit长。

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

seed = b"example_seed"  # 种子数据
j = 1
i = 2
hash_object = XOF(seed, j, i)#任意输出长度的哈希对象

print(hash_object.read(12))  

seed = b'\x00' * 32 
hash_object = PRF(seed, j,)#任意输出长度的哈希对象

print(hash_object.read(12))  

hash_object = J(seed)#任意输出长度的哈希对象

print(hash_object.read(12))  
# 输入种子
seed = b"example_seed"

# 调用函数
part1, part2 = G(seed)

# 输出结果
print("Part 1 (32 bytes):", part1.hex())
print("Part 2 (32 bytes):", part2.hex())

msg = b"example_message"

# 调用函数
hash_value = H(msg)

# 输出结果
print("SHA3-256 Hash (32 bytes):", hash_value.hex())

poly1 = Poly([1, 2, 3] + [0]*253)
poly2 = Poly([3, 2, 1] + [0]*253)
assert poly1 + poly2 == Poly([4, 4, 4] + [0]*253)

result = poly1 - poly2
expected = Poly([3327, 0, 2] + [0]*253)
assert result == expected
#######  Poly类的测试  ######

# 创建一个默认的 Poly 对象
poly1 = Poly()
# 打印结果
#print(poly1)  
# 创建一个自定义的 Poly 对象
poly2 = Poly([3, 2, 1] + [0]*253)
#print(poly2)  
poly1 = Poly([1, 2, 3] + [0]*253)
poly3 = poly1 + poly2 
#print(poly3)  
poly4 = poly1 - poly2 
#print(poly4)  
poly5 = - poly4 
#print(poly5)  
##### 数论变换 #####
array3 = np.random.randint(0, 3329, size=256)
Poly1 = Poly(array3)
result = Poly1.NTT()



    
Poly1=Poly([1,384,0]+[0]*253) #384x^1+1
Poly2=Poly([1,2,0]+[0]*253) #2x^1+1
Poly3=Poly([1,386,768]+[0]*253) #768x^2+386x^1+1

 
Poly4=Poly2.NTT()
Poly5=Poly2.RefNTT()

Poly1=Poly(np.random.randint(0, 3329, size=256)) #2x^1+1
Poly2=Poly(np.random.randint(0, 3329, size=256)) #2x^1+1
Poly1NTT = Poly1.NTT()
Poly2NTT = Poly2.NTT()

ployvec = Vec([Poly1,Poly2])
ployvecNTT = ployvec.NTT()
ploymat = Matrix([[Poly1,Poly2],[Poly1,Poly2]])
print(ploymat)