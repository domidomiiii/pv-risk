"""企业风险评估（系统核心功能）。

包含：企业信息与财务数据输入（手动 / Excel / 内置验证案例）、八项指标自动计算、
Firth Logit 评分卡、评估结果展示（指标原始值/缩尾值/z/贡献、logit、评分、等级、
Top-3 风险来源）、保存历史与导出。所有计算真实运行。
"""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from components.metric_cards import render_level_card
from components.theme import level_badge_html
from core.config_loader import load_indicators, load_risk_levels
from database import repository
from services import assessment_service, export_service, import_service

# 原始报表字段（中文标签 + 内部键）
_RAW_FIELDS = load_indicators()["raw_input_fields"]
_VALIDATION_CASE = load_risk_levels()["validation_case"]


def render() -> None:
    st.markdown("<h1>企业风险评估</h1>", unsafe_allow_html=True)
    st.markdown(
        '<div class="pv-subtitle">输入财务数据，实时计算风险评分、等级与主要风险来源。</div>',
        unsafe_allow_html=True,
    )

    input_mode = st.radio(
        "数据录入方式",
        ["手动输入财务报表数据", "上传 Excel", "内置验证案例（海源复材 2024）"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if input_mode == "手动输入财务报表数据":
        _manual_input_flow()
    elif input_mode == "上传 Excel":
        _excel_flow()
    else:
        _validation_case_flow()


# ---------------------------------------------------------------------------
# 手动输入
# ---------------------------------------------------------------------------
def _manual_input_flow() -> None:
    with st.form("manual_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            company_name = st.text_input("企业名称", placeholder="如：海源复材")
        with c2:
            stock_code = st.text_input("股票代码", placeholder="如：002529")
        with c3:
            fiscal_year = st.number_input("财务数据年度", min_value=2000, max_value=2030,
                                          value=2024, step=1)

        st.markdown("**财务报表数据**（合并报表·年报口径，单位统一）")
        fields: Dict[str, Any] = {}
        cols = st.columns(3)
        for i, f in enumerate(_RAW_FIELDS):
            with cols[i % 3]:
                # revenue_prev 允许留空（仅影响 growth）
                val = st.number_input(
                    f"{f['name_cn']}（{f['field']}）",
                    format="%.4f",
                    step=0.0001,
                    value=None,
                    key=f"manual_{f['field']}",
                    help=f"所属报表：{f['statement']}" + (f"；{f['note']}" if f.get("note") else ""),
                )
                fields[f["field"]] = val

        submitted = st.form_submit_button("计算风险评分", type="primary", use_container_width=True)

    if submitted:
        assessment = assessment_service.assess_from_raw_inputs(
            company_name=company_name or "缺省企业",
            stock_code=stock_code or None,
            fiscal_year=int(fiscal_year),
            raw_inputs=fields,
        )
        _render_result(assessment, allow_save=True)


# ---------------------------------------------------------------------------
# Excel 上传
# ---------------------------------------------------------------------------
def _excel_flow() -> None:
    st.markdown(
        '<div class="pv-note">下载模板按列填写后上传，表头与模板一致；「上期营业收入」留空。</div>',
        unsafe_allow_html=True,
    )
    tmpl_df = import_service.build_template_dataframe()
    st.download_button(
        "下载 Excel 模板",
        data=_df_to_excel_bytes(tmpl_df),
        file_name="PV-Risk_财务数据导入模板.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded = st.file_uploader("上传财务数据 Excel", type=["xlsx", "xls"])
    if uploaded is not None:
        records, errors = import_service.parse_excel(uploaded)
        for e in errors:
            st.markdown(f'<div class="pv-warn">{e}</div>', unsafe_allow_html=True)
        if not records:
            st.info("解析结果为空，请检查文件内容。")
            return

        st.markdown(f"**解析到 {len(records)} 条记录**，选择其一进行评分：")
        options = [f"{r['company_name']}（{r['stock_code'] or '代码缺省'} · {r['fiscal_year']}）"
                   for r in records]
        chosen = st.selectbox("选择企业", options)
        idx = options.index(chosen)
        rec = records[idx]
        assessment = assessment_service.assess_from_raw_inputs(
            company_name=rec["company_name"],
            stock_code=rec["stock_code"],
            fiscal_year=rec["fiscal_year"],
            raw_inputs=rec["raw_inputs"],
        )
        _render_result(assessment, allow_save=True)


def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="财务数据")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 内置验证案例
# ---------------------------------------------------------------------------
def _validation_case_flow() -> None:
    case = _VALIDATION_CASE
    st.markdown(
        f'<div class="pv-card"><b>内置验证案例：{case["company_name"]}（{case["stock_code"]}）'
        f'{case["year"]} 年度</b><br/>'
        f'<span style="color:#64748b;font-size:0.85rem;">'
        f'按表 7-3 八项指标实时复算，验证 logit={case["expected_logit"]}、score={case["expected_score"]}、'
        f'{case["expected_level"]} 级；次年归母净利润为负。</span></div>',
        unsafe_allow_html=True,
    )

    # 以论文表 7-3 的八项指标原始值直接评分（真实计算，不写死结果）
    assessment = assessment_service.assess_from_indicators(
        company_name=case["company_name"],
        stock_code=case["stock_code"],
        fiscal_year=case["year"],
        indicator_values=dict(case["raw_indicators"]),
    )
    _render_result(assessment, allow_save=False, validation_case=case)


# ---------------------------------------------------------------------------
# 结果渲染
# ---------------------------------------------------------------------------
def _render_result(assessment: Dict[str, Any], allow_save: bool,
                   validation_case: Dict[str, Any] | None = None) -> None:
    st.divider()

    if not assessment.get("ok"):
        st.error("输入有误，评分中止：")
        for issue in assessment.get("issues", []):
            st.markdown(f'<div class="pv-warn">[{issue["level"]}] {issue["message"]}</div>',
                        unsafe_allow_html=True)
        return

    # 校验提示（warning）
    warns = [i for i in assessment.get("issues", []) if i["level"] == "warning"]
    for w in warns:
        st.markdown(f'<div class="pv-warn">{w["message"]}</div>', unsafe_allow_html=True)

    # 顶部：企业 + 等级卡
    st.subheader("评估结果")
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.markdown(
            f'<div class="pv-card"><b style="font-size:1.15rem;">{assessment["company_name"]}</b>'
            f'　<span style="color:#64748b;">{assessment.get("stock_code") or "代码缺省"}</span>'
            f'　<span class="pv-tag">{assessment.get("fiscal_year")} 年度</span></div>',
            unsafe_allow_html=True,
        )
        # 关键数字
        m1, m2, m3 = st.columns(3)
        m1.metric("logit", f"{assessment['logit']:.3f}")
        m2.metric("风险评分", f"{assessment['score']:.1f}")
        m3.metric("风险等级", assessment["risk_level"])

        # Top-3 风险来源
        st.markdown("**主要风险来源**（正向贡献最大三项）")
        top = assessment["top_risk_sources"]
        if top:
            tcols = st.columns(len(top))
            for col, s in zip(tcols, top):
                with col:
                    st.markdown(
                        f'<div class="pv-card" style="text-align:center;">'
                        f'<div style="color:#64748b;font-size:0.8rem;">{s["name_cn"]}</div>'
                        f'<div style="font-size:1.4rem;font-weight:700;color:#d64545;">'
                        f'{s["contribution"]:+.3f}</div>'
                        f'<div style="color:#94a3b8;font-size:0.72rem;">{s["variable"]}</div></div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("各指标贡献均 ≤ 0，风险相对偏低。")
    with c_right:
        render_level_card(assessment["risk_level"], assessment["level_meaning"],
                          assessment["score"])

    st.markdown(
        '<div class="pv-note">评分为 0—100 相对风险评分，用于企业间排序与初筛；'
        '「贡献」表示关联强度。</div>',
        unsafe_allow_html=True,
    )

    # 指标明细表
    st.subheader("指标计算明细")
    detail_df = pd.DataFrame([
        {
            "指标": r["variable"],
            "中文名": r["name_cn"],
            "原始值": _fmt(r["raw"]),
            "缩尾值": _fmt(r["winsorized"]),
            "标准化 z": _fmt(r["z"]),
            "对 logit 贡献": _fmt(r["contribution"]),
            "缩尾提示": r["clip_note"] or "—",
        }
        for r in assessment["detail_rows"]
    ])
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    if assessment.get("missing_variables"):
        st.markdown(
            f'<div class="pv-warn">以下指标缺失，贡献按 0 计入：'
            f'{", ".join(assessment["missing_variables"])}。</div>',
            unsafe_allow_html=True,
        )

    # 验证案例对照
    if validation_case is not None:
        _render_case_verification(assessment, validation_case)

    # 导出与保存
    st.subheader("导出与保存")
    b1, b2 = st.columns(2)
    with b1:
        excel_bytes = export_service.export_single_assessment(assessment)
        st.download_button(
            "导出本次评估结果（Excel）",
            data=excel_bytes,
            file_name=f"PV-Risk_{assessment['company_name']}_{assessment.get('fiscal_year')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with b2:
        if allow_save:
            if st.button("保存到历史记录", use_container_width=True):
                rec = assessment_service.result_to_db_record(assessment)
                rid = repository.save_assessment(rec)
                st.success(f"已保存（记录 ID = {rid}），可在「数据管理」查看。")
        else:
            st.caption("内置验证案例独立于历史记录。")


def _render_case_verification(assessment: Dict[str, Any], case: Dict[str, Any]) -> None:
    """将实时复算结果与论文表 7-3 公布值逐项对照。"""
    st.subheader("表 7-3 复算验证")
    rows = []
    for var in case["raw_indicators"]:
        rows.append({
            "指标": var,
            "论文 z 值": case["expected_z"][var],
            "系统 z 值": round(assessment["z_scores"][var], 2),
            "论文贡献": case["expected_contribution"][var],
            "系统贡献": round(assessment["contributions"][var], 3),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    cmp = pd.DataFrame([
        {"项目": "logit", "论文值": case["expected_logit"], "系统复算": round(assessment["logit"], 3)},
        {"项目": "score", "论文值": case["expected_score"], "系统复算": round(assessment["score"], 2)},
        {"项目": "风险等级", "论文值": case["expected_level"], "系统复算": assessment["risk_level"]},
        {"项目": "Top 风险来源", "论文值": "、".join(case["expected_top_risk_sources"]),
         "系统复算": "、".join(s["variable"] for s in assessment["top_risk_sources"])},
    ])
    st.dataframe(cmp, use_container_width=True, hide_index=True)

    tol_ok = (
        abs(assessment["logit"] - case["expected_logit"]) < 0.01
        and abs(assessment["score"] - case["expected_score"]) < 0.15
        and assessment["risk_level"] == case["expected_level"]
        and [s["variable"] for s in assessment["top_risk_sources"]] == case["expected_top_risk_sources"]
    )
    if tol_ok:
        st.success("✅ 实时复算与表 7-3 一致。")
    else:
        st.error("复算与论文存在偏差，请检查数据精度与计算顺序。")


def _fmt(v) -> str:
    return "—" if v is None else f"{v:.4f}"
