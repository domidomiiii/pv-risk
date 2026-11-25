"""Plotly 交互式图表组件。

统一金融终端深色风格。所有图表仅使用论文已公布的汇总数值绘制，
不伪造逐观测数据；图 5-1（ROC/PR）、图 5-2（SHAP 分布）、图 5-3（SHAP 依赖）
因论文未提供逐点数据，改以表格/文字呈现，不在此绘制曲线。
"""
from __future__ import annotations

from typing import Dict, List, Optional

import plotly.graph_objects as go

from components.theme import PLOT_ACCENT, PLOT_BG, PLOT_GRID, PLOT_PANEL, PLOT_TEXT

# 模型对比配色（深色舞台：信号橙 + 骨白/灰阶 + 少量数据色）
MODEL_COLORS = {
    "Altman Z''": "#6b665c",
    "单变量基准（−ROA）": "#f4f1eb",
    "Firth Logit": "#ff4d00",
    "LightGBM（未加权）": "#ffb020",
    "LightGBM（类别加权）": "#5eead4",
    "LightGBM（正例加权）": "#c084fc",
    "LightGBM（SMOTE）": "#8a857b",
}


def _base_layout(title: str, height: int = 420) -> go.Layout:
    return go.Layout(
        title=dict(text=title, font=dict(size=15, color=PLOT_TEXT)),
        paper_bgcolor=PLOT_PANEL,
        plot_bgcolor=PLOT_BG,
        font=dict(color=PLOT_TEXT, size=12),
        height=height,
        margin=dict(l=50, r=24, t=54, b=44),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(gridcolor=PLOT_GRID, zerolinecolor=PLOT_GRID),
        yaxis=dict(gridcolor=PLOT_GRID, zerolinecolor=PLOT_GRID),
    )


def grouped_bar(
    categories: List[str],
    series: Dict[str, List[float]],
    title: str,
    y_title: str = "",
    height: int = 420,
    color_map: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """分组柱状图。series: {系列名: [各分类值]}。"""
    fig = go.Figure()
    for name, values in series.items():
        color = (color_map or {}).get(name, PLOT_ACCENT)
        fig.add_trace(go.Bar(name=name, x=categories, y=values, marker_color=color))
    fig.update_layout(_base_layout(title, height))
    fig.update_layout(barmode="group", yaxis_title=y_title)
    return fig


def single_bar(
    categories: List[str],
    values: List[float],
    title: str,
    y_title: str = "",
    color: str = PLOT_ACCENT,
    height: int = 420,
    text: Optional[List[str]] = None,
) -> go.Figure:
    """单系列柱状图。"""
    fig = go.Figure(go.Bar(
        x=categories, y=values, marker_color=color,
        text=text, textposition="outside",
    ))
    fig.update_layout(_base_layout(title, height))
    fig.update_layout(yaxis_title=y_title, showlegend=False)
    return fig


def line_chart(
    x: List,
    series: Dict[str, List[float]],
    title: str,
    x_title: str = "",
    y_title: str = "",
    height: int = 420,
    color_map: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """多系列折线图。"""
    fig = go.Figure()
    default_colors = [PLOT_ACCENT, "#f4f1eb", "#8a857b", "#ffb020", "#5eead4"]
    for i, (name, values) in enumerate(series.items()):
        color = (color_map or {}).get(name, default_colors[i % len(default_colors)])
        fig.add_trace(go.Scatter(
            x=x, y=values, mode="lines+markers", name=name,
            line=dict(color=color, width=2), marker=dict(size=7),
        ))
    fig.update_layout(_base_layout(title, height))
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    return fig


def bar_line_combo(
    categories: List[str],
    bars: List[float],
    line: List[float],
    title: str,
    bar_name: str = "观测数",
    line_name: str = "亏损率",
    bar_color: str = PLOT_ACCENT,
    line_color: str = "#f4f1eb",
    height: int = 420,
) -> go.Figure:
    """柱线组合图（左轴柱状、右轴折线，如各年观测数与亏损率）。"""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories, y=bars, name=bar_name, marker_color=bar_color))
    fig.add_trace(go.Scatter(
        x=categories, y=line, name=line_name, mode="lines+markers",
        line=dict(color=line_color, width=2), yaxis="y2",
    ))
    layout = _base_layout(title, height)
    fig.update_layout(layout)
    fig.update_layout(
        yaxis=dict(title=bar_name, gridcolor=PLOT_GRID),
        yaxis2=dict(title=line_name, overlaying="y", side="right",
                    gridcolor="rgba(0,0,0,0)", tickformat=".0%"),
    )
    return fig


def errorbar_range(
    categories: List[str],
    centers: List[float],
    lows: List[float],
    highs: List[float],
    title: str,
    height: int = 420,
) -> go.Figure:
    """区间图（用于 Bootstrap 95% 置信区间），含 0 参考线。"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=categories + categories[::-1],
        y=highs + lows[::-1],
        fill="toself", fillcolor="rgba(255,77,0,0.18)",
        line=dict(color="rgba(0,0,0,0)"), name="95% 区间",
    ))
    fig.add_trace(go.Scatter(
        x=categories, y=centers, mode="markers", name="原样本系数",
        marker=dict(color=PLOT_ACCENT, size=8),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="#8a857b")
    fig.update_layout(_base_layout(title, height))
    fig.update_layout(yaxis_title="系数值")
    return fig
