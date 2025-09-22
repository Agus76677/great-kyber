"""
@Descripttion: SPHINCS+ 参数集合（Stage-0 占位版）
@version: V0.1
@Author: GoldenModel-Team
@Date: 2025-03-15 12:00
"""

from __future__ import annotations

from typing import Dict

_SHA256_LEVEL1_PARAMS: Dict[str, int | str] = {
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
}


def get_params(level: int = 1, variant: str = "sha256") -> Dict[str, int | str]:
    """
    根据安全等级与哈希后端获取参数集合。

    输入：
        level (int): 安全等级编号，目前仅支持 1。
        variant (str): 哈希后端标识，阶段 0 限定为 "sha256"。
    输出：
        Dict[str, int | str]: 对应参数字典的浅拷贝，用于后续模块初始化。
    """
    if level != 1:
        raise ValueError("Only level 1 parameters are available in Stage 0")
    if variant.lower() != "sha256":
        raise ValueError("Only sha256 variant is available in Stage 0")
    return dict(_SHA256_LEVEL1_PARAMS)


__all__ = ["get_params"]
