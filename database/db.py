"""SQLite 连接与初始化。

数据库目录选择优先级：
    1. 环境变量 PV_RISK_DB_DIR 指定的目录（便于 VPS/容器持久化挂载）；
    2. 项目内 data/ 目录（本地开发默认）；
    3. 若上述目录不可写（如云端只读/临时文件系统），自动回退到系统临时目录，
       保证应用在 Streamlit Community Cloud 等平台仍可运行（数据为会话级，重启即清空）。
首次运行时按 schema.sql 建表。
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from core.config_loader import ROOT_DIR

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _resolve_db_dir() -> Path:
    """确定一个可写的数据库目录（见模块 docstring 的优先级）。"""
    env = os.environ.get("PV_RISK_DB_DIR")
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p

    local = ROOT_DIR / "data"
    try:
        local.mkdir(parents=True, exist_ok=True)
        probe = local / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return local
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "pv_risk" / "data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DB_DIR = _resolve_db_dir()
DB_PATH = DB_DIR / "pv_risk.db"


def get_connection() -> sqlite3.Connection:
    """返回一个 row_factory=sqlite3.Row 的连接。"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """按 schema.sql 初始化数据库（幂等）。"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(sql)
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"数据库已初始化：{DB_PATH}")
