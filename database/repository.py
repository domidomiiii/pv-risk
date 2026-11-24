"""评估记录的数据访问层（Repository）。

提供保存、查询、删除企业风险评估历史记录的操作。
所有 JSON 字段以字符串形式存储，读取时反序列化。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.db import get_connection, init_db

# 需要以 JSON 存储的字段
_JSON_FIELDS = [
    "raw_inputs", "indicators", "winsorized", "z_scores",
    "contributions", "top_risk_sources", "validation_notes",
]


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _loads(text: Optional[str]) -> Any:
    if text is None or text == "":
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def save_assessment(record: Dict[str, Any]) -> int:
    """保存一条评估记录，返回自增 id。"""
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO assessments (
                company_name, stock_code, fiscal_year, created_at,
                raw_inputs, indicators, winsorized, z_scores, contributions,
                logit, score, risk_level, level_meaning, top_risk_sources,
                validation_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("company_name", "未命名"),
                record.get("stock_code"),
                int(record.get("fiscal_year", 0)),
                now,
                _dumps(record.get("raw_inputs")),
                _dumps(record.get("indicators")),
                _dumps(record.get("winsorized")),
                _dumps(record.get("z_scores")),
                _dumps(record.get("contributions")),
                record.get("logit"),
                record.get("score"),
                record.get("risk_level"),
                record.get("level_meaning"),
                _dumps(record.get("top_risk_sources")),
                _dumps(record.get("validation_notes")),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def _row_to_dict(row) -> Dict[str, Any]:
    d = dict(row)
    for f in _JSON_FIELDS:
        if f in d:
            d[f] = _loads(d[f])
    return d


def list_assessments(limit: int = 200) -> List[Dict[str, Any]]:
    """按创建时间倒序列出评估记录。"""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM assessments ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_assessment(record_id: int) -> Optional[Dict[str, Any]]:
    """按 id 获取单条记录。"""
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM assessments WHERE id = ?", (record_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_assessment(record_id: int) -> None:
    """删除单条记录。"""
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM assessments WHERE id = ?", (record_id,))
        conn.commit()


def count_assessments() -> int:
    """记录总数。"""
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM assessments").fetchone()
    return int(row["c"]) if row else 0
