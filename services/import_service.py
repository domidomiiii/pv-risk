"""Excel 财务数据导入服务。

模板列（中文表头）与原始报表字段一一对应，另含企业名称、股票代码、年度三列。
导入时进行完整性检查，返回可评估的记录列表与问题清单。

模板表头：
    企业名称, 股票代码, 年度,
    资产总计, 负债合计, 流动资产合计, 流动负债合计, 在建工程净额,
    固定资产净额, 未分配利润, 归母净利润, 营业收入, 上期营业收入,
    经营活动现金流量净额
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

# 中文表头 -> 内部字段名
COLUMN_MAP: Dict[str, str] = {
    "企业名称": "company_name",
    "股票代码": "stock_code",
    "年度": "fiscal_year",
    "资产总计": "total_assets",
    "负债合计": "total_liabilities",
    "流动资产合计": "current_assets",
    "流动负债合计": "current_liabilities",
    "在建工程净额": "construction_in_progress",
    "固定资产净额": "fixed_assets_net",
    "未分配利润": "retained_earnings",
    "归母净利润": "net_profit_attr",
    "营业收入": "revenue",
    "上期营业收入": "revenue_prev",
    "经营活动现金流量净额": "net_operating_cashflow",
}

TEMPLATE_HEADERS: List[str] = list(COLUMN_MAP.keys())

# 除 revenue_prev（growth 用，可缺）外，其余报表字段为必填
REQUIRED_COLUMNS = [c for c in TEMPLATE_HEADERS if c not in ("上期营业收入", "股票代码")]


def build_template_dataframe() -> pd.DataFrame:
    """生成一份带表头与一行示例（海源复材口径占位）的空模板 DataFrame。"""
    example = {h: "" for h in TEMPLATE_HEADERS}
    example["企业名称"] = "示例企业"
    example["股票代码"] = "000000"
    example["年度"] = 2024
    return pd.DataFrame([example], columns=TEMPLATE_HEADERS)


def parse_excel(file_like) -> Tuple[List[Dict[str, Any]], List[str]]:
    """解析上传的 Excel 文件。

    返回 (记录列表, 错误信息列表)。每条记录含 company_name / stock_code /
    fiscal_year 与 raw_inputs（字段名为内部英文键）。
    """
    errors: List[str] = []
    try:
        df = pd.read_excel(file_like)
    except Exception as exc:  # noqa: BLE001
        return [], [f"Excel 读取失败：{exc}"]

    # 表头校验
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"必需列缺失：{', '.join(missing_cols)}")
        return [], errors

    records: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        line_no = idx + 2  # Excel 行号（含表头）
        rec = _parse_row(row, line_no, errors)
        if rec is not None:
            records.append(rec)

    return records, errors


def _parse_row(row, line_no: int, errors: List[str]) -> Dict[str, Any] | None:
    """解析单行；企业名称缺失则跳过并记录错误。"""
    company_name = row.get("企业名称")
    if pd.isna(company_name) or str(company_name).strip() == "":
        errors.append(f"第 {line_no} 行：企业名称为空，已跳过。")
        return None

    raw_inputs: Dict[str, Any] = {}
    for cn_header, field in COLUMN_MAP.items():
        if field in ("company_name", "stock_code", "fiscal_year"):
            continue
        v = row.get(cn_header)
        raw_inputs[field] = None if pd.isna(v) else v

    fiscal_year = row.get("年度")
    try:
        fiscal_year = int(fiscal_year) if not pd.isna(fiscal_year) else None
    except (ValueError, TypeError):
        fiscal_year = None

    stock_code = row.get("股票代码")
    stock_code = None if pd.isna(stock_code) else str(stock_code).strip()

    return {
        "company_name": str(company_name).strip(),
        "stock_code": stock_code,
        "fiscal_year": fiscal_year,
        "raw_inputs": raw_inputs,
    }
