"""预处理：1%/99% 缩尾与 Z-score 标准化。

严格遵循论文表 7-2 参数与计算顺序：
    第一步 缩尾：按训练集 P1/P99 分位点截断，超出部分取边界值。
    第二步 标准化：z = (x - 缩尾后均值) / 缩尾后标准差。

论文强调：均值和标准差为缩尾后的数值，即先按 P1/P99 截断再计算，顺序不可颠倒。
所有分位点、均值、标准差均取自训练集（2014—2022，n=551），不使用测试期数据。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from core.config_loader import get_scorecard_params


@dataclass
class PreprocessResult:
    """单项指标的缩尾与标准化结果。"""

    variable: str
    raw: Optional[float]
    winsorized: Optional[float]
    z: Optional[float]
    clipped_low: bool = False
    clipped_high: bool = False


def winsorize(value: float, p1: float, p99: float) -> tuple[float, bool, bool]:
    """按 P1/P99 缩尾。返回 (缩尾值, 是否触及下界, 是否触及上界)。"""
    clipped_low = value < p1
    clipped_high = value > p99
    w = min(max(value, p1), p99)
    return w, clipped_low, clipped_high


def standardize(winsorized: float, mean: float, std: float) -> float:
    """Z-score 标准化：z = (x - mean) / std。"""
    if abs(std) < 1e-12:
        # 论文参数中 std 均为正；此处防御性处理，避免除零
        return 0.0
    return (winsorized - mean) / std


def preprocess_indicator(variable: str, value: Optional[float]) -> PreprocessResult:
    """对单项指标执行缩尾 + 标准化。"""
    params = get_scorecard_params()[variable]
    if value is None:
        return PreprocessResult(variable=variable, raw=None, winsorized=None, z=None)

    p1 = float(params["winsor_p1"])
    p99 = float(params["winsor_p99"])
    mean = float(params["mean"])
    std = float(params["std"])

    w, low, high = winsorize(float(value), p1, p99)
    z = standardize(w, mean, std)
    return PreprocessResult(
        variable=variable,
        raw=float(value),
        winsorized=w,
        z=z,
        clipped_low=low,
        clipped_high=high,
    )


def preprocess_all(indicator_values: Dict[str, Optional[float]]) -> Dict[str, PreprocessResult]:
    """对八项指标批量执行缩尾 + 标准化，返回按变量名索引的结果字典。"""
    return {var: preprocess_indicator(var, indicator_values.get(var)) for var in indicator_values}
