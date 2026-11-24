"""数据管理：Excel 导入、完整性检查、历史记录、结果导出、论文实证数据浏览。

不实现用户注册、权限管理、多人协作与云端数据管理。
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from components.tables import table_from_spec
from core.config_loader import (
    load_indicators, load_model_parameters, load_research_overview, load_research_results,
    load_risk_levels,
)
from database import repository
from services import assessment_service, export_service, import_service


def render() -> None:
    st.markdown("<h1>数据管理</h1>", unsafe_allow_html=True)
    tab_import, tab_history, tab_paper = st.tabs(
        ["Excel 导入与批量评估", "评估历史记录", "论文实证数据浏览"]
    )
    with tab_import:
        _tab_import()
    with tab_history:
        _tab_history()
    with tab_paper:
        _tab_paper_data()


# ---------------------------------------------------------------------------
def _tab_import() -> None:
    st.subheader("Excel 财务数据导入")
    st.markdown(
        '<div class="pv-note">下载模板 → 按列填写 → 上传；系统做完整性检查（缺失、分母为零），'
        '通过者批量评分并可保存。</div>',
        unsafe_allow_html=True,
    )
    tmpl_df = import_service.build_template_dataframe()
    st.download_button(
        "下载 Excel 导入模板",
        data=_df_to_excel_bytes(tmpl_df),
        file_name="PV-Risk_财务数据导入模板.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded = st.file_uploader("上传财务数据 Excel", type=["xlsx", "xls"], key="dm_upload")
    if uploaded is None:
        return

    records, errors = import_service.parse_excel(uploaded)
    for e in errors:
        st.markdown(f'<div class="pv-warn">{e}</div>', unsafe_allow_html=True)
    if not records:
        st.info("未解析到有效记录。")
        return

    st.markdown(f"**解析到 {len(records)} 条记录，逐条评估：**")
    results = []
    for rec in records:
        assessment = assessment_service.assess_from_raw_inputs(
            company_name=rec["company_name"],
            stock_code=rec["stock_code"],
            fiscal_year=rec["fiscal_year"],
            raw_inputs=rec["raw_inputs"],
        )
        results.append(assessment)

    summary_rows = []
    for a in results:
        if a.get("ok"):
            summary_rows.append({
                "企业名称": a["company_name"], "股票代码": a.get("stock_code") or "",
                "年度": a.get("fiscal_year"), "logit": round(a["logit"], 3),
                "风险评分": round(a["score"], 1), "风险等级": a["risk_level"],
                "风险含义": a["level_meaning"],
                "主要风险来源": "、".join(s["name_cn"] for s in a["top_risk_sources"]),
                "状态": "已评分",
            })
        else:
            summary_rows.append({
                "企业名称": a["company_name"], "股票代码": a.get("stock_code") or "",
                "年度": a.get("fiscal_year"), "logit": "—", "风险评分": "—",
                "风险等级": "—", "风险含义": "—",
                "主要风险来源": "；".join(i["message"] for i in a["issues"][:1]),
                "状态": "校验未通过",
            })
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    ok_results = [a for a in results if a.get("ok")]
    c1, c2 = st.columns(2)
    with c1:
        if st.button("保存全部已评分记录到历史", use_container_width=True,
                     disabled=not ok_results):
            saved = 0
            for a in ok_results:
                repository.save_assessment(assessment_service.result_to_db_record(a))
                saved += 1
            st.success(f"已保存 {saved} 条记录。")
    with c2:
        st.download_button(
            "导出本批评估结果（Excel）",
            data=export_service.export_history(
                [{"company_name": a["company_name"], "stock_code": a.get("stock_code"),
                  "fiscal_year": a.get("fiscal_year"), "logit": a.get("logit"),
                  "score": a.get("score"), "risk_level": a.get("risk_level"),
                  "level_meaning": a.get("level_meaning"),
                  "top_risk_sources": a.get("top_risk_sources", [])}
                 for a in ok_results]
            ),
            file_name="PV-Risk_批量评估结果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            disabled=not ok_results,
        )


# ---------------------------------------------------------------------------
def _tab_history() -> None:
    st.subheader("企业风险评估历史记录")
    records = repository.list_assessments()
    total = repository.count_assessments()
    st.caption(f"共 {total} 条记录。")
    if not records:
        st.info("暂无历史记录。")
        return

    list_df = pd.DataFrame([
        {"ID": r["id"], "企业名称": r["company_name"], "股票代码": r.get("stock_code") or "",
         "年度": r.get("fiscal_year"), "评分": round(r["score"], 1) if r.get("score") else "—",
         "等级": r.get("risk_level"), "创建时间": r.get("created_at")}
        for r in records
    ])
    st.dataframe(list_df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns([3, 1])
    with c1:
        chosen_id = st.selectbox(
            "查看记录详情",
            options=[r["id"] for r in records],
            format_func=lambda i: next(
                f"#{i} {r['company_name']}（{r.get('fiscal_year')}）"
                for r in records if r["id"] == i
            ),
        )
    with c2:
        st.download_button(
            "导出全部历史（Excel）",
            data=export_service.export_history(records),
            file_name="PV-Risk_评估历史.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    detail = repository.get_assessment(chosen_id)
    if detail:
        _render_history_detail(detail)
        if st.button(f"删除记录 #{chosen_id}"):
            repository.delete_assessment(chosen_id)
            st.success("已删除。")
            st.rerun()


def _render_history_detail(detail: dict) -> None:
    st.markdown(
        f'<div class="pv-card"><b>{detail["company_name"]}</b>　'
        f'<span style="color:#64748b;">{detail.get("stock_code") or "无代码"}</span>　'
        f'{detail.get("fiscal_year")} 年度　|　评分 '
        f'<b>{detail["score"]:.1f}</b>　等级 <b>{detail["risk_level"]}</b>'
        f'（{detail.get("level_meaning")}）</div>',
        unsafe_allow_html=True,
    )
    indicators = detail.get("indicators") or {}
    z = detail.get("z_scores") or {}
    contrib = detail.get("contributions") or {}
    wins = detail.get("winsorized") or {}
    if indicators:
        df = pd.DataFrame([
            {"指标": k, "原始值": indicators.get(k), "缩尾值": wins.get(k),
             "标准化 z": z.get(k), "对 logit 贡献": contrib.get(k)}
            for k in indicators
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    top = detail.get("top_risk_sources") or []
    if top:
        st.markdown("**主要风险来源：** " + "、".join(
            f"{s['name_cn']}({s['contribution']:+.3f})" for s in top))


# ---------------------------------------------------------------------------
def _tab_paper_data() -> None:
    st.subheader("论文实证数据")
    st.markdown(
        '<div class="pv-note">内置论文实证数据配置（只读浏览）。</div>',
        unsafe_allow_html=True,
    )
    sources = {
        "指标定义（表 3-1）": load_indicators(),
        "模型参数（表 4-1/5-1/7-2、Altman Z''）": load_model_parameters(),
        "风险等级与验证案例（表 7-1/7-3）": load_risk_levels(),
        "研究概览与结论": load_research_overview(),
        "实证结果表格（表 3-2 至 6-5）": load_research_results(),
    }
    chosen = st.selectbox("选择配置文件", list(sources.keys()))
    st.json(sources[chosen], expanded=False)

    # 论文实证表格清单
    st.markdown("**论文实证结果表格索引**")
    rr = load_research_results()
    table_keys = [k for k in rr.keys() if k.startswith("table_")]
    idx_rows = []
    for k in table_keys:
        spec = rr[k]
        df = table_from_spec(spec)
        idx_rows.append({"配置键": k, "标题": spec.get("title", ""),
                         "行数": len(df), "列数": len(df.columns)})
    st.dataframe(pd.DataFrame(idx_rows), use_container_width=True, hide_index=True)


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="财务数据")
    return buf.getvalue()
