"""输入数据校验：缺失值、分母为零、异常值检查。

论文要求：分母为零、缺失值、异常值必须进行提示，不能静默生成错误评分。
本模块在指标计算前后进行校验，返回结构化的问题清单供页面提示。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.config_loader import load_indicators

# 原始报表字段（来自 indicator_definitions.json 的 raw_input_fields）
RAW_FIELDS: List[Dict[str, str]] = load_indicators()["raw_input_fields"]
RAW_FIELD_NAMES: List[str] = [f["field"] for f in RAW_FIELDS]
FIELD_LABELS: Dict[str, str] = {f["field"]: f["name_cn"] for f in RAW_FIELDS}

# growth 依赖 revenue_prev；若缺失则 growth 无法计算
REQUIRED_FOR_GROWTH = "revenue_prev"


@dataclass
class ValidationIssue:
    """单条校验问题。"""

    level: str  # "error" | "warning"
    field: str
    message: str


@dataclass
class ValidationResult:
    """校验结果集合。"""

    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        """无 error 即认为可继续计算（warning 仅提示）。"""
        return len(self.errors) == 0

    def add(self, level: str, fld: str, message: str) -> None:
        self.issues.append(ValidationIssue(level=level, field=fld, message=message))


def _to_float(value: Any) -> Optional[float]:
    """尝试将输入转换为 float；无法转换（含空、None、非数字串）返回 None。"""
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip().replace(",", "")
        if v == "" or v.lower() in {"nan", "none", "null"}:
            return None
        try:
            return float(v)
        except ValueError:
            return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    # NaN / inf 视为无效
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def validate_raw_inputs(raw: Dict[str, Any]) -> tuple[Dict[str, Optional[float]], ValidationResult]:
    """校验原始报表输入。

    返回：(清洗后的数值字典, 校验结果)。
    - 缺失字段记为 error。
    - revenue_prev 缺失记为 warning（仅影响 growth）。
    """
    result = ValidationResult()
    cleaned: Dict[str, Optional[float]] = {}

    for fld in RAW_FIELD_NAMES:
        val = _to_float(raw.get(fld))
        cleaned[fld] = val
        label = FIELD_LABELS[fld]
        if val is None:
            if fld == REQUIRED_FOR_GROWTH:
                result.add(
                    "warning",
                    fld,
                    f"「{label}」缺失：营收增速 growth 无法计算，其余指标不受影响。",
                )
            else:
                result.add("error", fld, f"「{label}」缺失或非法，无法完成评分。")

    return cleaned, result


def check_denominators(cleaned: Dict[str, Optional[float]]) -> ValidationResult:
    """检查各指标分母是否为零或接近零（会导致比值失真）。"""
    result = ValidationResult()
    indicators = load_indicators()["indicators"]
    for ind in indicators:
        denom_field = ind.get("zero_denominator_field")
        if not denom_field:
            continue
        denom = cleaned.get(denom_field)
        if denom is None:
            continue  # 缺失已在 validate_raw_inputs 记录
        if abs(denom) < 1e-12:
            result.add(
                "error",
                denom_field,
                f"指标 {ind['variable']} 的分母「{FIELD_LABELS.get(denom_field, denom_field)}」为零，无法计算。",
            )
    return result


def check_indicator_anomalies(indicator_values: Dict[str, Optional[float]]) -> ValidationResult:
    """对已计算指标做异常提示（warning，不阻断）。

    例如资产负债率超过 1（资不抵债）、流动比率为负等，论文说明此类极端值
    来自资不抵债或业务重整企业，属真实现象，缩尾后压至分位点，故仅作提示。
    """
    result = ValidationResult()
    lev = indicator_values.get("lev")
    if lev is not None and lev > 1.0:
        result.add(
            "warning",
            "lev",
            f"资产负债率 {lev:.3f} 超过 100%（资不抵债），属论文所述真实极端值，缩尾后将压至 P99 边界。",
        )
    cr = indicator_values.get("cr")
    if cr is not None and cr < 0:
        result.add("warning", "cr", f"流动比率为负（{cr:.3f}），请核对流动资产/流动负债科目。")
    return result


def merge_results(*results: ValidationResult) -> ValidationResult:
    """合并多个校验结果。"""
    merged = ValidationResult()
    for r in results:
        merged.issues.extend(r.issues)
    return merged
