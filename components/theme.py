"""全局主题与样式：浅色高级风（高对比、简洁、清晰）。

配色方案：
    - 主内容区：白 / 浅冷灰底，深墨蓝正文（高对比，文字清晰）
    - 侧边栏：浅色，与主区统一，保证导航文字高对比
    - 强调色：精致蓝 #2563eb
    - 风险等级：绿(A) / 青(B) / 橙(C) / 红(D)
统一注入 CSS，供各页面复用。避免渐变、霓虹、3D、粒子动画等装饰。
"""
from __future__ import annotations

import streamlit as st

# 风险等级配色（浅色底下仍保证徽章白字可读）
LEVEL_COLORS = {
    "A": "#16a34a",   # 绿 低风险
    "B": "#0d9488",   # 青 中低风险
    "C": "#d97706",   # 橙 中高风险
    "D": "#dc2626",   # 红 高风险
}

# Plotly 浅色模板配色
PLOT_ACCENT = "#2563eb"
PLOT_BG = "#ffffff"
PLOT_PANEL = "#ffffff"
PLOT_GRID = "#e6ebf2"
PLOT_TEXT = "#334155"

# 设计令牌（供页面内联样式统一取用）
TEXT_PRIMARY = "#0f172a"   # 深墨蓝，主标题/关键数值
TEXT_BODY = "#334155"      # 正文
TEXT_MUTED = "#64748b"     # 次要说明

GLOBAL_CSS = """
<style>
/* 基础字体与主区底色 */
html, body, [class*="css"] { font-family: "Segoe UI", "Microsoft YaHei", -apple-system, sans-serif; }
.stApp { background-color: #f6f8fb; color: #0f172a; }

/* 侧边栏：浅色，与主区统一，保证文字高对比 */
section[data-testid="stSidebar"] {
    background-color: #fbfcfe;
    border-right: 1px solid #e6ebf2;
}
section[data-testid="stSidebar"] hr { border-color: #e6ebf2; }
/* 侧栏导航单选按钮与说明文字：深色高对比，保证清晰可读 */
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p { color: #0f172a; font-weight: 500; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] small { color: #64748b; }

/* 标题层次：深色高对比 */
h1, h2, h3 { color: #0f172a; font-weight: 650; letter-spacing: -0.01em; }
.pv-subtitle { color: #64748b; font-size: 0.95rem; margin-bottom: 0.5rem; }
.pv-tag {
    display:inline-block; padding:2px 10px; border-radius:5px;
    background:#eff4ff; color:#2563eb; font-size:0.78rem; margin-left:6px;
    border:1px solid #d6e2ff; font-weight:600;
}

/* 指标卡（st.metric）：白底、细边、深色数值 */
div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e6ebf2;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
div[data-testid="stMetricValue"] { color: #0f172a; font-size: 1.5rem; font-weight: 650; }
div[data-testid="stMetricLabel"] { color: #64748b; }

/* 通用卡片：白底、细边、轻阴影 */
.pv-card {
    background-color:#ffffff; border:1px solid #e6ebf2; border-radius:10px;
    padding:16px 18px; margin-bottom:12px; color:#334155;
    box-shadow:0 1px 2px rgba(15,23,42,0.04);
}
.pv-card b { color:#0f172a; }

/* 说明 / 提示块 */
.pv-note {
    background-color:#f1f5fb; border-left:3px solid #2563eb; padding:10px 14px;
    color:#475569; font-size:0.86rem; border-radius:6px; margin:8px 0; line-height:1.6;
}
.pv-warn {
    background-color:#fff7ed; border-left:3px solid #d97706; padding:10px 14px;
    color:#92610e; font-size:0.86rem; border-radius:6px; margin:8px 0; line-height:1.6;
}
.pv-paper-badge {
    display:inline-block; padding:1px 8px; border-radius:4px; font-size:0.72rem;
    background:#fef6e7; color:#a16207; border:1px solid #f0d9a8; margin-left:6px; font-weight:600;
}

/* 风险等级徽章 */
.pv-level-badge {
    display:inline-block; padding:6px 18px; border-radius:8px; font-size:1.4rem;
    font-weight:700; color:#ffffff;
}

/* 表格与分隔线 */
.stDataFrame { border:1px solid #e6ebf2; border-radius:8px; }
hr { border-color:#e6ebf2; }

/* 选项卡 / 单选按钮文字更清晰 */
.stTabs [data-baseweb="tab"] { color:#475569; font-weight:600; }
.stTabs [aria-selected="true"] { color:#2563eb; }
</style>
"""


def inject_css() -> None:
    """注入全局样式（幂等）。"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def paper_badge(text: str = "论文实证结果") -> str:
    """返回'论文实证结果'标注徽章 HTML。"""
    return f'<span class="pv-paper-badge">{text}</span>'


def level_badge_html(level: str, meaning: str = "") -> str:
    """风险等级徽章 HTML。"""
    color = LEVEL_COLORS.get(level, "#2563eb")
    label = f"{level}" + (f" · {meaning}" if meaning else "")
    return f'<span class="pv-level-badge" style="background-color:{color}">{label}</span>'
