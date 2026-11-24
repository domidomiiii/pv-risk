"""配置文件加载器：集中读取 config/ 下的论文参数与实证结果 JSON。

所有模块通过本加载器获取论文参数，避免在各处硬编码数值，
确保系统计算严格遵循论文口径且不修改任何模型参数、阈值。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

# 项目根目录（PV-Risk/）
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"


@lru_cache(maxsize=None)
def _load(filename: str) -> Dict[str, Any]:
    """读取并缓存单个 JSON 配置文件。"""
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"配置文件缺失：{path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_indicators() -> Dict[str, Any]:
    """表 3-1 指标体系与原始报表字段定义。"""
    return _load("indicator_definitions.json")


def load_model_parameters() -> Dict[str, Any]:
    """表 5-1 Firth 系数、表 7-2 评分卡参数、表 4-1 LGB 超参、Altman Z''。"""
    return _load("model_parameters.json")


def load_risk_levels() -> Dict[str, Any]:
    """表 7-1 风险等级阈值与表 7-3 海源复材验证案例。"""
    return _load("risk_levels.json")


def load_research_results() -> Dict[str, Any]:
    """论文全部实证结果表格与图表数据（标注为论文实证结果）。"""
    return _load("research_results.json")


def load_research_overview() -> Dict[str, Any]:
    """首页概览：摘要、背景、贡献、结论、评分卡应用文字。"""
    return _load("research_overview.json")


def get_scorecard_params() -> Dict[str, Any]:
    """返回评分卡逐项参数（缩尾点、均值、标准差、系数）与截距。"""
    mp = load_model_parameters()
    return mp["scorecard_params"]["params"]


def get_intercept() -> float:
    """Firth Logit 截距（论文表 5-1 / 表 7-2，值为 -1.941）。"""
    return float(load_model_parameters()["firth_logit"]["intercept"])


def get_indicator_order() -> list[str]:
    """八项指标在模型中的固定顺序。"""
    return list(load_model_parameters()["firth_logit"]["coefficient_order"])
