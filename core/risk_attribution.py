"""风险来源分解：按论文要求取正向贡献最大的三项作为主要风险来源。

论文口径：
    单项贡献 = Firth 系数 × 标准化后的指标值 z。
    取正向贡献最大的三项作为主要风险来源。

重要说明（论文原文）：此处的"贡献"指指标对模型输出的影响，
因果识别需另行设计；资产负债率等出现负贡献时，不应据此认为高杠杆对企业有利
（与论文 5.1 节的抑制效应一致）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from core.config_loader import load_indicators

# 变量 -> 中文名映射（来自表 3-1）
_INDICATOR_CN: Dict[str, str] = {
    ind["variable"]: ind["name_cn"] for ind in load_indicators()["indicators"]
}


@dataclass
class RiskSource:
    """单条风险来源。"""

    variable: str
    name_cn: str
    contribution: float


def rank_risk_sources(contributions: Dict[str, float], top_n: int = 3) -> List[RiskSource]:
    """按贡献降序排序，返回正向贡献最大的前 top_n 项。

    仅纳入贡献为正（> 0）的指标；若正向指标不足 top_n，则返回实际数量。
    """
    positive = [
        RiskSource(variable=v, name_cn=_INDICATOR_CN.get(v, v), contribution=c)
        for v, c in contributions.items()
        if c > 0
    ]
    positive.sort(key=lambda rs: rs.contribution, reverse=True)
    return positive[:top_n]


def full_attribution(contributions: Dict[str, float]) -> List[RiskSource]:
    """返回全部指标的贡献排序（降序），用于结果明细展示。"""
    items = [
        RiskSource(variable=v, name_cn=_INDICATOR_CN.get(v, v), contribution=c)
        for v, c in contributions.items()
    ]
    items.sort(key=lambda rs: rs.contribution, reverse=True)
    return items


def indicator_cn(variable: str) -> str:
    """获取指标中文名。"""
    return _INDICATOR_CN.get(variable, variable)
