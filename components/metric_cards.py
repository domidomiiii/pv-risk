"""指标卡片组件：关键数字展示。"""
from __future__ import annotations

from typing import List

import streamlit as st


def render_metric_row(items: List[dict], cols_per_row: int = 3) -> None:
    """按每行 cols_per_row 个渲染 st.metric 卡片。

    items 元素支持键：label / value / unit / delta（可选）。
    """
    for start in range(0, len(items), cols_per_row):
        chunk = items[start:start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, chunk):
            value = item.get("value")
            unit = item.get("unit", "")
            display = f"{value}{(' ' + unit) if unit else ''}"
            with col:
                st.metric(label=item.get("label", ""), value=display,
                          delta=item.get("delta"))


def render_level_card(level: str, meaning: str, score: float) -> None:
    """大号风险等级 + 评分卡片。"""
    from components.theme import LEVEL_COLORS
    color = LEVEL_COLORS.get(level, "#3b82f6")
    st.markdown(
        f"""
        <div class="pv-card" style="text-align:center;">
          <div style="color:#64748b;font-size:0.85rem;">风险等级</div>
          <div class="pv-level-badge" style="background-color:{color};margin:8px 0;">
            {level} · {meaning}
          </div>
          <div style="color:#64748b;font-size:0.85rem;margin-top:10px;">风险评分（0—100 相对值）</div>
          <div style="font-size:2.2rem;font-weight:700;color:#0f172a;">{score:.1f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
