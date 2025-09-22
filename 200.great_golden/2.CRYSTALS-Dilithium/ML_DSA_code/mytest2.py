import pytest
import numpy as np
import random
import os
from auxiliary_function import *


for i in range(256):
    t=InterToBits(i,8)
    c=BitsToInter(t,8)
    print("截断")
    print(i)
    print(t)

x = 123456789  # 输入的非负整数
a = 8  # 输出的byte数组长度

# 调用函数
result = InterToBytes(x, a)
print("转换后的字节数组（小端字节序）:", result)