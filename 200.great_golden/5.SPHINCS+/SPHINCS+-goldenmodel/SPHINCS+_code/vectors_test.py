"""Stage-6: 官方 KAT 向量对齐测试（SHA256 L1/L3/L5）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import pytest

from SPHINCS_plus import Verify
from sphincs_params import get_params


@dataclass
class KatVector:
    count: int
    seed: bytes
    message: bytes
    public_key: bytes
    secret_key: bytes
    signature: bytes
    signature_len: int


def _hex_to_bytes(value: str) -> bytes:
    value = value.strip()
    return bytes.fromhex(value) if value else b""


def _parse_rsp(path: Path, limit: int | None = None) -> List[KatVector]:
    vectors: List[KatVector] = []
    current: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key == "count":
                if current:
                    vectors.append(
                        KatVector(
                            count=int(current["count"]),
                            seed=_hex_to_bytes(current["seed"]),
                            message=_hex_to_bytes(current["msg"]),
                            public_key=_hex_to_bytes(current["pk"]),
                            secret_key=_hex_to_bytes(current["sk"]),
                            signature=_hex_to_bytes(current["sm"]),
                            signature_len=int(current["smlen"]),
                        )
                    )
                    current.clear()
                    if limit is not None and len(vectors) >= limit:
                        break
                current["count"] = value
            else:
                current[key] = value
        else:
            if current and (limit is None or len(vectors) < limit):
                vectors.append(
                    KatVector(
                        count=int(current["count"]),
                        seed=_hex_to_bytes(current["seed"]),
                        message=_hex_to_bytes(current["msg"]),
                        public_key=_hex_to_bytes(current["pk"]),
                        secret_key=_hex_to_bytes(current["sk"]),
                        signature=_hex_to_bytes(current["sm"]),
                        signature_len=int(current["smlen"]),
                    )
                )
    return vectors


def _kat_cases() -> Sequence[Tuple[str, int, Path]]:
    base = Path(__file__).resolve().parent
    kat_root = (
        base.parent.parent
        / "1.sphincs+-submission-nist"
        / "NIST-PQ-Submission-SPHINCS-20171130"
        / "KAT"
    )
    candidates: Iterable[Tuple[str, int, str]] = (
        ("sha256-128s", 1, "sphincs-sha256-128s"),
        ("sha256-192s", 3, "sphincs-sha256-192s"),
        ("sha256-256s", 5, "sphincs-sha256-256s"),
    )
    cases: List[Tuple[str, int, Path]] = []
    for name, level, folder in candidates:
        path = kat_root / folder / "PQCsignKAT_64.rsp"
        if path.exists():
            cases.append((name, level, path))
    if not cases:
        pytest.skip("官方 SHA256-s 向量文件未找到，跳过 KAT 对齐测试", allow_module_level=True)
    return cases


def _expected_sig_len(params: Dict[str, int | str]) -> int:
    n = int(params["n"])
    fors_height = int(params["fors_height"])
    fors_trees = int(params["fors_trees"])
    d = int(params["d"])
    tree_height = int(params["tree_height"])
    wots_len = int(params["len"]) * n
    auth_len = tree_height * n
    fors_len = fors_trees * (fors_height + 1) * n
    return n + fors_len + d * (wots_len + auth_len)


@pytest.mark.parametrize(
    "param_name, level, vector",
    [
        (name, level, vector)
        for name, level, path in _kat_cases()
        for vector in _parse_rsp(path, limit=1)
    ],
)
def test_official_vectors_verify(param_name: str, level: int, vector: KatVector) -> None:
    params = get_params(level=level)
    assert params["name"] == param_name
    sig_len = _expected_sig_len(params)
    assert sig_len + len(vector.message) == vector.signature_len

    signature = vector.signature[:sig_len]
    message_from_sig = vector.signature[sig_len:]
    assert message_from_sig == vector.message

    n = int(params["n"])
    pk_seed = vector.public_key[:n]
    pk_root = vector.public_key[n:]
    public_key = {"seed": pk_seed, "root": pk_root}

    # 校验 secret key 中的根是否与公钥一致
    sk_seed = vector.secret_key[:n]
    sk_prf = vector.secret_key[n : 2 * n]
    sk_pub_seed = vector.secret_key[2 * n : 3 * n]
    sk_root = vector.secret_key[3 * n :]
    assert sk_pub_seed == pk_seed
    assert sk_root == pk_root

    # 验证签名
    assert Verify(public_key, vector.message, signature, params)
