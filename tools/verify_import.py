"""生成一份符合导入模板的验证用 Excel，并跑通完整导入评估链路。

用途：验证「Excel 导入 → 字段校验 → 表3-1 指标计算 → 表7-2 缩尾/标准化
→ Firth logit → Sigmoid 分值 → 表7-1 定级 → 贡献归因」全链路是否与论文一致。

其中「海源复材」行的原始报表字段经表 3-1 口径计算后，恰好复现论文表 7-3
的八项指标，lev 负贡献经符号约束置零后预期 logit≈2.141、score≈89.5、D 级；
其余为测试企业，仅用于检验导入与批量评估机制，其结果由模型真实计算得出（非论文数据）。

运行：python tools/verify_import.py
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd

from core.config_loader import load_risk_levels
from services.assessment_service import assess_from_raw_inputs
from services.import_service import TEMPLATE_HEADERS, parse_excel

# ---------------------------------------------------------------------------
# 验证用数据：每行 = 一家企业的原始报表字段（中文表头，与导入模板一致）
# ---------------------------------------------------------------------------
ROWS = [
    {
        # 论文表 7-3 案例：原始字段按表 3-1 口径计算后精确复现八项指标
        "企业名称": "海源复材", "股票代码": "002529", "年度": 2024,
        "资产总计": 100.0, "负债合计": 66.6,
        "流动资产合计": 22.36, "流动负债合计": 40.0,
        "在建工程净额": 10.65, "固定资产净额": 30.0,
        "未分配利润": -135.1, "归母净利润": -18.4,
        "营业收入": 22.3, "上期营业收入": 35.34,
        "经营活动现金流量净额": -3.4342,
    },
    {
        # 测试企业 A：盈利、低杠杆、现金流健康（预期低风险）
        "企业名称": "测试稳健企业", "股票代码": "600001", "年度": 2024,
        "资产总计": 200.0, "负债合计": 60.0,
        "流动资产合计": 120.0, "流动负债合计": 50.0,
        "在建工程净额": 8.0, "固定资产净额": 90.0,
        "未分配利润": 60.0, "归母净利润": 24.0,
        "营业收入": 130.0, "上期营业收入": 110.0,
        "经营活动现金流量净额": 30.0,
    },
    {
        # 测试企业 B：微利、杠杆偏高（预期中风险区间）
        "企业名称": "测试中等企业", "股票代码": "600002", "年度": 2024,
        "资产总计": 150.0, "负债合计": 90.0,
        "流动资产合计": 45.0, "流动负债合计": 60.0,
        "在建工程净额": 20.0, "固定资产净额": 55.0,
        "未分配利润": 5.0, "归母净利润": 3.0,
        "营业收入": 80.0, "上期营业收入": 82.0,
        "经营活动现金流量净额": 2.0,
    },
]

OUT_PATH = os.path.join(_ROOT, "data", "sample", "验证用财务数据.xlsx")


def build_excel() -> None:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df = pd.DataFrame(ROWS, columns=TEMPLATE_HEADERS)
    with pd.ExcelWriter(OUT_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="财务数据")
    print(f"[生成] 验证用 Excel 已写入：{OUT_PATH}")
    print(f"[生成] 共 {len(df)} 行企业数据，列：{', '.join(TEMPLATE_HEADERS)}\n")


def run_chain() -> None:
    """读取刚生成的 Excel，跑完整导入评估链路并打印每步数值。"""
    with open(OUT_PATH, "rb") as fh:
        records, errors = parse_excel(fh)

    print("=" * 78)
    print("导入解析")
    print("=" * 78)
    print(f"解析出 {len(records)} 条记录；错误 {len(errors)} 条")
    for e in errors:
        print(f"  ! {e}")
    print()

    expected = load_risk_levels()["validation_case"]

    for rec in records:
        res = assess_from_raw_inputs(
            company_name=rec["company_name"],
            stock_code=rec["stock_code"],
            fiscal_year=rec["fiscal_year"],
            raw_inputs=rec["raw_inputs"],
        )
        print("=" * 78)
        head = f"{res['company_name']}　{res.get('stock_code') or '—'}　{res.get('fiscal_year') or '—'} 年度"
        print(head)
        print("=" * 78)
        if not res["ok"]:
            print(f"  评估未通过校验：{res['issues']}")
            print()
            continue

        # 指标 → 缩尾 → z → 贡献 明细
        print(f"{'指标':<12}{'原始值':>12}{'缩尾值':>12}{'z值':>10}{'贡献':>10}")
        print("-" * 56)
        for row in res["detail_rows"]:
            raw = "—" if row["raw"] is None else f"{row['raw']:.4f}"
            w = "—" if row["winsorized"] is None else f"{row['winsorized']:.4f}"
            z = "—" if row["z"] is None else f"{row['z']:.4f}"
            c = f"{row['contribution']:.4f}"
            tag = f" ({row['clip_note']})" if row["clip_note"] else ""
            print(f"{row['name_cn']:<12}{raw:>12}{w:>12}{z:>10}{c:>10}{tag}")
        print("-" * 56)
        print(f"截距 = {res['intercept']:.3f}")
        print(f"logit = {res['logit']:.4f}")
        print(f"score = {res['score']:.4f}")
        print(f"风险等级 = {res['risk_level']}（{res['level_meaning']}）")
        tops = "，".join(f"{t['name_cn']} {t['contribution']:.3f}" for t in res["top_risk_sources"])
        print(f"主要风险来源（前三正向贡献）= {tops}")

        # 海源复材与论文表 7-3 期望值对照
        if res["company_name"] == expected["company_name"]:
            print("\n  【与论文表 7-3 期望值对照】")
            checks = [
                ("logit", res["logit"], expected["expected_logit"], 0.01),
                ("score", res["score"], expected["expected_score"], 0.15),
            ]
            for name, got, exp, tol in checks:
                ok = abs(got - exp) <= tol
                print(f"    {name:<6} 实算 {got:.4f} | 论文 {exp} | 容差 {tol} -> {'✅ 一致' if ok else '❌ 偏差'}")
            lv_ok = res["risk_level"] == expected["expected_level"]
            print(f"    level  实算 {res['risk_level']} | 论文 {expected['expected_level']} -> {'✅ 一致' if lv_ok else '❌ 偏差'}")
            got_top = [t["variable"] for t in res["top_risk_sources"]]
            top_ok = got_top == expected["expected_top_risk_sources"]
            print(f"    top3   实算 {got_top} | 论文 {expected['expected_top_risk_sources']} -> {'✅ 一致' if top_ok else '❌ 偏差'}")
        print()


if __name__ == "__main__":
    build_excel()
    run_chain()
