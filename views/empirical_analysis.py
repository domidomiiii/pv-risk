"""实证研究：以顶部二级标签整合论文第 3—7 章全部研究内容。

标签：
    A 研究设计与样本（第 3 章）
    B 模型与研究方法（第 4 章）
    C 实证结果与模型比较（第 5 章）
    D 稳健性检验（第 6 章）
    E 评分卡构建与案例分析（第 7 章）

所有实证数据来自 config/research_results.json 与 model_parameters.json，
均标注为「论文实证结果」。图表仅用论文已公布汇总值绘制，不伪造逐点数据；
图 5-1/5-2/5-3 因无逐点数据以表格/文字呈现。
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.charts import (
    MODEL_COLORS, bar_line_combo, errorbar_range, grouped_bar, line_chart, single_bar,
)
from components.tables import render_paper_table, table_from_spec
from core.config_loader import (
    load_indicators, load_model_parameters, load_research_overview, load_research_results,
    load_risk_levels,
)

TABS = [
    "A · 研究设计与样本",
    "B · 模型与研究方法",
    "C · 实证结果与模型比较",
    "D · 稳健性检验",
    "E · 评分卡构建与案例",
]


def render() -> None:
    st.markdown("<h1>实证研究</h1>", unsafe_allow_html=True)
    st.markdown(
        '<div class="pv-subtitle">第 3—7 章研究内容。'
        '<span class="pv-paper-badge">论文实证结果</span> = 论文已公布数据。</div>',
        unsafe_allow_html=True,
    )
    tab_a, tab_b, tab_c, tab_d, tab_e = st.tabs(TABS)
    with tab_a:
        _tab_design()
    with tab_b:
        _tab_models()
    with tab_c:
        _tab_results()
    with tab_d:
        _tab_robustness()
    with tab_e:
        _tab_scorecard()


# ===========================================================================
# 标签 A · 研究设计与样本（第 3 章）
# ===========================================================================
def _tab_design() -> None:
    rr = load_research_results()
    summ = rr["_meta"]["sample_summary"]

    st.subheader("研究对象与行业认定")
    st.markdown(
        f'<div class="pv-card">研究对象为沪深 A 股光伏上市公司，面板构建期 '
        f'{summ["panel_period"]}。行业认定标准：{summ["industry_criteria"]}。'
        f'数据来源：{summ["data_source"]}。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("样本筛选流程")
    render_paper_table(rr["table_3_2_sample_screening"])

    st.subheader("八项财务指标定义")
    inds = load_indicators()["indicators"]
    ind_df = pd.DataFrame([
        {"维度": i["dimension"], "变量": i["variable"], "定义": i["definition"],
         "预期方向": i["expected_direction"]}
        for i in inds
    ])
    st.markdown("**表 3-1 指标体系**", unsafe_allow_html=False)
    st.dataframe(ind_df, use_container_width=True, hide_index=True)
    st.markdown(
        '<div class="pv-note">"预期方向"= 指标升高时次年亏损概率的变化方向；'
        'roa、reta、asset_turn 分母为期末总资产；cip_fa 方向由实证确定。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("盈利恶化标签定义")
    st.markdown(
        f'<div class="pv-card">标签：{summ["label"]}；正例 {summ["positive_cases"]} 个'
        f'（{summ["positive_rate"]}）。标签用下一年归母净利润、ROA 用当期归母净利润，'
        '二者分属相邻会计期间，ROA 具先验优势。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("描述性统计")
    render_paper_table(rr["table_3_3_descriptive_stats"])

    st.subheader("各年观测数与下一年度亏损率")
    t34 = rr["table_3_4_yearly_loss_rate"]
    render_paper_table(t34)
    df34 = table_from_spec(t34)
    fig = bar_line_combo(
        categories=[str(y) for y in df34["特征年"].tolist()],
        bars=df34["观测数"].tolist(),
        line=df34["次年亏损率"].tolist(),
        title="表 3-4：各年观测数（柱）与下一年度亏损率（线）",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("行业深度亏损期划分与样本切分")
    cyc = t34["cycle_periodization"]
    st.markdown(
        f'<div class="pv-card"><b>周期分期：</b>常规期 {cyc["normal_period"]}，'
        f'年度亏损率均值 {cyc["normal_avg_loss_rate_yearly"]}，合并发生率 '
        f'{cyc["normal_pooled_loss_rate"]}；深度亏损期 {cyc["deep_loss_period"]}。<br/>'
        f'<b>操作性界定：</b>{cyc["definition"]}。<br/>'
        f'<b>对应行业冲击：</b>{cyc["shock_event"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="pv-warn">{cyc["caveat"]}</div>', unsafe_allow_html=True)
    split = load_research_overview()["sample_split"]
    tr, te = split["train"], split["test"]
    c1, c2 = st.columns(2)
    c1.markdown(
        f'<div class="pv-card"><b>训练集 {tr["period"]}</b><br/>{tr["obs"]} 观测 · '
        f'{tr["positives"]} 正例 · 亏损率 {tr["loss_rate"]}</div>', unsafe_allow_html=True)
    c2.markdown(
        f'<div class="pv-card"><b>测试集 {te["period"]}</b><br/>{te["obs"]} 观测 · '
        f'{te["positives"]} 正例 · 亏损率 {te["loss_rate"]}（时间外推检验）</div>',
        unsafe_allow_html=True)


# ===========================================================================
# 标签 B · 模型与研究方法（第 4 章）
# ===========================================================================
def _tab_models() -> None:
    rr = load_research_results()
    mp = load_model_parameters()

    st.subheader("主模型：Firth Logit")
    firth = mp["firth_logit"]
    st.markdown(
        f'<div class="pv-card">{firth["description"]}<br/>'
        f'<b>logit 公式：</b>{firth["logit_formula"]}　<b>评分公式：</b>{firth["score_formula"]}<br/>'
        f'<b>EPV 适用性：</b>{firth["epv_note"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pv-note">Firth 惩罚似然在分离情形下仍有有限解、减小小样本偏误；'
        '用于风险来源解释与评分卡，预测精度次于 ROA 与 LightGBM。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("对照模型：LightGBM")
    lgb = mp["lightgbm"]
    st.markdown(f'<div class="pv-card">{lgb["description"]}</div>', unsafe_allow_html=True)
    hyper_df = pd.DataFrame([
        {"参数": k, "取值": v["value"], "作用": v["purpose"]}
        for k, v in lgb["hyperparameters"].items()
    ])
    st.markdown("**表 4-1 LightGBM 超参数设置** <span class='pv-paper-badge'>论文实证结果</span>",
                unsafe_allow_html=True)
    st.dataframe(hyper_df, use_container_width=True, hide_index=True)

    st.markdown("**表 4-2 参数设置的合理性检验**", unsafe_allow_html=True)
    render_paper_table(rr["table_4_2_param_check"], show_title=False)
    st.markdown(
        f'<div class="pv-warn">{lgb["availability_note"]}</div>', unsafe_allow_html=True)

    st.subheader("基准模型：Altman Z'' 与单变量 ROA")
    z = mp["altman_z_double_prime"]
    st.markdown(
        f'<div class="pv-card"><b>Altman Z\'\'：</b>{z["formula"]}<br/>'
        f'X1={z["variables"]["X1"]}；X2={z["variables"]["X2"]}；'
        f'X3={z["variables"]["X3"]}；X4={z["variables"]["X4"]}。<br/>'
        f'{z["risk_score_direction"]}<br/>'
        f'<span style="color:#8a857b;font-size:0.84rem;">{z["caveat"]}</span></div>',
        unsafe_allow_html=True,
    )
    roa = mp["univariate_roa_baseline"]
    st.markdown(
        f'<div class="pv-card"><b>单变量 ROA 基准：</b>{roa["description"]}　'
        f'风险分数 = {roa["risk_score_formula"]}</div>', unsafe_allow_html=True)

    st.subheader("时间外推验证设计")
    st.markdown(
        '<div class="pv-card">滚动时间外推：预测 2020 年以 2014—2019 训练，2021 年以 2014—2020 训练，'
        '依此递推至 2024 年。每轮缩尾分位点与标准化参数只由该轮训练集计算，预测时仅用该轮训练集信息。'
        '训练集（2014—2022）年度亏损率最高 22.7%，集中亏损情形仅出现在测试期；'
        '特征年度 2023 的输入落在训练分布之外，构成集中亏损阶段的首次样本外检验。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("模型选择与功能分工")
    st.markdown(
        '<div class="pv-note">Firth Logit 负责可解释的条件关联与风险来源；LightGBM 检验非线性与交互的'
        '样本外增量；单变量 ROA 为透明基准。模型比较按功能分工展开。</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# 标签 C · 实证结果与模型比较（第 5 章）
# ===========================================================================
def _tab_results() -> None:
    rr = load_research_results()

    st.subheader("5.1 Firth Logit 估计结果")
    render_paper_table(rr["table_5_1_firth_estimation"])
    t51 = rr["table_5_1_firth_estimation"]
    coef_df = table_from_spec(t51)
    coef_df = coef_df[coef_df["变量"] != "截距"]
    fig = single_bar(
        categories=coef_df["变量"].tolist(),
        values=coef_df["系数"].tolist(),
        title="表 5-1：Firth Logit 各指标系数（训练集 n=551）",
        y_title="系数",
        color="#ff4d00",
    )
    st.plotly_chart(fig, use_container_width=True)
    sup = t51["lev_suppression_evidence"]
    st.markdown(
        f'<div class="pv-note"><b>lev 负系数（抑制效应）：</b>单变量系数 {sup["univariate_coef"]}'
        f'（p={sup["univariate_p"]}），加入 roa、ocf 后转负，全变量 {sup["full_model_coef"]}；'
        f'VIF {sup["vif_range"]}，lev 与 roa 相关 {sup["lev_roa_corr"]}。'
        '方向变化归因于抑制效应，属关联关系。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("5.1 按资产负债率分组的亏损率")
    t52 = rr["table_5_2_loss_by_leverage"]
    render_paper_table(t52)
    df52 = table_from_spec(t52)
    st.plotly_chart(
        single_bar(df52["负债率区间"].tolist(), df52["亏损率"].tolist(),
                   "表 5-2：各杠杆区间亏损率", y_title="亏损率", color="#ff4d00"),
        use_container_width=True,
    )

    st.subheader("5.1 分时期、分杠杆区间的亏损率")
    render_paper_table(rr["table_5_3_loss_by_period_leverage"])

    st.subheader("5.2 模型对比与双重基准")
    t54 = rr["table_5_4_model_comparison"]
    render_paper_table(t54)
    df54 = table_from_spec(t54)
    models = df54["模型"].tolist()
    fig54 = grouped_bar(
        categories=models,
        series={"AUPR（主指标）": df54["AUPR"].tolist(), "AUC（辅助指标）": df54["AUC"].tolist()},
        title="表 5-4：各模型 AUPR / AUC 对比（测试集 n=214）",
        y_title="指标值", height=460,
    )
    fig54.data[0].marker.color = "#ff4d00"
    fig54.data[1].marker.color = "#f4f1eb"
    st.plotly_chart(fig54, use_container_width=True)
    ci = t54["bootstrap_ci"]
    st.markdown(
        f'<div class="pv-note"><b>配对 Bootstrap 95% CI：</b>'
        f'AUPR（类别加权 LGB vs ROA）差 {ci["aupr_lgb_cat_vs_roa"]["diff"]}，'
        f'CI {ci["aupr_lgb_cat_vs_roa"]["ci95"]}（跨 0，差异可忽略）；'
        f'AUC（ROA vs Firth）差 {ci["auc_roa_vs_firth"]["diff"]}，'
        f'CI {ci["auc_roa_vs_firth"]["ci95"]}（CI 全正，ROA 更优）；'
        f'AUC（ROA vs 类别加权 LGB）差 {ci["auc_roa_vs_lgb_cat"]["diff"]}，'
        f'CI {ci["auc_roa_vs_lgb_cat"]["ci95"]}（跨 0，差异可忽略）。</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pv-warn">图 5-1（ROC/PR 曲线）以上表与柱状图呈现。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("5.3 滚动外推与周期敏感性")
    t55 = rr["table_5_5_rolling_extrapolation"]
    render_paper_table(t55)
    df55 = table_from_spec(t55)
    years = df55["特征年度"].tolist()
    fig55 = line_chart(
        x=years,
        series={
            "Firth AUC": df55["Firth AUC"].tolist(),
            "LightGBM(类别加权) AUC": df55["LightGBM(类别加权) AUC"].tolist(),
            "单变量 ROA 的 AUC": df55["单变量 ROA 的 AUC"].tolist(),
        },
        title="表 5-5：滚动外推逐年 AUC（跨年比较以 AUC 为主线）",
        x_title="特征年度", y_title="AUC", height=440,
    )
    st.plotly_chart(fig55, use_container_width=True)
    for kf in t55["key_findings"]:
        st.markdown(f"- {kf}")
    st.markdown(
        '<div class="pv-note">模型 A（固定 2014—2022）与模型 C（滚动至 2023）的 AUC 差'
        '（0.715 vs 0.801）来自训练更新与时期变化两种来源。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("5.4 SHAP 解释")
    t56 = rr["table_5_6_shap_importance"]
    render_paper_table(t56)
    df56 = table_from_spec(t56)
    st.plotly_chart(
        single_bar(df56["特征"].tolist(), df56["平均绝对 SHAP 值"].tolist(),
                   "表 5-6：SHAP 特征重要性排序（类别加权 LightGBM）",
                   y_title="平均绝对 SHAP 值", color="#ff4d00"),
        use_container_width=True,
    )
    st.markdown(
        '<div class="pv-warn">图 5-2/5-3 以表 5-6 重要性排序呈现。'
        '图 5-3 结论：资产负债率与风险贡献呈倒 U 型，标准化值 0.5 附近（负债率约 55%）SHAP 由正转负，'
        '超 1.0（约 65% 以上）进一步下降；边际风险以表 5-2 为准。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("5.5 概率校准")
    t57 = rr["table_5_7_calibration"]
    render_paper_table(t57)
    df57 = table_from_spec(t57)
    fig57 = grouped_bar(
        categories=df57["模型"].tolist(),
        series={"平均预测概率": df57["平均预测概率"].tolist(),
                "Brier Score": df57["Brier Score"].tolist()},
        title="表 5-7 / 图 5-4：各模型平均预测概率与 Brier（实际亏损率 44.86%）",
        y_title="数值", height=440,
    )
    fig57.data[0].marker.color = "#ff4d00"
    fig57.data[1].marker.color = "#f4f1eb"
    fig57.add_hline(y=0.4486, line_dash="dash", line_color="#f4f1eb",
                    annotation_text="实际亏损率 44.86%")
    st.plotly_chart(fig57, use_container_width=True)
    st.markdown(
        f'<div class="pv-note">{t57["notes"]}</div>', unsafe_allow_html=True)

    st.subheader("5.6 预警名单检验")
    t58 = rr["table_5_8_warning_list_2024"]
    render_paper_table(t58)
    st.markdown(
        f'<div class="pv-card">命中率 {t58["hit_rate"]}；基准率 {t58["baseline_rate"]}，'
        f'随机期望命中 {t58["random_expected_hits"]} 家，实际为期望的 {t58["actual_to_expected"]} 倍，'
        f'超几何检验 p={t58["hypergeometric_p"]}（p 值高于 5% 阈值，作为应用示例）。<br/>'
        f'<b>预警名单外企业子集：</b>{t58["unwarned_subset"]["count"]} 家中 '
        f'{t58["unwarned_subset"]["hits"]} 家亏损，命中率 {t58["unwarned_subset"]["hit_rate"]}。<br/>'
        f'<b>误判分析：</b>{t58["misjudgment_analysis"]}</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# 标签 D · 稳健性检验（第 6 章）
# ===========================================================================
def _tab_robustness() -> None:
    rr = load_research_results()

    st.subheader("6.1 系数的 Bootstrap 稳定性")
    t61 = rr["table_6_1_bootstrap_stability"]
    render_paper_table(t61)
    df61 = table_from_spec(t61)
    st.plotly_chart(
        errorbar_range(
            categories=df61["变量"].tolist(),
            centers=df61["原样本系数"].tolist(),
            lows=[ci[0] for ci in df61["95% 百分位区间"].tolist()],
            highs=[ci[1] for ci in df61["95% 百分位区间"].tolist()],
            title="表 6-1：Firth 系数 Bootstrap 95% 区间（企业层面聚类，500 次）",
        ),
        use_container_width=True,
    )

    st.subheader("6.2 训练窗口敏感性")
    render_paper_table(rr["table_6_2_training_window_sensitivity"])

    st.subheader("6.2 引入年份固定效应前后的系数对比")
    t63 = rr["table_6_3_year_fixed_effects"]
    render_paper_table(t63)
    df63 = table_from_spec(t63)
    fig63 = grouped_bar(
        categories=df63["变量"].tolist(),
        series={"无年份 FE 系数": df63["无年份 FE 系数"].tolist(),
                "含年份 FE 系数": df63["含年份 FE 系数"].tolist()},
        title="表 6-3：引入年份固定效应前后系数对比（全样本 n=765）",
        y_title="系数", height=440,
    )
    fig63.data[0].marker.color = "#8a857b"
    fig63.data[1].marker.color = "#ff4d00"
    st.plotly_chart(fig63, use_container_width=True)

    st.subheader("6.3 变量数量与样本外表现")
    t64 = rr["table_6_4_variable_count"]
    render_paper_table(t64)
    df64 = table_from_spec(t64).dropna(subset=["测试 AUC"])
    fig64 = line_chart(
        x=df64["变量数"].tolist(),
        series={"训练 AUC": df64["训练 AUC"].tolist(), "测试 AUC": df64["测试 AUC"].tolist()},
        title="表 6-4：变量数量与训练/测试 AUC（测试 AUPR 见上表）",
        x_title="变量数", y_title="AUC", height=420,
    )
    st.plotly_chart(fig64, use_container_width=True)

    st.subheader("6.4 标签严格度的影响")
    t65 = rr["table_6_5_label_severity"]
    render_paper_table(t65)
    ci2 = t65["bootstrap_ci_label2"]
    st.markdown(
        f'<div class="pv-note"><b>标签 2</b>（{t65["label_2"]}）配对 Bootstrap：'
        f'LGB vs ROA AUPR 差 {ci2["lgb_vs_roa_aupr"]["diff"]}，CI {ci2["lgb_vs_roa_aupr"]["ci95"]}；'
        f'Firth vs ROA 差 {ci2["firth_vs_roa_aupr"]["diff"]}，CI {ci2["firth_vs_roa_aupr"]["ci95"]}，'
        '均跨 0，增量在统计上可忽略。</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# 标签 E · 评分卡构建与案例分析（第 7 章）
# ===========================================================================
def _tab_scorecard() -> None:
    rr = load_research_results()
    mp = load_model_parameters()
    rl = load_risk_levels()
    ov = load_research_overview()
    app = ov["scorecard_application"]

    st.subheader("7.1 评分卡载体选择与输出形式")
    st.markdown(
        f'<div class="pv-card"><b>载体：</b>{app["carrier"]}。选择依据：<br/>'
        + "<br/>".join(f"· {r}" for r in app["carrier_rationale"])
        + f'<br/><b>输出三部分：</b>{"、".join(app["output_parts"])}。</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pv-note">Firth AUPR（0.683）低于 ROA（0.762）与 LightGBM（0.785—0.790）；'
        '排序场景直接用 −ROA 更简便。Firth 评分卡的价值在回答"风险来自哪些指标"。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("7.1 风险等级阈值")
    levels_df = pd.DataFrame([
        {"等级": lv["level"], "分值区间": _level_range(lv),
         "训练集分位": lv["train_quantile"], "含义": lv["meaning"]}
        for lv in rl["levels"]
    ])
    st.markdown("**表 7-1 风险等级阈值（训练集 n=551）**", unsafe_allow_html=False)
    st.dataframe(levels_df, use_container_width=True, hide_index=True)
    st.markdown(f'<div class="pv-note">{rl["_meta"]["training_D_level_note"]}</div>',
                unsafe_allow_html=True)

    st.subheader("7.2 评分卡计算流程")
    for i, step in enumerate(mp["scorecard_params"]["computation_steps"], 1):
        st.markdown(f"{step}")

    st.subheader("7.2 评分卡参数")
    params = mp["scorecard_params"]["params"]
    param_df = pd.DataFrame([
        {"指标": k, "缩尾下界 P1": v["winsor_p1"], "缩尾上界 P99": v["winsor_p99"],
         "缩尾后均值": v["mean"], "缩尾后标准差": v["std"], "Firth 系数": v["coef"]}
        for k, v in params.items()
    ])
    param_df.loc[len(param_df)] = {"指标": "截距", "缩尾下界 P1": "—", "缩尾上界 P99": "—",
                                   "缩尾后均值": "—", "缩尾后标准差": "—",
                                   "Firth 系数": mp["scorecard_params"]["intercept"]}
    st.markdown(
        "**表 7-2 评分卡参数（训练集 2014—2022，n=551）** "
        "<span class='pv-paper-badge'>论文实证结果</span>", unsafe_allow_html=True)
    st.dataframe(param_df, use_container_width=True, hide_index=True)
    st.markdown(
        '<div class="pv-note">均值与标准差为缩尾后数值，顺序为先截断后计算。</div>',
        unsafe_allow_html=True,
    )

    st.subheader("7.3 应用场景与使用边界")
    st.markdown(
        f'<div class="pv-card"><b>典型场景：</b>{"、".join(app["scenarios"])}。<br/>'
        f'<b>分级预警实际效果：</b>{app["graded_warning_effect"]}</div>',
        unsafe_allow_html=True,
    )
    for b in app["usage_boundaries"]:
        st.markdown(f'<div class="pv-warn">{b}</div>', unsafe_allow_html=True)

    st.subheader("7.4 海源复材案例（表 7-3，系统内置验证案例）")
    case = rl["validation_case"]
    st.markdown(
        f'<div class="pv-card">案例：{case["company_name"]}（{case["stock_code"]}）'
        f'{case["year"]} 年度，次年归母净利润为负。实时复算见「企业风险评估 → 内置验证案例」'
        f'（论文值 logit={case["expected_logit"]}、score={case["expected_score"]}、'
        f'{case["expected_level"]} 级）。</div>',
        unsafe_allow_html=True,
    )
    case_df = pd.DataFrame([
        {"指标": k, "原始值": case["raw_indicators"][k], "标准化值": case["expected_z"][k],
         "对 logit 的贡献": case["expected_contribution"][k]}
        for k in case["raw_indicators"]
    ])
    case_df.loc[len(case_df)] = {"指标": "截距", "原始值": "—", "标准化值": "—",
                                 "对 logit 的贡献": case["expected_intercept"]}
    st.markdown("**表 7-3 海源复材 2024 年度风险测算**", unsafe_allow_html=False)
    st.dataframe(case_df, use_container_width=True, hide_index=True)
    st.markdown(f'<div class="pv-note">{case["case_note"]}</div>', unsafe_allow_html=True)


def _level_range(lv: dict) -> str:
    lo, hi = lv["score_min"], lv["score_max"]
    if lo is None:
        return f"< {hi}"
    if hi is None:
        return f"> {lo}"
    return f"{lo}—{hi}"
