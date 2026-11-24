"""左侧固定导航栏：最多四个一级菜单。"""
from __future__ import annotations

import streamlit as st

# 四个一级菜单（键 -> 显示名）
MENU = {
    "dashboard": "首页 · 研究概览",
    "assessment": "企业风险评估",
    "empirical": "实证研究",
    "data": "数据管理",
}


def render_sidebar() -> str:
    """渲染侧栏导航，返回当前选中的页面键。"""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:6px 0 14px 0;">
              <div style="font-size:1.35rem;font-weight:700;color:#0f172a;letter-spacing:1px;">
                PV-Risk
              </div>
              <div style="color:#64748b;font-size:0.8rem;margin-top:2px;">
                光伏上市公司财务风险预警<br/>与实证分析系统
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        selection = st.radio(
            "导航",
            options=list(MENU.keys()),
            format_func=lambda k: MENU[k],
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(
            """
            <div class="pv-note" style="font-size:0.76rem;">
            评分卡载体：Firth Logit<br/>
            阈值口径：论文表 7-1（训练集 n=551）<br/>
            输出为 0—100 相对风险评分，未经概率校准。
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("数据来源：论文《光伏上市公司财务困境预警研究与应用》")

    return selection
