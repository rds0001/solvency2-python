"""Public integration tests; run only after the prepared component is installed."""
from copy import deepcopy
import importlib

import pytest
from solvency2.catalogue import reference_dataset
import solvency2 as s2


@pytest.mark.parametrize("version", ["2.8.2", "2.8.2-hotfix", "2.10.0"])
def test_portable_archived_status_references(version):
    cases = reference_dataset("reference_reporting_validation_status.json")["cases"]
    catalog = s2.reporting_catalog(technical_version=version)
    expected_cases = [case for case in cases if case["technical_version"] == version]
    assert catalog["validation_status_reference_cases"] == expected_cases
    for case in expected_cases:
        result = s2.reporting_validation_status(case["validation_code"], technical_version=version, module=case["module"])
        assert {key: result[key] for key in case["expected"]} == case["expected"]
        assert result["current_deactivations_checked"] is False
        assert result["full_report_validated"] is False
        assert result["legal_applicability_verified"] is False
        assert len(result["input_hash"]) == 64


@pytest.mark.parametrize("version", [None, [], {}, "latest", "2026-06-03"])
def test_no_implicit_technical_version(version):
    with pytest.raises(s2.CalculationError, match="UNSUPPORTED_PARAMETER"):
        s2.reporting_validation_status("BV1053-1", technical_version=version, module="ars")


@pytest.mark.parametrize("module", [None, [], {}, "", "ARS", "ars|arg"])
def test_no_implicit_module(module):
    with pytest.raises(s2.CalculationError, match="INVALID_INPUT"):
        s2.reporting_validation_status("BV1053-1", technical_version="2.10.0", module=module)


@pytest.mark.parametrize("mutation", ["resource", "hash", "source", "snapshot", "version", "sheet"])
def test_status_resource_binding_integrity(monkeypatch, mutation):
    module = importlib.import_module("solvency2._core.reporting_catalog")
    original = module.load_resource

    def altered(name):
        data = deepcopy(original(name))
        if name.endswith("catalog.json"):
            descriptor = data["validation_status_resource"]
            if mutation == "resource":
                descriptor["resource"] = "../unqualified.json.gz"
            elif mutation == "hash":
                descriptor["sha256"] = "0" * 64
        elif name.endswith("validation_status.json.gz"):
            if mutation == "source":
                data["source"]["source_id"] = "SYNTHETIC_WRONG_SOURCE"
            elif mutation == "snapshot":
                data["snapshot_date"] = "2000-01-01"
            elif mutation == "version":
                data["technical_version"] = "2.8.2"
            elif mutation == "sheet":
                data["sheet"] = "Wrong sheet"
        return data

    monkeypatch.setattr(module, "load_resource", altered)
    with pytest.raises(s2.CalculationError, match="RESOURCE_INTEGRITY"):
        s2.reporting_validation_status("BV1053-1", technical_version="2.10.0", module="ars")


def test_archived_status_returns_fresh_nested_evidence():
    first = s2.reporting_validation_status("BV1750_1", technical_version="2.8.2-hotfix", module="ars")
    first["entries"][0]["values"]["Deactivated"] = "no"
    first["related_snapshot_conflicts"].clear()
    second = s2.reporting_validation_status("BV1750_1", technical_version="2.8.2-hotfix", module="ars")
    assert second["entries"][0]["values"]["Deactivated"] == "yes"
    assert second["related_snapshot_conflicts"]
    assert second["active_in_snapshot"] is None
