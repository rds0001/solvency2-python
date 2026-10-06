"""Public-edition data boundary, local imports and synthetic provenance."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest
import solvency2 as s2

BASE = s2.Context("2025-01-31", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")


def user_archive(rate=.07, as_of="2025-02-28"):
    """Independently invented stand-in for a caller-owned file (no market source)."""
    digest = hashlib.sha256(str(rate).encode()).hexdigest()
    return {"schema_version": 1, "status": "USER_SUPPLIED", "datasets": {as_of: {
        "data_kind": "USER_SUPPLIED", "source_id": "TEST_CALLER_OWN_INPUT", "retrieved_at": "2025-03-01",
        "archive_sha256": digest, "member": "my-local-grid.json", "member_sha256": digest,
        "maturities": [1], "rate_row_offset": 0, "unit": "decimal_rate", "blocked_series": {},
        "series": {"EUR": {"raw_currency_metadata": "EUR", "label": "test caller EUR", "column": "C1",
            "currency_metadata_status": "USER_SUPPLIED", "variants": {
                "no_va": {"raw_metadata": {"VA": 0}, "sheet": "my-grid", "rates": [rate]}}}},
    }}}


def spot(*, context=BASE, **kwargs):
    return s2.rfr_archived_spot_rate("EUR", 1, "no_va", qualification_reference="TEST", context=context, **kwargs)


def test_demo_accessor_and_reference_scope():
    data = s2.rfr_monthly_data()
    assert data["synthetic"] is True and data["status"] == "SYNTHETIC_DEMO"
    assert list(data["datasets"]) == ["2025-01-31"]
    assert "Flat EUR/USD" in data["recipe"]
    data.clear()
    assert s2.rfr_monthly_data()["datasets"]
    assert s2.coverage()["official_rfr_data"]["included"] is False


@pytest.mark.parametrize("case", [c for c in s2.reference_cases()["cases"]
                                  if c["function"].startswith("rfr_archived_")], ids=lambda c: c["id"])
def test_demo_all_lookup_families(case):
    with pytest.warns(UserWarning, match="SYNTHETIC_DEMO"):
        result = getattr(s2, case["function"])(**case["kwargs"], context=BASE)
    assert result.value == pytest.approx(case["expected"])
    assert result.status == "SYNTHETIC_DEMO" and "SYNTHETIC_DEMO" in result.sources
    assert result.details["market_data_kind"] == "SYNTHETIC_DEMO"
    assert len(result.details["market_dataset_hash"]) == 64


def test_local_file_new_date_no_mutation_and_fingerprints(tmp_path):
    path = tmp_path / "own-data.json"
    path.write_text(json.dumps(user_archive()))
    data = json.loads(path.read_text())
    before = deepcopy(data)
    context = replace(BASE, as_of="2025-02-28")
    result = spot(context=context, market_data=data)
    assert result.value == .07 and result.status == "REFERENCE_COMPONENT"
    assert result.details["market_data_kind"] == "USER_SUPPLIED"
    assert data == before and "SYNTHETIC_DEMO" not in result.sources
    changed = spot(context=context, market_data=user_archive(.08))
    assert changed.value == .08 and changed.input_hash != result.input_hash
    assert changed.details["market_dataset_hash"] != result.details["market_dataset_hash"]


@pytest.mark.parametrize("payload", [{}, {"schema_version": 1}, [], {"schema_version": 2},
    {"schema_version": 1, "status": "USER_SUPPLIED", "datasets": {"2025-01-31": {}}}])
def test_incomplete_external_input_never_falls_back(payload):
    with pytest.raises(s2.CalculationError) as caught:
        spot(market_data=payload)
    assert caught.value.code in {"INVALID_INPUT", "MISSING_INPUT"}


def test_exact_date_knowledge_currency_and_tenor_guards():
    with pytest.raises(s2.CalculationError) as caught:
        spot(market_data=user_archive())
    assert caught.value.code == "MISSING_INPUT"
    context = replace(BASE, as_of="2025-02-28")
    for changes in ({"known_at": "2025-02-28"}, {"currency": "USD"}):
        with pytest.raises(s2.CalculationError) as caught:
            spot(context=replace(context, **changes), market_data=user_archive())
        assert caught.value.code == "REVIEW_REQUIRED"
    for tenor, error in ((1.5, "UNSUPPORTED_METHOD"), (2, "MISSING_INPUT")):
        with pytest.raises(s2.CalculationError) as caught:
            s2.rfr_archived_spot_rate("EUR", tenor, "no_va", qualification_reference="TEST",
                                     context=context, market_data=user_archive())
        assert caught.value.code == error


@pytest.mark.parametrize("mutation", ["nonfinite", "missing_rates", "invalid_date", "wrong_kind", "blocked", "va"])
def test_malformed_or_disallowed_external_table(mutation):
    data = user_archive()
    dataset = data["datasets"]["2025-02-28"]
    error = "INVALID_INPUT"
    if mutation == "nonfinite":
        dataset["extra"] = float("nan")
    elif mutation == "missing_rates":
        del dataset["series"]["EUR"]["variants"]["no_va"]["rates"]
    elif mutation == "invalid_date":
        dataset["retrieved_at"] = "yesterday"
    elif mutation == "wrong_kind":
        dataset["data_kind"] = "SYNTHETIC_DEMO"
    elif mutation == "blocked":
        dataset["blocked_series"]["EUR"] = "caller excluded this series"
        error = "REVIEW_REQUIRED"
    else:
        dataset["series"]["EUR"]["variants"]["no_va"]["rates"] = [-1]
        error = "REVIEW_REQUIRED"
    with pytest.raises(s2.CalculationError) as caught:
        spot(context=replace(BASE, as_of="2025-02-28"), market_data=data)
    assert caught.value.code == error


def test_demo_overrides_stay_demo_and_do_not_modify_external_data():
    entry = s2.NumericOverride("rfr_monthly.json",
        ("datasets", "2025-01-31", "series", "EUR", "variants", "no_va", "rates", 0), .09, "synthetic test")
    context = replace(BASE, overrides=(entry,))
    with pytest.warns(UserWarning, match="SYNTHETIC_DEMO"):
        result = spot(context=context)
    assert result.value == .09 and result.status == "SYNTHETIC_DEMO"
    assert result.details["analyst_overrides"]
    with pytest.raises(s2.CalculationError, match="INVALID_INPUT"):
        spot(context=context, market_data=user_archive(as_of="2025-01-31"))


def test_demo_dependency_status_survives_cache_without_contaminating_pure_values():
    engine = s2.Engine()
    inputs = {"spot_rate": .05, "time_years": 1, "qualification_reference": "TEST"}
    direct = {"discount": {"function": "rfr_spot_discount_factor", "inputs": inputs}}
    assert engine.run(direct, context=BASE)["results"]["discount"]["status"] == "REFERENCE_COMPONENT"
    nodes = {"spot": {"function": "rfr_archived_spot_rate", "inputs": {
        "series_id": "EUR", "maturity_years": 1, "variant": "no_va", "qualification_reference": "TEST"}},
        "discount": {"function": "rfr_spot_discount_factor", "inputs": {**inputs, "spot_rate": {"$ref": "spot"}}}}
    with pytest.warns(UserWarning, match="SYNTHETIC_DEMO"):
        result = engine.run(nodes, context=BASE)
    assert "discount" in result["cache_hits"]
    assert result["results"]["discount"]["status"] == "SYNTHETIC_DEMO"
    assert engine.run(nodes, context=BASE)["results"]["discount"]["status"] == "SYNTHETIC_DEMO"
    assert engine.run(direct, context=BASE)["results"]["discount"]["status"] == "REFERENCE_COMPONENT"


def test_entire_demo_portfolio_is_marked():
    portfolio = next(p for p in s2.reference_portfolios()["portfolios"] if p["id"] == "synthetic-market-to-one-year-provisions")
    with pytest.warns(UserWarning, match="SYNTHETIC_DEMO"):
        results = s2.calculate(portfolio["nodes"], context=s2.Context(**portfolio["context"]))["results"]
    assert all(result["status"] == "SYNTHETIC_DEMO" for result in results.values())
    for name, expected in portfolio["expected_values"].items():
        assert results[name]["value"] == pytest.approx(expected)
