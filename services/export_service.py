"""评估结果导出服务（Excel）。

支持导出单次评估的完整明细（指标原始值/缩尾值/z 值/贡献、logit、评分、
等级、风险来源），以及历史记录列表。使用 openpyxl 引擎。
"""
from __future__ import annotations

import io
from typing import Any, Dict, List

import pandas as pd

from core.risk_attribution import indicator_cn


def export_single_assessment(assessment: Dict[str, Any]) -> bytes:
    """将单次评估结果导出为多 Sheet Excel 字节流。"""
    buffer = io.BytesIO()

    # Sheet1：评估概览
    overview = pd.DataFrame([
        {"项目": "企业名称", "值": assessment.get("company_name", "")},
        {"项目": "股票代码", "值": assessment.get("stock_code", "")},
        {"项目": "评估年度", "值": assessment.get("fiscal_year", "")},
        {"项目": "logit", "值": _round(assessment.get("logit"), 4)},
        {"项目": "风险评分(0-100)", "值": _round(assessment.get("score"), 2)},
        {"项目": "风险等级", "值": assessment.get("risk_level", "")},
        {"项目": "风险含义", "值": assessment.get("level_meaning", "")},
        {"项目": "主要风险来源", "值": "、".join(
            f"{s['name_cn']}({s['contribution']:+.3f})"
            for s in assessment.get("top_risk_sources", [])
        )},
        {"项目": "评分说明", "值": "0—100 相对风险评分，未经概率校准，非绝对亏损概率。"},
    ])

    # Sheet2：指标明细
    detail_rows = assessment.get("detail_rows", [])
    detail = pd.DataFrame([
        {
            "指标": r["variable"],
            "中文名": r["name_cn"],
            "原始值": _round(r["raw"], 6),
            "缩尾值": _round(r["winsorized"], 6),
            "标准化z": _round(r["z"], 4),
            "对logit贡献": _round(r["contribution"], 4),
            "缩尾提示": r["clip_note"],
        }
        for r in detail_rows
    ])

    # Sheet3：校验提示
    issues = assessment.get("issues", [])
    issues_df = pd.DataFrame([
        {"级别": i["level"], "字段": i["field"], "说明": i["message"]} for i in issues
    ]) if issues else pd.DataFrame([{"级别": "", "字段": "", "说明": "无校验问题"}])

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="评估概览", index=False)
        detail.to_excel(writer, sheet_name="指标明细", index=False)
        issues_df.to_excel(writer, sheet_name="校验提示", index=False)

    return buffer.getvalue()


def export_history(records: List[Dict[str, Any]]) -> bytes:
    """将历史记录列表导出为单 Sheet Excel 字节流。"""
    buffer = io.BytesIO()
    rows = []
    for r in records:
        top = r.get("top_risk_sources") or []
        rows.append({
            "记录ID": r.get("id"),
            "企业名称": r.get("company_name"),
            "股票代码": r.get("stock_code"),
            "评估年度": r.get("fiscal_year"),
            "创建时间": r.get("created_at"),
            "logit": _round(r.get("logit"), 4),
            "风险评分": _round(r.get("score"), 2),
            "风险等级": r.get("risk_level"),
            "风险含义": r.get("level_meaning"),
            "主要风险来源": "、".join(
                f"{indicator_cn(s['variable'])}({s['contribution']:+.3f})" for s in top
            ) if top else "",
        })
    df = pd.DataFrame(rows) if rows else pd.DataFrame([{"提示": "暂无历史记录"}])
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="评估历史", index=False)
    return buffer.getvalue()


def _round(v: Any, n: int) -> Any:
    if v is None:
        return None
    try:
        return round(float(v), n)
    except (TypeError, ValueError):
        return v
