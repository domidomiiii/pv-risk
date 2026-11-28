"""生成示例导入 Excel（data/sample/）。

示例行的原始报表字段经论文表 3-1 口径计算后，恰好复现论文表 7-3
海源复材 2024 年度的八项指标，可用于验证「Excel 导入 → 指标计算 → Firth 评分」
全链路是否得到 logit≈2.141、score≈89.5、D 级（lev 负贡献经符号约束置零）。

另附两行占位示例，便于测试批量导入。运行：python tools/make_sample_data.py
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd

from services.import_service import TEMPLATE_HEADERS

# 海源复材 2024：原始报表字段（单位任意，比例一致即可），复现论文表 7-3 指标
_HAIYUAN_ROW = {
    "企业名称": "海源复材",
    "股票代码": "002529",
    "年度": 2024,
    "资产总计": 100.0,
    "负债合计": 66.6,
    "流动资产合计": 22.36,
    "流动负债合计": 40.0,
    "在建工程净额": 10.65,
    "固定资产净额": 30.0,
    "未分配利润": -135.1,
    "归母净利润": -18.4,
    "营业收入": 22.3,
    "上期营业收入": 35.34,
    "经营活动现金流量净额": -3.4342,
}

# 另一家低风险占位示例（盈利、低杠杆）
_HEALTHY_ROW = {
    "企业名称": "示例稳健企业",
    "股票代码": "600000",
    "年度": 2024,
    "资产总计": 200.0,
    "负债合计": 60.0,
    "流动资产合计": 120.0,
    "流动负债合计": 60.0,
    "在建工程净额": 10.0,
    "固定资产净额": 80.0,
    "未分配利润": 50.0,
    "归母净利润": 20.0,
    "营业收入": 120.0,
    "上期营业收入": 100.0,
    "经营活动现金流量净额": 25.0,
}


def main() -> None:
    sample_dir = os.path.join(_ROOT, "data", "sample")
    uploads_dir = os.path.join(_ROOT, "data", "uploads")
    os.makedirs(sample_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)

    df = pd.DataFrame([_HAIYUAN_ROW, _HEALTHY_ROW], columns=TEMPLATE_HEADERS)
    out_path = os.path.join(sample_dir, "示例财务数据.xlsx")
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="财务数据")

    # 同时放一份空白模板
    tmpl = pd.DataFrame([{h: "" for h in TEMPLATE_HEADERS}], columns=TEMPLATE_HEADERS)
    tmpl_path = os.path.join(sample_dir, "导入模板.xlsx")
    with pd.ExcelWriter(tmpl_path, engine="openpyxl") as writer:
        tmpl.to_excel(writer, index=False, sheet_name="财务数据")

    # uploads 目录占位
    gitkeep = os.path.join(uploads_dir, ".gitkeep")
    if not os.path.exists(gitkeep):
        open(gitkeep, "w", encoding="utf-8").close()

    print(f"已生成：{out_path}")
    print(f"已生成：{tmpl_path}")


if __name__ == "__main__":
    main()
