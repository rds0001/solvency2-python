"""Inspect, override and restore a scalar and a symmetric matrix."""
from dataclasses import replace
from pathlib import Path

from solvency2 import Context, NumericOverride, aggregate_risk, intangible_risk, parameter
from solvency2.scenarios import load_numeric_overrides_json


def main():
    base = Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
    original = parameter("scalars/intangible", context=base)
    scenario = replace(base, overrides=load_numeric_overrides_json(Path(__file__).with_name("scenario.json")))
    changed = intangible_risk(100, context=scenario)
    assert changed.value == 70 and changed.status == "ANALYST_SCENARIO"
    assert changed.details["analyst_overrides"][0]["original"] == original["value"] == 0.8
    assert intangible_risk(100, context=base).value == 80
    correlated = replace(base, overrides=(NumericOverride(
        "profile.json", ("matrices", "health_nslt", "values", 0, 1), 0.5, "Synthetic correlation",
    ),))
    matrix = parameter("matrices/health_nslt", context=correlated)
    assert matrix["values"][0][1] == matrix["values"][1][0] == 0.5
    assert abs(aggregate_risk({"premium_reserve": 3, "lapse": 4}, "health_nslt", context=correlated).value - 37**0.5) < 1e-12
    assert aggregate_risk({"premium_reserve": 3, "lapse": 4}, "health_nslt", context=base).value == 5
    print("Scenarios: scalar 80 -> 70 -> 80; correlation mirrored; baseline unchanged")


if __name__ == "__main__":
    main()
