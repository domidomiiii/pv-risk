"""Firth Logit 风险评分：严格实现论文第 7 章评分卡计算过程。

计算步骤（表 7-2 参数）：
    第一步 缩尾      —— core.preprocessing
    第二步 标准化    —— z = (x - mean) / std
    第三步 logit     —— logit = -1.941 + Σ(βᵢ × zᵢ)，其中 lev 贡献经符号约束截断
    第四步 分值      —— score = 100 / (1 + exp(-logit))
    第五步 风险等级  —— 按重定阈值 A—D

符号约束（应用层修复）：
    β_lev = -0.495 是"控制其余 7 项不变"的条件效应，不是提高负债率的因果效应。
    为避免工具输出"负债越高越安全"，lev 贡献取 max(0, β_lev × z_lev)，
    原始贡献保留于 raw_contributions 供明细展示；风险来源排序只用截断后贡献。

风险等级阈值（训练集 2014—2022，n=551，分值 50/75/90 分位重定）：
    A: score < 14.23        低风险
    B: 14.23 ≤ score ≤ 23.17 中低风险
    C: 23.17 < score ≤ 37.27 中高风险
    D: score > 37.27        高风险

论文声明：分值是 0—100 的相对风险评分，未经概率校准，
不能直接解释为企业下一年度亏损的绝对概率。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.config_loader import (
    get_indicator_order,
    get_intercept,
    get_scorecard_params,
    load_risk_levels,
)
from core.preprocessing import PreprocessResult, preprocess_all

# 符号约束变量：负贡献截断为 0（条件效应系数，不作因果解释）
SIGN_CLAMPED_VARS = ("lev",)


@dataclass
class ScoringResult:
    """Firth Logit 评分完整结果。"""

    logit: float
    score: float
    level: str
    level_meaning: str
    contributions: Dict[str, float] = field(default_factory=dict)
    raw_contributions: Dict[str, float] = field(default_factory=dict)
    preprocess: Dict[str, PreprocessResult] = field(default_factory=dict)
    intercept: float = 0.0
    missing_variables: List[str] = field(default_factory=list)


def sigmoid_score(logit: float) -> float:
    """第四步：score = 100 / (1 + exp(-logit))。"""
    return 100.0 / (1.0 + math.exp(-logit))


def classify_level(score: float) -> tuple[str, str]:
    """第五步：按重定阈值（config/risk_levels.json）确定 A—D 等级。返回 (等级, 风险含义)。"""
    levels = load_risk_levels()["levels"]
    for lv in levels:
        lo = lv["score_min"]
        hi = lv["score_max"]
        if lo is None and hi is not None and score < hi:
            return lv["level"], lv["meaning"]
        if hi is None and lo is not None and score > lo:
            return lv["level"], lv["meaning"]
        if lo is not None and hi is not None and lo <= score <= hi:
            return lv["level"], lv["meaning"]
    # 兜底：论文阈值应完整覆盖 [0,100]，此处理论上不可达
    return levels[-1]["level"], levels[-1]["meaning"]


def compute_raw_contributions(preprocess: Dict[str, PreprocessResult]) -> Dict[str, float]:
    """原始单项贡献 = Firth 系数 × 标准化后的指标值 z（未截断，供明细展示）。"""
    params = get_scorecard_params()
    contributions: Dict[str, float] = {}
    for var, pr in preprocess.items():
        coef = float(params[var]["coef"])
        contributions[var] = 0.0 if pr.z is None else coef * pr.z
    return contributions


def apply_sign_constraint(raw: Dict[str, float]) -> Dict[str, float]:
    """符号约束：lev 负贡献置零，其余 7 项不变。logit 与风险来源排序均用截断后贡献。"""
    return {
        v: (max(0.0, c) if v in SIGN_CLAMPED_VARS else c)
        for v, c in raw.items()
    }


def compute_contributions(preprocess: Dict[str, PreprocessResult]) -> Dict[str, float]:
    """截断后单项贡献（lev 取 max(0, β×z)，其余同原始贡献）。"""
    return apply_sign_constraint(compute_raw_contributions(preprocess))


def score_indicators(indicator_values: Dict[str, Optional[float]]) -> ScoringResult:
    """对八项指标执行完整评分卡流程。

    参数 indicator_values: {指标名: 数值 或 None}。
    缺失指标记入 missing_variables，其贡献按 0 计（并在页面提示）。
    """
    order = get_indicator_order()
    intercept = get_intercept()

    preprocess = preprocess_all(indicator_values)
    raw_contributions = compute_raw_contributions(preprocess)
    contributions = apply_sign_constraint(raw_contributions)

    missing = [v for v in order if preprocess[v].z is None]
    logit = intercept + sum(contributions.get(v, 0.0) for v in order)
    score = sigmoid_score(logit)
    level, meaning = classify_level(score)

    return ScoringResult(
        logit=logit,
        score=score,
        level=level,
        level_meaning=meaning,
        contributions=contributions,
        raw_contributions=raw_contributions,
        preprocess=preprocess,
        intercept=intercept,
        missing_variables=missing,
    )
