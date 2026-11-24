"""Firth Logit 风险评分：严格实现论文第 7 章评分卡计算过程。

计算步骤（表 7-2 参数）：
    第一步 缩尾      —— core.preprocessing
    第二步 标准化    —— z = (x - mean) / std
    第三步 logit     —— logit = -1.941 + Σ(βᵢ × zᵢ)
    第四步 分值      —— score = 100 / (1 + exp(-logit))
    第五步 风险等级  —— 按表 7-1 阈值 A—D

风险等级阈值（论文原始，不得修改）：
    A: score < 11.52        低风险
    B: 11.52 ≤ score ≤ 20.02 中低风险
    C: 20.02 < score ≤ 33.24 中高风险
    D: score > 33.24        高风险

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


@dataclass
class ScoringResult:
    """Firth Logit 评分完整结果。"""

    logit: float
    score: float
    level: str
    level_meaning: str
    contributions: Dict[str, float] = field(default_factory=dict)
    preprocess: Dict[str, PreprocessResult] = field(default_factory=dict)
    intercept: float = 0.0
    missing_variables: List[str] = field(default_factory=list)


def sigmoid_score(logit: float) -> float:
    """第四步：score = 100 / (1 + exp(-logit))。"""
    return 100.0 / (1.0 + math.exp(-logit))


def classify_level(score: float) -> tuple[str, str]:
    """第五步：按论文表 7-1 阈值确定 A—D 等级。返回 (等级, 风险含义)。"""
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


def compute_contributions(preprocess: Dict[str, PreprocessResult]) -> Dict[str, float]:
    """单项贡献 = Firth 系数 × 标准化后的指标值 z。"""
    params = get_scorecard_params()
    contributions: Dict[str, float] = {}
    for var, pr in preprocess.items():
        coef = float(params[var]["coef"])
        contributions[var] = 0.0 if pr.z is None else coef * pr.z
    return contributions


def score_indicators(indicator_values: Dict[str, Optional[float]]) -> ScoringResult:
    """对八项指标执行完整评分卡流程。

    参数 indicator_values: {指标名: 数值 或 None}。
    缺失指标记入 missing_variables，其贡献按 0 计（并在页面提示）。
    """
    order = get_indicator_order()
    intercept = get_intercept()

    preprocess = preprocess_all(indicator_values)
    contributions = compute_contributions(preprocess)

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
        preprocess=preprocess,
        intercept=intercept,
        missing_variables=missing,
    )
