"""全局主题与样式：动力学排印（深色舞台 + 可变字体动效）。

配色方案（design.md 令牌）：
    - 舞台底 Ink Black #0b0b0c，卡片 Panel #141416
    - 文字 Bone #f4f1eb，次级 Muted Grey #8a857b
    - 唯一强调色 Signal Orange #ff4d00：主 CTA、关键词与 hover
    - 边框 rgba(244,241,235,0.12)，圆角 2px
动效纪律：只动 transform / opacity / font-variation-settings；
入场 expo-out 0.7—0.9s；跑马灯 24s linear 无缝循环并提供暂停；
prefers-reduced-motion 直接终态。风险等级 A—D 为数据语义色，不作品牌强调。
"""
from __future__ import annotations

import html

import streamlit as st

# 设计令牌
INK_BLACK = "#0b0b0c"
BONE = "#f4f1eb"
SIGNAL_ORANGE = "#ff4d00"
PANEL = "#141416"
MUTED_GREY = "#8a857b"
BORDER = "rgba(244,241,235,0.12)"

# 风险等级配色（深色底语义色，_outline 徽章用）
LEVEL_COLORS = {
    "A": "#4ade80",   # 绿 低风险
    "B": "#2dd4bf",   # 青 中低风险
    "C": "#fbbf24",   # 橙 中高风险
    "D": "#f87171",   # 红 高风险
}

# Plotly 深色模板配色
PLOT_ACCENT = SIGNAL_ORANGE
PLOT_BG = PANEL
PLOT_PANEL = PANEL
PLOT_GRID = BORDER
PLOT_TEXT = BONE

# 设计令牌（供页面内联样式统一取用）
TEXT_PRIMARY = BONE        # 主标题/关键数值
TEXT_BODY = "#e6e2da"      # 正文
TEXT_MUTED = MUTED_GREY    # 次要说明

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300..900&display=swap');

:root {
    --ink: #0b0b0c; --bone: #f4f1eb; --orange: #ff4d00;
    --panel: #141416; --muted: #8a857b; --bd: rgba(244,241,235,0.12);
}

/* 舞台与字体 */
html, body, [class*="css"] {
    font-family: 'Inter', 'Helvetica Neue', 'Microsoft YaHei', system-ui, sans-serif;
}
.stApp { background-color: var(--ink); color: var(--bone); }
.block-container { max-width: 1360px; padding: 32px 32px 96px 32px; }

/* 侧边栏：Panel 面 */
section[data-testid="stSidebar"] {
    background-color: var(--panel);
    border-right: 1px solid var(--bd);
}
section[data-testid="stSidebar"] hr { border-color: var(--bd); }
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: var(--bone); font-weight: 500;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] small { color: var(--muted); }

