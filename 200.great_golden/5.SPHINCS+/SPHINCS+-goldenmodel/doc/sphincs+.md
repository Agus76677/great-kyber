# SPHINCS+ 黄金模型（Stage 5：KAT 对齐）

本目录结构与 `CRYSTALS-Kyber`、`CRYSTALS-Dilithium` 黄金模型保持一致，包含：

- `SPHINCS+_code/`
  - Python 代码骨架及 pytest 测试文件。
- `doc/assets/`
  - 后续阶段用于存放图示与说明的静态资源。
- `ReadMe.md`
  - 提供依赖、运行方式与阶段说明。

## Stage 5 进展摘要

1. 对齐 NIST SHA256-128s KAT：重写 `F/H/PRF/H_msg` 以匹配参考实现的 mgf1 / HMAC 域分离；
2. 调整 FORS/Merkle 逻辑，支持 `thash_multi` 聚合并准确复现地址偏移；
3. 新增 `vectors_test.py`，自动解析官方 `.rsp` 向量并验证 KeyGen 与 Verify 的一致性；
4. README 与文档同步升级至 Stage 5，记录 KAT 测试命令与哈希域分离细节。

## Stage 3 回顾

1. 实现 FORS 多树签名、认证路径恢复与公钥聚合逻辑，全面复用 Stage 1 哈希工具；
2. 新增 `fors_test.py`，验证固定向量的签名成功、消息篡改失败以及索引派生稳定性；
3. 扩展 `sphincs_utils`，补齐 FORS 地址、索引派生与类型重写工具，并同步更新测试；
4. 演示脚本串联 FORS、WOTS+ 与单层 Merkle，展示 Stage 3 半闭环数据流与长度信息。

## Stage 2 回顾

1. 实现 WOTS+ 链函数、密钥生成、签名与公钥恢复接口，全部遵循 bytes 输入输出；
2. 衔接 Stage 1 的 SHA256 基元与地址工具，完成固定种子下的签名-验签闭环；
3. 新增 `wots_test.py`，以确定性向量覆盖正常路径与异常消息的验证分支；
4. 更新演示脚本，可直接运行观察 WOTS+ 长度信息与验签结果。

## Stage 1 回顾

1. 基于 `hashlib.sha256` 实现 `F/H/PRF/PRF_msg/H_msg`，并以固定向量验证；
2. 完成字节编解码、地址（ADR）工具集，支持与 Kyber/Dilithium 同风格的测试；
3. 提供树索引解析、认证路径推导等实用函数，为后续 WOTS+/FORS 奠定基础；
4. 更新 `ReadMe.md` 与单元测试，确保 `pytest` 即时覆盖全部新特性。

## Stage 0 回顾

1. 构建目录与文件骨架，保持与 Kyber/Dilithium 项目风格一致。
2. 提供统一的文件头注释与函数文档模板，方便后续阶段扩展。
3. 完成最小化的 pytest 烟雾测试：
   - 模块可被导入；
   - 参数查询接口返回 SHA256 Level-1 配置；
   - 占位哈希接口可探测（当前抛出 `NotImplementedError`）。

## 下一阶段计划

- Stage 6 拓展至 SHA256 Level-3/Level-5 参数集；
- Stage 7 引入 SHAKE256 后端并复用统一接口。

> 参考资料：`../1.sphincs+-submission-nist` 目录中的 NIST 官方提交文档与代码实现。
