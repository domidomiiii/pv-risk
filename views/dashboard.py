"""首页 · 研究概览。

展示项目整体情况与论文核心研究结论：关键数字卡片、三类模型、样本切分、
核心模型表现对比、主要结论与适用边界。只保留关键数字、少量图表与简短文字。
"""
from __future__ import annotations

import streamlit as st

from components.charts import MODEL_COLORS, grouped_bar
from components.metric_cards import render_metric_row
from components.tables import table_from_spec
from components.theme import marquee_html, stagger_html
from core.config_loader import load_research_overview, load_research_results


def render() -> None:
    ov = load_research_overview()
    rr = load_research_results()
    proj = ov["project"]
    motion = st.session_state.get("pv_motion", True)

    # 标题区：逐字入场 + 核心数字跑马灯
    st.markdown('<div class="pv-label">Solar PV Listed Companies · Financial Risk Warning</div>',
                unsafe_allow_html=True)
    st.markdown(stagger_html(proj["full_name"]), unsafe_allow_html=True)
    st.markdown(f'<div class="pv-subtitle">{proj["paper_title"]}</div>', unsafe_allow_html=True)
    marquee_items = [(n["label"], f'{n["value"]}{n.get("unit", "")}') for n in ov["core_numbers"]]
    marquee_items += [
        ("训练集亏损率", ov["sample_split"]["train"]["loss_rate"]),
        ("测试集亏损率", ov["sample_split"]["test"]["loss_rate"]),
    ]
    st.markdown(marquee_html(marquee_items, off=not motion), unsafe_allow_html=True)
    st.markdown(
        f'<div class="pv-card"><b>研究对象：</b>{proj["research_object"]}　|　'
        f'<b>研究目标：</b>{proj["research_goal"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pv-note">{proj["positioning"]}</div>',
        unsafe_allow_html=True,
    )

    # 关键数字卡片
    st.subheader("样本基本情况")
    render_metric_row(ov["core_numbers"], cols_per_row=3)

    # 三类模型
    st.subheader("三类模型")
    cols = st.columns(3)
    for col, m in zip(cols, ov["three_models"]):
        with col:
            extra = ""
            if "test_aupr" in m:
                extra = f"<br/>测试集 AUPR {m['test_aupr']} · AUC {m['test_auc']}"
            elif "test_aupr_range" in m:
                extra = f"<br/>测试集 AUPR {m['test_aupr_range']} · AUC {m['test_auc']}"
            elif "risk_score" in m:
                extra = f"<br/>风险分数 = {m['risk_score']}"
            st.markdown(
                f'<div class="pv-card"><b>{m["name"]}</b><br/>'
                f'<span style="color:#8a857b;font-size:0.85rem;">{m["role"]}</span>'
                f'{extra}</div>',
                unsafe_allow_html=True,
            )

    # 训练/测试切分
    st.subheader("训练集与测试集划分")
    split = ov["sample_split"]
    c1, c2 = st.columns(2)
    tr, te = split["train"], split["test"]
    with c1:
        st.markdown(
            f'<div class="pv-card"><b>训练集 {tr["period"]}</b><br/>'
            f'{tr["obs"]} 观测 · {tr["positives"]} 正例 · 亏损率 {tr["loss_rate"]}<br/>'
            f'<span style="color:#8a857b;font-size:0.82rem;">{tr["note"]}</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="pv-card"><b>测试集 {te["period"]}</b><br/>'
            f'{te["obs"]} 观测 · {te["positives"]} 正例 · 亏损率 {te["loss_rate"]}<br/>'
            f'<span style="color:#8a857b;font-size:0.82rem;">{te["note"]}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown(f'<div class="pv-note">{split["validation_design"]}</div>', unsafe_allow_html=True)

    # 核心模型表现对比（论文实证结果）
    st.subheader("核心模型表现对比（测试集 n=214）")
    st.markdown(
        '**表 5-4 数据** <span class="pv-paper-badge">论文实证结果</span>',
        unsafe_allow_html=True,
    )
    t54 = rr["table_5_4_model_comparison"]
    df = table_from_spec(t54)
    models = df["模型"].tolist()
    fig = grouped_bar(
        categories=models,
        series={"AUPR（主指标）": df["AUPR"].tolist(), "AUC（辅助指标）": df["AUC"].tolist()},
        title="各模型 AUPR / AUC 对比",
        y_title="指标值",
        height=440,
    )
    # 两个系列用不同颜色
    fig.data[0].marker.color = "#ff4d00"
    fig.data[1].marker.color = "#f4f1eb"
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        '<div class="pv-note">AUPR 为主指标、AUC 为辅；排序不一致时并列报告。'
        'LightGBM AUPR 点估计较高，但相对 ROA 差异可忽略（差 0.028，CI [−0.027, +0.072] 跨 0）。</div>',
        unsafe_allow_html=True,
    )

    # 主要结论
    st.subheader("主要结论")
    for c in ov["main_conclusions"]:
        with st.expander(f"结论 {c['id']}：{c['title']}", expanded=(c["id"] == 1)):
            st.write(c["detail"])

    # 适用边界
    st.subheader("适用边界")
    for b in ov["applicability_boundaries"]:
        st.markdown(f'<div class="pv-warn">{b}</div>', unsafe_allow_html=True)
