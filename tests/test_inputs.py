"""New adapters only; fixed values are independent of the implementation."""
from dataclasses import replace
import json
import math

import pytest

from solvency2 import CalculationError, Context, intangible_risk, parameter
from solvency2.data import (DiscountCurve, best_estimate_with_curve,
                           discount_curve_from_spot_rates, load_discount_curve_csv,
                           load_discount_curve_json)
from solvency2.scenarios import load_numeric_overrides_json, numeric_overrides_from_dict


@pytest.fixture
def context():
    return Context("2028-12-31", "2028-12-31", "EUR", "EU-S2-DOCUMENTS-2027-v0.1")


@pytest.fixture
def curve():
    return DiscountCurve("synthetic", "2028-12-31", "EUR", "base", "SYNTHETIC", (("2029-12-31", .95),))


def estimate(curve, context):
    return best_estimate_with_curve(
        {"2029-12-31": {"expected_inflows": 0, "expected_outflows": 100}},
        curve=curve, runoff_complete=True, cashflow_reference="SYNTHETIC", context=context)


def test_local_parity_and_signed_cashflows(tmp_path, curve, context):
    path = tmp_path / "curve.json"
    path.write_text(json.dumps(curve.to_dict()))
    csv = tmp_path / "curve.csv"
    csv.write_text("date,discount_factor\n2029-12-31,0.95\n")
    meta = {key: getattr(curve, key) for key in ("curve_id", "as_of", "currency", "curve_kind", "source_reference")}
    loaded = load_discount_curve_json(path)
    assert loaded == load_discount_curve_csv(csv, **meta) == curve
    result = estimate(curve, context)
    assert estimate(loaded, context) == result and result.value == 95
    assert result.details["user_curve"]["qualification_status"] == "EXTERNAL_UNVERIFIED"
    assert str(tmp_path) not in json.dumps(result.to_dict())
    reverse = best_estimate_with_curve(
        {"2029-12-31": {"expected_inflows": 100, "expected_outflows": 0}},
        curve=curve, runoff_complete=True, cashflow_reference="SYNTHETIC", context=context)
    assert reverse.value == -95


def test_hash_order_provenance_and_defensive_copy(curve, context):
    points = [["2030-12-31", .9], ["2029-12-31", .95]]
    ordered = replace(curve, points=points)
    same = replace(curve, points=list(reversed(points)))
    assert ordered.input_hash == same.input_hash
    points[0][1] = 42
    payload = ordered.to_dict()
    payload["points"].clear()
    assert ordered.factor("2030-12-31") == .9
    assert estimate(curve, context).input_hash != estimate(replace(curve, source_reference="OTHER"), context).input_hash
    assert estimate(curve, context).input_hash != estimate(replace(curve, points=(("2029-12-31", .96),)), context).input_hash


@pytest.mark.parametrize("factor", [0, -1, True, "0.95", math.nan, math.inf, None])
def test_bad_factors(curve, factor):
    with pytest.raises(CalculationError):
        replace(curve, points=(("2029-12-31", factor),))


@pytest.mark.parametrize("changes", [
    {"points": ()}, {"points": (("2029-12-31", .9), ("2029-12-31", .8))},
    {"points": (("2027-01-01", .9),)}, {"points": (("2028-12-31", .9),)},
    {"points": (("bad", .9),)}, {"currency": "eur"}, {"curve_kind": "latest"},
    {"source_reference": ""}, {"as_of": "20281231"},
])
def test_bad_metadata(curve, changes):
    with pytest.raises(CalculationError):
        replace(curve, **changes)


@pytest.mark.parametrize("patch", [{"schema_version": True}, {"schema_version": 2}, {"unit": "percent"},
                                  {"value_type": "spot_rate"}, {"extra": 1}, {"points": {}}])
def test_json_schema(curve, patch):
    with pytest.raises(CalculationError):
        DiscountCurve.from_dict({**curve.to_dict(), **patch})


