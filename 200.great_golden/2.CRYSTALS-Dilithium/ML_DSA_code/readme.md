[TOC]
## 1.目录
```
ML_DSA_code
    ├─ auxiliary_function.py
    ├─ auxiliary_function_test.py
    ├─ Benchmark_ML_DSA.py
    ├─ ML_DSA.py
    ├─ ML_DSA_internal.py
    ├─ ML_DSA_internal_test.py
    ├─ ML_DSA_test.py
    └─ readme.md
```
## 2.文件说明
* 环境支持：
  * pip3 install pycryptodome pytest
* auxiliary_function.py：辅助函数
* auxiliary_function_test.py：辅助函数自动化测试文件
  * 运行方式：pytest CRYSTALS-Dilithium\ML_DSA_code\auxiliary_function_test.py
* ML_DSA_internal.py:对应于ML_DSA_internal组件方案
* ML_DSA_internal_test.py：ML_DSA_internal组件方案自动化测试文件
  * 运行方式：pytest CRYSTALS-Dilithium\ML_DSA_code\ML_DSA_internal_test.py
* ML_DSA.py:对应于ML_DSA外部组件方案
* ML_DSA_test.py：ML_DSA.py自动化测试文件
  * 运行方式：pytest CRYSTALS-Dilithium\ML_DSA_code\ML_DSA_test.py