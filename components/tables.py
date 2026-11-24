"""表格组件：统一渲染论文表格（columns + rows 结构）为 DataFrame。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


def table_from_spec(spec: Dict[str, Any], index_col: Optional[str] = None) -> pd.DataFrame:
    """将 {title, columns, rows} 结构的论文表格转为 DataFrame。"""
    columns = spec.get("columns", [])
    rows = spec.get("rows", [])
    df = pd.DataFrame(rows, columns=columns)
    if index_col and index_col in df.columns:
        df = df.set_index(index_col)
    return df


def render_paper_table(
    spec: Dict[str, Any],
    show_title: bool = True,
    paper_badge: bool = True,
    index_col: Optional[str] = None,
    height: Optional[int] = None,
) -> pd.DataFrame:
    """渲染论文表格：标题 + 论文实证结果徽章 + DataFrame。"""
    df = table_from_spec(spec, index_col=index_col)
    if show_title:
        title = spec.get("title", "")
        badge = '<span class="pv-paper-badge">论文实证结果</span>' if paper_badge else ""
        st.markdown(f"**{title}** {badge}", unsafe_allow_html=True)
    if height is None:
        st.dataframe(df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True, height=height)
    notes = spec.get("notes")
    if notes:
        st.markdown(f'<div class="pv-note">{notes}</div>', unsafe_allow_html=True)
    return df


def render_dataframe(df: pd.DataFrame, **kwargs) -> None:
    """渲染任意 DataFrame。"""
    st.dataframe(df, use_container_width=True, **kwargs)