def test_missing_and_mismatched_inputs(curve, context):
    with pytest.raises(CalculationError, match="MISSING_INPUT"):
        curve.factor("2030-12-31")
    for other in (replace(context, currency="USD"), replace(context, as_of="2029-01-01")):
        with pytest.raises(CalculationError):
            estimate(curve, other)
    assert replace(curve, points=(("2029-12-31", 1.02),)).factor("2029-12-31") == 1.02


@pytest.mark.parametrize("content", ['{"schema_version":1,"schema_version":1}', "not json", "[", "null"])
def test_bad_json_file(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content)
    with pytest.raises(CalculationError):
        load_discount_curve_json(path)


@pytest.mark.parametrize("content", ["date,date\na,b\n", "date,discount_factor\n2029-12-31,nan\n",
                                   "date,discount_factor\n2029-12-31\n", "date,discount_factor\n2029-12-31,.9,x\n"])
def test_bad_csv_file(tmp_path, content, curve):
    path = tmp_path / "bad.csv"
    path.write_text(content)
    with pytest.raises(CalculationError):
        load_discount_curve_csv(path, curve_id=curve.curve_id, as_of=curve.as_of, currency=curve.currency,
                                curve_kind=curve.curve_kind, source_reference=curve.source_reference)


@pytest.mark.parametrize("path", ["https://example.invalid/curve", "http://example.invalid", "file:///tmp/a"])
def test_urls_rejected(path):
    with pytest.raises(CalculationError, match="UNSUPPORTED_INPUT"):
        load_discount_curve_json(path)
    with pytest.raises(CalculationError, match="UNSUPPORTED_INPUT"):
        load_numeric_overrides_json(path)


def test_missing_file_is_controlled(tmp_path):
    with pytest.raises(CalculationError, match="INPUT_IO_ERROR"):
        load_discount_curve_json(tmp_path / "absent")


def spot(points, context, basis="Explicit anniversary"):
    return discount_curve_from_spot_rates(points, curve_id="SYNTHETIC", curve_kind="base",
                                          source_reference="SYNTHETIC", time_basis_reference=basis, context=context)


def test_explicit_spot_conversion(context):
    rows = {"2029-12-31": {"annual_effective_rate": -.01, "time_years": 1},
            "2030-12-31": {"annual_effective_rate": .02, "time_years": 2}}
    curve = spot(rows, context)
    assert curve.factor("2029-12-31") == pytest.approx(1 / .99)
    assert curve.factor("2030-12-31") == pytest.approx(1 / 1.02**2)
    assert spot(rows, context, "Different supplied basis").input_hash != curve.input_hash
    for row in ({"annual_effective_rate": -1, "time_years": 1},
                {"annual_effective_rate": .01, "time_years": 0},
                {"annual_effective_rate": 1, "time_years": "1"}):
        with pytest.raises(CalculationError):
            spot({"2029-12-31": row}, context)


def test_scenario_file_restoration_and_audit(tmp_path, context):
    payload = {"schema_version": 1, "overrides": [{"resource": "profile.json",
               "path": ["scalars", "intangible", "value"], "value": .7, "reason": "SYNTHETIC"}]}
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(payload))
    assert load_numeric_overrides_json(path) == numeric_overrides_from_dict(payload)
    scenario = replace(context, overrides=load_numeric_overrides_json(path))
    before = parameter("scalars/intangible", context=context)
    result = intangible_risk(100, context=scenario)
    assert result.value == 70 and result.status == "ANALYST_SCENARIO"
    assert result.details["analyst_overrides"][0]["original"] == .8
    assert intangible_risk(100, context=context).value == 80
    assert parameter("scalars/intangible", context=context) == before
    assert numeric_overrides_from_dict({"schema_version": 1, "overrides": []}) == ()
    for changes in ({"path": [True]}, {"path": []}, {"value": True}, {"reason": ""}):
        with pytest.raises(CalculationError):
            numeric_overrides_from_dict({**payload, "overrides": [{**payload["overrides"][0], **changes}]})
    invalid = numeric_overrides_from_dict({**payload, "overrides": [
        {**payload["overrides"][0], "path": ["scalars", "unknown", "value"]}]})
    with pytest.raises(CalculationError, match="UNSUPPORTED_PARAMETER"):
        replace(context, overrides=invalid).validate()
