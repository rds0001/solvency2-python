"""One bundled acceptance pass; independent expected values are never regenerated."""
from dataclasses import replace
import importlib.util

import pytest
import solvency2 as s2

BASE = s2.Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
CASES = s2.reference_cases()["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_independent_reference(case):
    context = replace(BASE, **case.get("context", {}))
    function = getattr(s2, case["function"])
    if "expected_error" in case:
        with pytest.raises(s2.CalculationError) as caught:
            function(**case["kwargs"], context=context)
        assert caught.value.code == case["expected_error"]
        return
    try:
        result = function(**case["kwargs"], context=context)
    except s2.CalculationError as error:
        if (error.code == "REVIEW_REQUIRED" and error.field in {"optimizer", "numerical_backend"}
                and importlib.util.find_spec("scipy") is None):
            pytest.skip("Optional SciPy method: install statistics/optimization extra for full acceptance")
        raise
    assert result.value == pytest.approx(case["expected"], rel=1e-12, abs=case.get("absolute_tolerance", 1e-12))
    assert result.sources and result.status == case.get("expected_status", "REFERENCE_COMPONENT")
    assert len(result.input_hash) == len(result.profile_hash) == 64
    assert result.to_dict()["value"] == result.value


@pytest.mark.parametrize("portfolio", s2.reference_portfolios()["portfolios"], ids=lambda p: p["id"])
def test_integration_portfolio(portfolio):
    engine = s2.Engine()
    result = engine.run(portfolio["nodes"], context=s2.Context(**portfolio["context"]))
    assert result["status"] == "PARTIAL" and result["regulatory_total_released"] is False
    assert set(result["results"]) == set(portfolio["expected_values"])
    for name, expected in portfolio["expected_values"].items():
        assert result["results"][name]["value"] == pytest.approx(
            expected, rel=1e-12, abs=portfolio.get("absolute_tolerances", {}).get(name, 1e-12))
        assert result["results"][name]["sources"]
