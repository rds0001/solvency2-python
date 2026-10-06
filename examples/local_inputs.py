"""Synthetic local CSV/JSON/in-memory parity; run from any working directory."""
from pathlib import Path

from solvency2 import Context
from solvency2.data import (DiscountCurve, best_estimate_with_curve,
                           discount_curve_from_spot_rates, load_discount_curve_csv,
                           load_discount_curve_json)

HERE = Path(__file__).resolve().parent
CONTEXT = Context("2028-12-31", "2028-12-31", "EUR", "EU-S2-DOCUMENTS-2027-v0.1")


def main():
    json_curve = load_discount_curve_json(HERE / "curve.json")
    metadata = {key: getattr(json_curve, key) for key in
                ("curve_id", "as_of", "currency", "curve_kind", "source_reference")}
    csv_curve = load_discount_curve_csv(HERE / "curve.csv", **metadata)
    memory_curve = DiscountCurve(**metadata, points=(("2029-12-31", 0.95),))
    assert csv_curve == json_curve == memory_curve
    results = [best_estimate_with_curve(
        {"2029-12-31": {"expected_inflows": 0, "expected_outflows": 100}},
        curve=curve, runoff_complete=True, cashflow_reference="SYNTHETIC: complete toy runoff",
        context=CONTEXT,
    ) for curve in (json_curve, csv_curve, memory_curve)]
    assert results[0] == results[1] == results[2]
    assert results[0].value == 95
    spot_curve = discount_curve_from_spot_rates(
        {"2029-12-31": {"annual_effective_rate": -0.01, "time_years": 1}},
        curve_id="synthetic-spot", curve_kind="base", source_reference="SYNTHETIC",
        time_basis_reference="Explicit annual anniversary: 1 year", context=CONTEXT,
    )
    assert abs(spot_curve.factor("2029-12-31") - 1 / 0.99) < 1e-12
    print("Local inputs: CSV = JSON = memory; best estimate = 95 EUR")


if __name__ == "__main__":
    main()
