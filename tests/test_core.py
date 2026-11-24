"""核心算法单元测试。

重点验证：
1. 八项指标计算遵循论文表 3-1 口径。
2. 缩尾 + 标准化遵循表 7-2 参数与"先缩尾后标准化"顺序。
3. Firth 评分复算论文表 7-3 海源复材案例（logit=1.616, score=83.4, D 级）。
4. 风险等级严格按表 7-1 阈值。
5. 风险来源分解取正向贡献最大三项。
6. 缺失值 / 分母为零校验。

运行： python -m pytest tests/ -v   或   python tests/test_core.py
"""
from __future__ import annotations

import math
import os
import sys

# 保证可从项目根导入 core 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import indicator_calculator as ic
from core import validation as val
from core.firth_scoring import classify_level, score_indicators, sigmoid_score
from core.config_loader import load_risk_levels
from core.risk_attribution import rank_risk_sources


def _approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# 1. 指标计算
# ---------------------------------------------------------------------------
def test_indicator_formulas():
    cleaned = {
        "total_assets": 100.0,
        "total_liabilities": 66.6,
        "current_assets": 55.9,
        "current_liabilities": 100.0,
        "net_profit_attr": -18.4,
        "revenue": 50.0,
        "revenue_prev": 79.24,   # 使 growth = 50/79.24 - 1 ≈ -0.369
        "net_operating_cashflow": -7.7,
        "construction_in_progress": 35.5,
        "fixed_assets_net": 100.0,
        "retained_earnings": -135.1,
    }
    ind = ic.compute_indicators(cleaned)
    assert _approx(ind["lev"], 0.666), ind["lev"]
    assert _approx(ind["cr"], 0.559), ind["cr"]
    assert _approx(ind["roa"], -0.184), ind["roa"]
    assert _approx(ind["cip_fa"], 0.355), ind["cip_fa"]
    assert _approx(ind["reta"], -1.351), ind["reta"]
    assert _approx(ind["asset_turn"], 0.5), ind["asset_turn"]
    assert _approx(ind["growth"], -0.369, tol=1e-3), ind["growth"]
    print("[PASS] test_indicator_formulas")


def test_zero_denominator_returns_none():
    cleaned = {"total_assets": 0.0, "total_liabilities": 10.0, "revenue": 5.0,
               "net_profit_attr": 1.0, "current_assets": 1.0, "current_liabilities": 0.0,
               "net_operating_cashflow": 1.0, "construction_in_progress": 1.0,
               "fixed_assets_net": 1.0, "retained_earnings": 1.0, "revenue_prev": 4.0}
    ind = ic.compute_indicators(cleaned)
    assert ind["lev"] is None       # total_assets=0
    assert ind["cr"] is None        # current_liabilities=0
    print("[PASS] test_zero_denominator_returns_none")


# ---------------------------------------------------------------------------
# 2. 缩尾 + 标准化
# ---------------------------------------------------------------------------
def test_winsorize_before_standardize():
    """reta 原始 -1.351 低于 P1=-1.1103，应先缩尾再标准化，z≈-4.57。"""
    from core.preprocessing import preprocess_indicator
    pr = preprocess_indicator("reta", -1.351)
    assert pr.clipped_low is True
    assert _approx(pr.winsorized, -1.1103), pr.winsorized
    assert _approx(pr.z, -4.57, tol=0.01), pr.z
    print("[PASS] test_winsorize_before_standardize")


# ---------------------------------------------------------------------------
# 3. 海源复材案例复算（论文表 7-3）
# ---------------------------------------------------------------------------
def test_haiyuan_case_reproduction():
    case = load_risk_levels()["validation_case"]
    raw = case["raw_indicators"]
    result = score_indicators(raw)

    # 逐项 z 值校验
    for var, exp_z in case["expected_z"].items():
        got = result.preprocess[var].z
        assert _approx(got, exp_z, tol=0.02), f"{var}: z={got} 期望≈{exp_z}"

    # 逐项贡献校验
    for var, exp_c in case["expected_contribution"].items():
        got = result.contributions[var]
        assert _approx(got, exp_c, tol=0.01), f"{var}: 贡献={got} 期望≈{exp_c}"

    # logit / score / 等级
    assert _approx(result.logit, case["expected_logit"], tol=0.01), result.logit
    assert _approx(result.score, case["expected_score"], tol=0.15), result.score
    assert result.level == case["expected_level"], result.level

    # Top 风险来源
    top = rank_risk_sources(result.contributions, top_n=3)
    top_vars = [t.variable for t in top]
    assert top_vars == case["expected_top_risk_sources"], top_vars
    print(f"[PASS] test_haiyuan_case_reproduction  logit={result.logit:.3f} "
          f"score={result.score:.2f} level={result.level} top={top_vars}")


# ---------------------------------------------------------------------------
# 4. 风险等级阈值（表 7-1）
# ---------------------------------------------------------------------------
def test_risk_level_thresholds():
    assert classify_level(5.0)[0] == "A"
    assert classify_level(11.51)[0] == "A"
    assert classify_level(11.52)[0] == "B"
    assert classify_level(20.02)[0] == "B"
    assert classify_level(20.03)[0] == "C"
    assert classify_level(33.24)[0] == "C"
    assert classify_level(33.25)[0] == "D"
    assert classify_level(90.0)[0] == "D"
    print("[PASS] test_risk_level_thresholds")


def test_sigmoid_score():
    assert _approx(sigmoid_score(0.0), 50.0), sigmoid_score(0.0)
    assert _approx(sigmoid_score(1.616), 83.43, tol=0.05)
    print("[PASS] test_sigmoid_score")


# ---------------------------------------------------------------------------
# 5. 校验
# ---------------------------------------------------------------------------
def test_validation_missing_and_warning():
    raw = {"total_assets": 100.0}  # 大量缺失
    cleaned, res = val.validate_raw_inputs(raw)
    assert not res.ok                       # 有 error
    assert len(res.errors) > 0
    # revenue_prev 缺失应为 warning 而非 error
    raw2 = {f: 1.0 for f in val.RAW_FIELD_NAMES}
    raw2["revenue_prev"] = None
    _, res2 = val.validate_raw_inputs(raw2)
    assert res2.ok                          # 无 error
    assert any(w.field == "revenue_prev" for w in res2.warnings)
    print("[PASS] test_validation_missing_and_warning")


def test_missing_indicator_flagged_in_scoring():
    raw = dict(load_risk_levels()["validation_case"]["raw_indicators"])
    raw["growth"] = None
    result = score_indicators(raw)
    assert "growth" in result.missing_variables
    print("[PASS] test_missing_indicator_flagged_in_scoring")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_indicator_formulas,
        test_zero_denominator_returns_none,
        test_winsorize_before_standardize,
        test_haiyuan_case_reproduction,
        test_risk_level_thresholds,
        test_sigmoid_score,
        test_validation_missing_and_warning,
        test_missing_indicator_flagged_in_scoring,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {t.__name__}: {e}")
    print("-" * 50)
    print(f"总计 {len(tests)} 项，失败 {failed} 项。")
    sys.exit(1 if failed else 0)
