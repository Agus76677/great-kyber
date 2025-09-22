[TOC]
## 1.目录
```
CRYSTALS-kyber_code
   ├─ auxiliary_function.py
   ├─ auxiliary_function_test.py
   ├─ kyber_demonstration.py
   ├─ kyber_k_KPE_test.py
   ├─ kyber_k_PKE.py
   ├─ ML_KEM.py
   ├─ ML_KEM_internal.py
   ├─ ML_KEM_internal_test.py
   ├─ ML_KEM_test.py
   └─ readme.md
```
## 2.文件说明
* 环境支持：
  * pip3 install pycryptodome pytest
* auxiliary_function.py：辅助函数
* auxiliary_function_test.py：辅助函数自动化测试文件
  * 运行方式：pytest CRYSTALS-kyber_code\auxiliary_function_test.py
  or
  pytest .\CRYSTALS-kyber\CRYSTALS-kyber_code\auxiliary_function_test.py

* kyber_k_PKE.py:对应于k_PKE组件方案
* kyber_k_KPE_test.py：k_PKE组件方案自动化测试文件
  * 运行方式：pytest CRYSTALS-kyber_code\kyber_k_KPE_test.py
  or 
  pytest .\CRYSTALS-kyber\CRYSTALS-kyber_code\kyber_k_KPE_test.py

* **kyber_demonstration.py：k_PKE组件方案使用示例**
* ML_KEM_internal.py：内部算法ML_KEM_internal
* ML_KEM_internal_test.py：内部算法ML_KEM_internal自动化测试文件
  * 运行方式：pytest CRYSTALS-kyber_code\ML_KEM_internal_test.py
  or
  pytest .\CRYSTALS-kyber\CRYSTALS-kyber_code\ML_KEM_internal_test.py

* ML_KEM.py:对应密钥封装机制
* ML_KEM_test.py：ML_KEM.py自动化测试文件
  * 运行方式：pytest CRYSTALS-kyber_code\ML_KEM_test.py
  or
  pytest .\CRYSTALS-kyber\CRYSTALS-kyber_code\ML_KEM_test.py



