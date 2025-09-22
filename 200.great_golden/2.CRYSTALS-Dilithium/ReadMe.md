[TOC]

'''
@Descripttion: CRYSTALS-Dilithium实现
@version: V1.0
@Author: HZW
@Date: 2025-03-14 16:53:00
'''

# 1.目录
```
CRYSTALS-Dilithium
├─ doc
│  ├─ assets
│  ├─ Dilithium.md
│  ├─ Dilithium.pdf
│  └─ NIST.FIPS.204.pdf
├─ ML_DSA_code
│  ├─ auxiliary_function.py
│  ├─ auxiliary_function_test.py
│  ├─ Benchmark_ML_DSA.py
│  ├─ ML_DSA.py
│  ├─ ML_DSA_internal.py
│  ├─ ML_DSA_internal_test.py
│  ├─ ML_DSA_test.py
│  └─ readme.md
└─ ReadMe.md
```
# 2.文件说明
* ML_DSA_code：代码
  * readme.md：代码文件说明
* doc
  * Dilithium.md:FIPS 204标准梳理
  * NIST.FIPS.204.pdf:FIPS 204标准
# 3.环境支持
* pip3 install pycryptodome pytest
# 4.性能测试
一个粗略的性能测试，使用AMD Ryzen5 4600H CPU，在Windows 10操作系统上运行。运行[`Benchmark_ML_DSA.py`](ML_DSA_code\Benchmark_ML_DSA.py)

|  1000 Iterations         | `ML_DSA_44`  | `ML_DSA_65`  | `ML_DSA_87`  |
|--------------------------|--------------|--------------|--------------|
| `KeyGen()` Average Time  |  43 ms        | 66 ms        | 95 ms        |
| `Sign()`   Average Time  |  254 ms       | 380 ms       | 426 ms       |
| `Verify()` Average Time  |  45 ms        | 64 ms        | 95 ms        |


