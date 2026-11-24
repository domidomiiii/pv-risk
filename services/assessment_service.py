"""评估服务：编排"原始输入 -> 校验 -> 指标计算 -> 缩尾标准化 -> Firth 评分
-> 风险等级 -> 贡献分解 -> 结果封装"的完整流程。

本服务是页面与核心算法之间的桥梁，输出统一的 dict 结果，供展示与入库使用。
所有计算真实运行，不使用写死结果。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core import indicator_calculator as ic
from core import validation as val
from core.firth_scoring import score_indicators
from core.risk_attribution import full_attribution, indicator_cn, rank_risk_sources


def assess_from_raw_inputs(
    company_name: str,
    stock_code: Optional[str],
    fiscal_year: Optional[int],
    raw_inputs: Dict[str, Any],
) -> Dict[str, Any]:
    """由原始报表字段完成一次完整评估。

    返回结构包含：
        ok / issues / indicators / winsorized / z_scores / contributions /
        logit / score / risk_level / level_meaning / top_risk_sources / detail_rows
    当存在 error 级校验问题时，ok=False 且不产出评分。
    """
    # 1. 校验原始输入
    cleaned, v_missing = val.validate_raw_inputs(raw_inputs)
    v_denom = val.check_denominators(cleaned)
    validation = val.merge_results(v_missing, v_denom)

    if not validation.ok:
        return {
            "ok": False,
            "company_name": company_name,
            "stock_code": stock_code,
            "fiscal_year": fiscal_year,
            "issues": _issues_to_dicts(validation.issues),
            "stage": "validation",
        }

    # 2. 计算八项指标
    indicators = ic.compute_indicators(cleaned)

    # 3. 指标异常提示（warning，不阻断）
    v_anom = val.check_indicator_anomalies(indicators)
    validation = val.merge_results(validation, v_anom)

    # 4. Firth 评分（含缩尾、标准化、logit、Sigmoid、定级）
    result = score_indicators(indicators)

    # 5. 贡献分解
    top_sources = rank_risk_sources(result.contributions, top_n=3)
    attribution = full_attribution(result.contributions)

    # 6. 封装明细行（原始值 / 缩尾值 / z / 贡献）
    detail_rows = _build_detail_rows(result, attribution)

    return {
        "ok": True,
        "company_name": company_name,
        "stock_code": stock_code,
        "fiscal_year": fiscal_year,
        "issues": _issues_to_dicts(validation.issues),
        "raw_inputs": cleaned,
        "indicators": indicators,
        "winsorized": {v: result.preprocess[v].winsorized for v in indicators},
        "z_scores": {v: result.preprocess[v].z for v in indicators},
        "contributions": result.contributions,
        "logit": result.logit,
        "intercept": result.intercept,
        "score": result.score,
        "risk_level": result.level,
        "level_meaning": result.level_meaning,
        "missing_variables": result.missing_variables,
        "top_risk_sources": [
            {"variable": t.variable, "name_cn": t.name_cn, "contribution": t.contribution}
            for t in top_sources
        ],
        "detail_rows": detail_rows,
        "stage": "scored",
    }


def assess_from_indicators(
    company_name: str,
    stock_code: Optional[str],
    fiscal_year: Optional[int],
    indicator_values: Dict[str, float],
) -> Dict[str, Any]:
    """当直接提供八项指标值（如内置验证案例）时完成评估。

    不经过原始报表字段计算，直接进入缩尾->评分流程。
    """
    result = score_indicators(indicator_values)
    top_sources = rank_risk_sources(result.contributions, top_n=3)
    attribution = full_attribution(result.contributions)
    return {
        "ok": True,
        "company_name": company_name,
        "stock_code": stock_code,
        "fiscal_year": fiscal_year,
        "issues": [],
        "indicators": dict(indicator_values),
        "winsorized": {v: result.preprocess[v].winsorized for v in indicator_values},
        "z_scores": {v: result.preprocess[v].z for v in indicator_values},
        "contributions": result.contributions,
        "logit": result.logit,
        "intercept": result.intercept,
        "score": result.score,
        "risk_level": result.level,
        "level_meaning": result.level_meaning,
        "missing_variables": result.missing_variables,
        "top_risk_sources": [
            {"variable": t.variable, "name_cn": t.name_cn, "contribution": t.contribution}
            for t in top_sources
        ],
        "detail_rows": _build_detail_rows(result, attribution),
        "stage": "scored",
    }


def _build_detail_rows(result, attribution) -> List[Dict[str, Any]]:
    """构建指标明细表行，按贡献降序排列。"""
    rows: List[Dict[str, Any]] = []
    for item in attribution:
        v = item.variable
        pr = result.preprocess[v]
        clip_note = ""
        if pr.clipped_low:
            clip_note = "触及 P1 下界"
        elif pr.clipped_high:
            clip_note = "触及 P99 上界"
        rows.append({
            "variable": v,
            "name_cn": indicator_cn(v),
            "raw": pr.raw,
            "winsorized": pr.winsorized,
            "z": pr.z,
            "contribution": item.contribution,
            "clip_note": clip_note,
        })
    return rows


def _issues_to_dicts(issues) -> List[Dict[str, str]]:
    return [{"level": i.level, "field": i.field, "message": i.message} for i in issues]


def result_to_db_record(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """将评估结果转换为 repository.save_assessment 所需的记录结构。"""
    return {
        "company_name": assessment.get("company_name"),
        "stock_code": assessment.get("stock_code"),
        "fiscal_year": assessment.get("fiscal_year"),
        "raw_inputs": assessment.get("raw_inputs"),
        "indicators": assessment.get("indicators"),
        "winsorized": assessment.get("winsorized"),
        "z_scores": assessment.get("z_scores"),
        "contributions": assessment.get("contributions"),
        "logit": assessment.get("logit"),
        "score": assessment.get("score"),
        "risk_level": assessment.get("risk_level"),
        "level_meaning": assessment.get("level_meaning"),
        "top_risk_sources": assessment.get("top_risk_sources"),
        "validation_notes": assessment.get("issues"),
    }
