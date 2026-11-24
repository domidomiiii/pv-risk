"""八项财务指标计算，严格遵循论文表 3-1 口径。

指标口径（不得替换）：
    lev        = 负债合计 / 资产总计
    cr         = 流动资产合计 / 流动负债合计
    roa        = 归母净利润 / 期末资产总计（论文自定义 ROA 代理指标）
    ocf        = 经营活动现金流量净额 / 营业收入
    cip_fa     = 在建工程净额 / 固定资产净额
    reta       = 未分配利润 / 期末资产总计
    asset_turn = 营业收入 / 期末资产总计
    growth     = 本期营业收入 / 上期营业收入 - 1
"""
from __future__ import annotations

from typing import Dict, Optional

# 指标计算所需的最小原始字段集合
INDICATOR_FORMULAS = {
    "lev": ("total_liabilities", "total_assets"),
    "cr": ("current_assets", "current_liabilities"),
    "roa": ("net_profit_attr", "total_assets"),
    "ocf": ("net_operating_cashflow", "revenue"),
    "cip_fa": ("construction_in_progress", "fixed_assets_net"),
    "reta": ("retained_earnings", "total_assets"),
    "asset_turn": ("revenue", "total_assets"),
}

# growth 为特殊形式：revenue / revenue_prev - 1
GROWTH_NUMERATOR = "revenue"
GROWTH_DENOMINATOR = "revenue_prev"

# 指标固定顺序（与模型系数顺序一致）
INDICATOR_ORDER = [
    "lev", "cr", "roa", "ocf", "cip_fa", "reta", "asset_turn", "growth",
]


def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """安全除法：分子或分母缺失、或分母为零时返回 None。"""
    if numerator is None or denominator is None:
        return None
    if abs(denominator) < 1e-12:
        return None
    return numerator / denominator


def compute_indicators(cleaned: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """根据清洗后的原始报表数值计算八项指标。

    参数 cleaned 的键为 core.validation.RAW_FIELD_NAMES。
    返回 {指标名: 数值 或 None}，None 表示因缺失/分母为零无法计算。
    """
    values: Dict[str, Optional[float]] = {}

    for name, (num_field, den_field) in INDICATOR_FORMULAS.items():
        values[name] = _safe_divide(cleaned.get(num_field), cleaned.get(den_field))

    # growth = revenue / revenue_prev - 1
    ratio = _safe_divide(cleaned.get(GROWTH_NUMERATOR), cleaned.get(GROWTH_DENOMINATOR))
    values["growth"] = None if ratio is None else ratio - 1.0

    return values


def compute_from_raw(raw_indicators: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """当已直接提供八项指标值（如论文表 7-3 案例）时，规整为标准顺序字典。

    仅做类型清洗，不重新按报表字段计算。用于内置验证案例复算。
    """
    out: Dict[str, Optional[float]] = {}
    for name in INDICATOR_ORDER:
        v = raw_indicators.get(name)
        out[name] = None if v is None else float(v)
    return out
