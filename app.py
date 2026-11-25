"""PV-Risk 主入口。

光伏上市公司财务风险预警与实证分析系统。
运行： streamlit run app.py

结构：左侧固定导航栏（四个一级菜单）+ 主区域页面。
所有评分计算真实运行；论文实证结果以已公布数据静态/交互展示并标注。
"""
from __future__ import annotations

import os
import sys

# 保证以任意工作目录启动都能导入项目内包
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st

from components.sidebar import render_sidebar
from components.theme import inject_css
from database.db import init_db
from views import company_assessment, dashboard, data_management, empirical_analysis

# 页面配置
st.set_page_config(
    page_title="PV-Risk · 光伏上市公司财务风险预警系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 数据库初始化 → 侧栏（含动效开关）→ 按开关注入全局样式
init_db()
selection = render_sidebar()
inject_css(motion=st.session_state.get("pv_motion", True))

if selection == "dashboard":
    dashboard.render()
elif selection == "assessment":
    company_assessment.render()
elif selection == "empirical":
    empirical_analysis.render()
elif selection == "data":
    data_management.render()
