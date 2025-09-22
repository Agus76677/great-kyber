# SPHINCS+ Golden Model（Stage 6）

> 目录与注释风格参考 `200.great_golden/1.CRYSTALS-kyber` 与 `200.great_golden/2.CRYSTALS-Dilithium`，保持统一的黄金模型结构。

## 目录结构

```
SPHINCS+-goldenmodel
├─ SPHINCS+_code
│  ├─ *.py / *_test.py
├─ doc
│  ├─ sphincs+.md
│  └─ assets/
└─ ReadMe.md
```

## 依赖说明

- Python ≥ 3.10
- `pytest`

使用 `pip install -r requirements.txt`（若后续提供）或手动安装 `pytest`。

## 运行 pytest

```bash
cd 200.great_golden/5.SPHINCS+/SPHINCS+-goldenmodel/SPHINCS+_code
pytest auxiliary_function_test.py -q
pytest sphincs_hash_test.py -q
pytest sphincs_utils_test.py -q
pytest sphincs_merkle_test.py -q
pytest wots_test.py -q
pytest fors_test.py -q
pytest SPHINCS_plus_test.py -q
pytest vectors_test.py -q
```

上述命令与 Kyber/Dilithium 黄金模型中的测试风格保持一致：单文件测试、`-q` 静默模式。
Stage 6 在 `SPHINCS_plus_test.py` 中对 SHA256 Level-1/3/5 三套参数执行确定性 KeyGen/Sign/Verify、
空消息与 100KB 长消息回归；
`vectors_test.py` 则对齐 SHA256-{128s,192s,256s} 官方 KAT 向量并验证签名长度、密钥字段与验签结果，
同时保留 Stage 2/3 的 WOTS+、FORS 基元测试，构成完整的端到端回归集合。

## 参数集切换

- 当前阶段实现 `SHA256` Level-1/Level-3/Level-5（`sha256-128s`、`sha256-192s`、`sha256-256s`）；
- 使用 `sphincs_params.get_params(level=<1|3|5>, variant="sha256")` 获取配置；
- 哈希后端仍限定 `sha256`，`shake256`/`haraka` 将在后续阶段逐步补充，接口保持兼容。

## 阶段路线图

| 阶段 | 目标 |
| ---- | ---- |
| Stage 0 | 完成骨架、注释模板、参数探针与基础 pytest |
| Stage 1 | 实现 SHA256-L1 哈希与辅助函数最小闭环 |
| Stage 2 | WOTS+ 基元落地并完成签名验证演示 |
| Stage 3 | FORS 与 WOTS+ 打通，构建半闭环 |
| Stage 4 | Merkle/Hypertree 及端到端 KeyGen/Sign/Verify |
| Stage 5 | 对齐官方向量（SHA256-L1）并补全哈希域分离 |
| Stage 6 | 扩展到 SHA256 Level-3 / Level-5，完成多参数回归 |
| Stage 7+ | 扩展更高安全级别与哈希后端 |

## 演示脚本

```bash
python sphincs_demonstration.py
```

Stage 6 脚本遍历 Level-1/3/5 参数集执行确定性密钥生成、签名、验签并打印签名结构，可快速观察各安全级别的差异。

## 参考资料

- `../1.sphincs+-submission-nist/`
- NIST PQC 官方 SPHINCS+ 规范