/* 排印层级 */
h1 { color: var(--bone); font-size: 64px; font-weight: 900; line-height: 0.95; letter-spacing: -0.03em; }
h2 { color: var(--bone); font-size: 26px; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
h3 { color: var(--bone); font-size: 18px; font-weight: 700; }
p, li { color: #e6e2da; }
.pv-label {
    font-size: 14px; font-weight: 500; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 12px;
}
.pv-subtitle { color: var(--muted); font-size: 14px; line-height: 1.5; margin-top: 12px; }
.pv-tag {
    display:inline-block; padding:2px 10px; border-radius:2px;
    background:transparent; color:var(--orange); font-size:0.78rem; margin-left:6px;
    border:1px solid rgba(255,77,0,0.5); font-weight:600;
}

/* 主 CTA：信号橙填充、墨黑文字 */
[data-testid="stFormSubmitButton"] button,
div.stDownloadButton button {
    background: var(--orange); color: var(--ink); border: none; border-radius: 2px;
    font-weight: 700; padding: 14px 32px;
    transition: filter 0.4s cubic-bezier(0.22,1,0.36,1), transform 0.4s cubic-bezier(0.22,1,0.36,1);
}
[data-testid="stFormSubmitButton"] button:hover,
div.stDownloadButton button:hover { filter: brightness(1.08); font-weight: 900; }
[data-testid="stFormSubmitButton"] button:active,
div.stDownloadButton button:active { transform: scale(0.98); }
/* 次级按钮：描边骨白，hover 落橙 */
div.stButton > button {
    background: transparent; color: var(--bone);
    border: 1px solid rgba(244,241,235,0.25); border-radius: 2px;
    transition: border-color 0.4s cubic-bezier(0.22,1,0.36,1), color 0.4s cubic-bezier(0.22,1,0.36,1);
}
div.stButton > button:hover { border-color: var(--orange); color: var(--orange); }

/* 输入控件 */
.stTextInput input, .stNumberInput input, .stDateInput input,
div[data-baseweb="select"] > div {
    background-color: var(--panel); color: var(--bone);
    border: 1px solid rgba(244,241,235,0.18); border-radius: 2px;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--orange); outline: none;
}

/* 指标卡（st.metric）：Panel 面、大号骨白数值 */
div[data-testid="stMetric"] {
    background-color: var(--panel);
    border: 1px solid var(--bd);
    border-radius: 2px;
    padding: 24px;
}
div[data-testid="stMetricValue"] {
    color: var(--bone); font-size: 40px; font-weight: 700; letter-spacing: -0.03em;
}
div[data-testid="stMetricLabel"] { color: var(--muted); font-size: 14px; letter-spacing: 0.06em; }
div[data-testid="stMetricDelta"] { color: var(--muted); }

/* 通用卡片：Panel 面、2px 圆角、Panel 投影 */
.pv-card {
    background-color: var(--panel); border: 1px solid var(--bd); border-radius: 2px;
    padding: 24px; margin-bottom: 16px; color: #e6e2da;
    box-shadow: 0 24px 60px rgba(0,0,0,0.60);
}
.pv-card b { color: var(--bone); }

/* 说明 / 提示块 */
.pv-note {
    background-color: transparent; border: 1px solid var(--bd);
    border-left: 2px solid rgba(244,241,235,0.45); padding: 12px 16px;
    color: #cfcbc2; font-size: 0.86rem; border-radius: 2px; margin: 8px 0; line-height: 1.6;
}
.pv-warn {
    background-color: transparent; border: 1px solid var(--bd);
    border-left: 2px solid #fbbf24; padding: 12px 16px;
    color: #d9a441; font-size: 0.86rem; border-radius: 2px; margin: 8px 0; line-height: 1.6;
}
.pv-paper-badge {
    display:inline-block; padding:1px 8px; border-radius:2px; font-size:0.72rem;
    background:transparent; color:var(--orange);
    border:1px solid rgba(255,77,0,0.5); margin-left:6px; font-weight:600;
}

/* 风险等级徽章：描边语义色 */
.pv-level-badge {
    display:inline-block; padding:6px 18px; border-radius:2px; font-size:1.4rem;
    font-weight:700; background:transparent; border:1px solid currentColor;
}

/* 表格与分隔线 */
.stDataFrame { border: 1px solid var(--bd); border-radius: 2px; }
hr { border-color: var(--bd); }

/* 选项卡：选中骨白、下划线信号橙 */
.stTabs [data-baseweb="tab"] { color: var(--muted); font-weight: 500; }
.stTabs [aria-selected="true"] { color: var(--bone); }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--orange); }

/* ---------------- 动力学排印动效 ---------------- */
/* 逐字入场：遮罩上升，35ms 间隔，单字 0.8s expo-out */
.pv-stagger { overflow: hidden; }
.pv-stagger .ch {
    display: inline-block; transform: translateY(110%); opacity: 0;
    animation: pv-rise 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    animation-delay: var(--d);
}
@keyframes pv-rise { to { transform: translateY(0); opacity: 1; } }

/* 字重呼吸：2.4s 循环，仅 transform/opacity/font-variation-settings 纪律内 */
.pv-breath { animation: pv-breath 2.4s ease-in-out infinite; }
@keyframes pv-breath {
    0%, 100% { font-variation-settings: 'wght' 300; }
    50%      { font-variation-settings: 'wght' 900; }
}

/* 跑马灯：24s linear 无缝循环，hover 暂停，.off 停止 */
.pv-marquee { overflow: hidden; border-top: 1px solid var(--bd); border-bottom: 1px solid var(--bd); padding: 12px 0; margin: 24px 0; }
.pv-marquee-track {
    display: inline-flex; gap: 64px; white-space: nowrap; will-change: transform;
    animation: pv-marquee 24s linear infinite;
}
.pv-marquee:hover .pv-marquee-track { animation-play-state: paused; }
.pv-marquee.off .pv-marquee-track { animation: none; transform: none; }
@keyframes pv-marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.pv-marquee-item { color: var(--muted); font-size: 14px; letter-spacing: 0.12em; }
.pv-marquee-item b { color: var(--bone); font-weight: 700; margin-left: 8px; }

/* 减少动态效果：直接终态 */
@media (prefers-reduced-motion: reduce) {
    .pv-stagger .ch, .pv-breath, .pv-marquee-track {
        animation: none !important; transform: none !important; opacity: 1 !important;
    }
}

