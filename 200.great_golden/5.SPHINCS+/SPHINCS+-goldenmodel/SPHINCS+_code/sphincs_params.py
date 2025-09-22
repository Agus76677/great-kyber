"""
@Descripttion: SPHINCS+ 参数集合（Stage-6 多安全级别版）
@version: V0.6
@Author: GoldenModel-Team
@Date: 2025-04-05 12:00
"""

from __future__ import annotations

from typing import Dict

_SHA256_PARAMS: Dict[int, Dict[str, int | str]] = {
    1: {
        "name": "sha256-128s",
        "n": 16,
        "h": 64,
        "full_height": 64,
        "d": 8,
        "tree_height": 8,
        "w": 16,
        "len_1": 32,
        "len_2": 3,
        "len": 35,
        "k": 10,
        "a": 15,
        "fors_height": 15,
        "fors_trees": 10,
        "optrand_bytes": 32,
    },
    3: {
        "name": "sha256-192s",
        "n": 24,
        "h": 64,
        "full_height": 64,
        "d": 8,
        "tree_height": 8,
        "w": 16,
        "len_1": 48,
        "len_2": 3,
        "len": 51,
        "k": 14,
        "a": 16,
        "fors_height": 16,
        "fors_trees": 14,
        "optrand_bytes": 32,
    },
    5: {
        "name": "sha256-256s",
        "n": 32,
        "h": 64,
        "full_height": 64,
        "d": 8,
        "tree_height": 8,
        "w": 16,
        "len_1": 64,
        "len_2": 3,
        "len": 67,
        "k": 22,
        "a": 14,
        "fors_height": 14,
        "fors_trees": 22,
        "optrand_bytes": 32,
    },
}


def get_params(level: int = 1, variant: str = "sha256") -> Dict[str, int | str]:
    """
    根据安全等级与哈希后端获取参数集合。

    输入：
        level (int): 安全等级编号，当前支持 {1, 3, 5}。
        variant (str): 哈希后端标识，Stage-6 限定为 "sha256"。
    输出：
        Dict[str, int | str]: 对应参数字典的浅拷贝，用于后续模块初始化。
    """

    variant_lower = variant.lower()
    if variant_lower != "sha256":
        raise ValueError("Only sha256 variant is available in Stage 6")
    try:
        params = _SHA256_PARAMS[level]
    except KeyError as exc:  # pragma: no cover - 触发时代表调用方传入了暂不支持的级别
        raise ValueError("Unsupported security level for sha256 variant") from exc
    return dict(params)


__all__ = ["get_params"]
