"""Public reporting data access: explicit versions, integrity and narrow scope."""
from copy import deepcopy
import importlib

import pytest
import solvency2 as s2

reporting = importlib.import_module("solvency2._core.reporting_catalog")


@pytest.mark.parametrize("version,count,rules", [
    ("2.8.2", 599, 6106), ("2.8.2-hotfix", 599, 6116), ("2.10.0", 570, 6746),
])
def test_catalog_versions(version, count, rules):
    catalog = s2.reporting_catalog(technical_version=version)
    assert catalog["technical_version"] == version
    assert len(catalog["modules"]) == 17
    assert len(catalog["tables"]) == count
    assert catalog["counts"]["vValidationRuleExpressions"] == rules
    assert catalog["legal_applicability_verified"] is False
    assert catalog["validation_rules_executed"] is False
    assert len(catalog["source"]["database_sha256"]) == 64


@pytest.mark.parametrize("version", [None, True, 2027, "latest", "2024-10-15", "2026-06-30", [], {}])
def test_unknown_or_implicit_version_rejected(version):
    with pytest.raises(s2.CalculationError, match="UNSUPPORTED_PARAMETER"):
        s2.reporting_catalog(technical_version=version)


@pytest.mark.parametrize("category", [None, [], {}, "all", "../profile", "profile.json"])
def test_unknown_category_rejected(category):
    with pytest.raises(s2.CalculationError, match="UNSUPPORTED_PARAMETER"):
        s2.reporting_data(category, technical_version="2.10.0")


@pytest.mark.parametrize("version", ["2.8.2", "2.8.2-hotfix", "2.10.0"])
@pytest.mark.parametrize("category", ["structure", "cells", "dictionary", "rules"])
def test_all_detail_categories(version, category):
    catalog = s2.reporting_catalog(technical_version=version)
    data = s2.reporting_data(category, technical_version=version)
    assert data["source"] == catalog["source"]
    assert data["technical_version"] == version
    assert data["validation_rules_executed"] is False
    assert sorted(data["tables"]) == catalog["detail_resources"][category]["tables"]
    for table, values in data["tables"].items():
        assert len(values) == catalog["counts"][table]


def test_catalog_load_does_not_load_details(monkeypatch):
    original = reporting.load_resource
    calls = []
    def tracked(name):
        calls.append(name)
        return original(name)
    monkeypatch.setattr(reporting, "load_resource", tracked)
    s2.reporting_catalog(technical_version="2.10.0")
    assert calls == ["reporting_2_10_0_catalog.json"]


def test_fresh_return_values():
    first = s2.reporting_catalog(technical_version="2.10.0")
    first["modules"].clear()
    assert len(s2.reporting_catalog(technical_version="2.10.0")["modules"]) == 17
    data = s2.reporting_data("rules", technical_version="2.8.2")
    data["tables"]["vValidationRuleExpressions"].clear()
    assert len(s2.reporting_data("rules", technical_version="2.8.2")["tables"]["vValidationRuleExpressions"]) == 6106


@pytest.mark.parametrize("mutation", ["resource", "hash", "version", "source", "inventory"])
def test_mismatched_bindings_rejected(monkeypatch, mutation):
    original = reporting.load_resource
    def corrupted(name):
        data = deepcopy(original(name))
        if name.endswith("catalog.json") and mutation == "resource":
            data["detail_resources"]["rules"]["resource"] = "../external.json.gz"
        elif name.endswith("catalog.json") and mutation == "hash":
            data["detail_resources"]["rules"]["sha256"] = "0" * 64
        elif name.endswith("rules.json.gz"):
            if mutation == "version":
                data["technical_version"] = "2.10.0"
            elif mutation == "source":
                data["source"]["source_id"] = "SRC-0000"
            elif mutation == "inventory":
                data["tables"]["unreviewed_extra"] = []
        return data
    monkeypatch.setattr(reporting, "load_resource", corrupted)
    with pytest.raises(s2.CalculationError, match="RESOURCE_INTEGRITY"):
        s2.reporting_data("rules", technical_version="2.8.2")


@pytest.mark.parametrize("version", ["2.8.2", "2.8.2-hotfix", "2.10.0"])
@pytest.mark.parametrize("code", ["S.02.01.01.01", "S.06.02.01.02", "S.37.02.04.02"])
def test_table_definition_scope(version, code):
    selected = s2.reporting_table(code, technical_version=version)
    assert selected["table"]["TableCode"] == code
    assert selected["cells"]
    assert all(row["TableID"] == selected["table"]["TableID"] for row in selected["cells"])
    axis_ids = {row["AxisID"] for row in selected["axes"]}
    assert all(row["AxisID"] in axis_ids for row in selected["ordinates"])
    cell_ids = {row["CellID"] for row in selected["cells"]}
    assert all(row["CellID"] in cell_ids for row in selected["cell_positions"])
    assert selected["open_axes_expanded"] is False
    assert selected["validation_rules_executed"] is False


@pytest.mark.parametrize("code", [None, [], "S.02.01", "s.02.01.01.01", "../profile.json"])
def test_unknown_table_rejected(code):
    with pytest.raises(s2.CalculationError, match="UNSUPPORTED_PARAMETER"):
        s2.reporting_table(code, technical_version="2.10.0")


def test_hotfix_nace_field_is_version_specific():
    base = s2.reporting_table("S.06.02.01.02", technical_version="2.8.2")
    hotfix = s2.reporting_table("S.06.02.01.02", technical_version="2.8.2-hotfix")
    assert "C0235" not in {row["OrdinateCode"] for row in base["ordinates"]}
    assert "C0235" in {row["OrdinateCode"] for row in hotfix["ordinates"]}


def test_bad_compressed_hash_is_rejected_before_decode(monkeypatch):
    import json
    from solvency2._core import core
    class Resource:
        def __init__(self, name=""):
            self.name = name
        def joinpath(self, name):
            return Resource(name)
        def read_bytes(self):
            if self.name == "manifest.json":
                return json.dumps({"sha256": {"reporting_2_10_0_rules.json.gz": "0" * 64}}).encode()
            return b"not-a-gzip-stream"
    monkeypatch.setattr(core, "files", lambda _: Resource())
    with pytest.raises(s2.CalculationError, match="RESOURCE_INTEGRITY"):
        core.load_resource("reporting_2_10_0_rules.json.gz")