/* ---------------- 交互层：滚动条 / 选中 / 焦点 / hover / 滚动揭示 ---------------- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--ink); }
::-webkit-scrollbar-thumb { background: #2a2a2e; border-radius: 5px; border: 2px solid var(--ink); }
::-webkit-scrollbar-thumb:hover { background: var(--orange); }
* { scrollbar-width: thin; scrollbar-color: #2a2a2e var(--ink); }
::selection { background: var(--orange); color: var(--ink); }
:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }

/* hover 微反馈：卡片浮起 + 描边落橙 */
.pv-card, div[data-testid="stMetric"] {
    transition: transform 0.4s cubic-bezier(0.22,1,0.36,1), border-color 0.4s cubic-bezier(0.22,1,0.36,1);
}
.pv-card:hover, div[data-testid="stMetric"]:hover {
    transform: translateY(-2px); border-color: rgba(255,77,0,0.45);
}
section[data-testid="stSidebar"] .stRadio label {
    transition: transform 0.3s cubic-bezier(0.22,1,0.36,1), color 0.3s;
}
section[data-testid="stSidebar"] .stRadio label:hover { transform: translateX(4px); color: var(--orange); }
.stTabs [data-baseweb="tab"] { transition: color 0.3s; }
.stTabs [data-baseweb="tab"]:hover { color: var(--bone); }
.stTabs [data-baseweb="tab-highlight"] { transition: all 0.4s cubic-bezier(0.22,1,0.36,1); }

/* 滚动驱动揭示（Chrome 115+；不支持时回退为入场一次性动画） */
@supports (animation-timeline: view()) {
    .pv-card, .pv-note, .pv-warn, div[data-testid="stMetric"], .stDataFrame {
        animation: pv-reveal linear both;
        animation-timeline: view();
        animation-range: entry 0% entry 55%;
    }
    @keyframes pv-reveal {
        from { opacity: 0; transform: translateY(28px); }
        to   { opacity: 1; transform: translateY(0); }
    }
}
</style>
"""

# 关闭动效时追加的覆盖样式（跑马灯暂停开关 / 入场与呼吸停止）
MOTION_OFF_CSS = """
<style>
.pv-stagger .ch { animation: none; transform: none; opacity: 1; }
.pv-breath { animation: none; }
.pv-marquee-track { animation: none; transform: none; }
.pv-card, .pv-note, .pv-warn, div[data-testid="stMetric"], .stDataFrame {
    animation: none !important; opacity: 1 !important; transform: none !important;
}
.pv-card:hover, div[data-testid="stMetric"]:hover { transform: none; }
</style>
"""


def inject_css(motion: bool = True) -> None:
    """注入全局样式（幂等）。motion=False 时停止全部动效。"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    if not motion:
        st.markdown(MOTION_OFF_CSS, unsafe_allow_html=True)


def stagger_html(text: str, tag: str = "h1", step_ms: int = 35) -> str:
    """标题逐字入场 HTML：每字符一个 span，间隔 step_ms 毫秒遮罩上升。"""
    spans = []
    for i, ch in enumerate(text):
        if ch == " ":
            spans.append('<span class="ch" style="--d:%dms;">&nbsp;</span>' % (i * step_ms))
        else:
            spans.append(
                '<span class="ch" style="--d:%dms;">%s</span>'
                % (i * step_ms, html.escape(ch))
            )
    return f'<{tag} class="pv-stagger" style="margin-bottom:2px;">{"".join(spans)}</{tag}>'


def marquee_html(items: list, off: bool = False) -> str:
    """跑马灯 HTML：内容复制两份实现 24s 无缝循环。items: [(标签, 值), ...]。"""
    def _run() -> str:
        return "".join(
            f'<span class="pv-marquee-item">{html.escape(k)}<b>{html.escape(str(v))}</b></span>'
            for k, v in items
        )
    state = "pv-marquee off" if off else "pv-marquee"
    return f'<div class="{state}"><div class="pv-marquee-track">{_run()}{_run()}</div></div>'


def paper_badge(text: str = "论文实证结果") -> str:
    """返回'论文实证结果'标注徽章 HTML。"""
    return f'<span class="pv-paper-badge">{text}</span>'


def level_badge_html(level: str, meaning: str = "") -> str:
    """风险等级徽章 HTML（描边语义色）。"""
    color = LEVEL_COLORS.get(level, SIGNAL_ORANGE)
    label = f"{level}" + (f" · {meaning}" if meaning else "")
    return f'<span class="pv-level-badge" style="color:{color}">{label}</span>'
