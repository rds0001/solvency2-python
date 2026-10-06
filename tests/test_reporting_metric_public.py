"""Metric domains and rule expressions deliberately remain separate checks."""

import pytest
from solvency2.catalogue import reference_dataset
import solvency2 as s2

CASES = reference_dataset("reference_reporting_metric_cases.json")["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_portable_metric_value_references(case):
    if "expected_error" in case:
        with pytest.raises(s2.CalculationError) as caught:
            s2.reporting_metric_value_check(case["metric_code"], case["fact"], technical_version=case["technical_version"])
        assert caught.value.code == case["expected_error"]
    else:
        result = s2.reporting_metric_value_check(case["metric_code"], case["fact"], technical_version=case["technical_version"])
        assert result["value"] is case["expected"]
        assert result["xml_schema_validated"] is False
        assert result["business_rules_executed"] is False
        assert result["full_report_validated"] is False
        assert len(result["input_hash"]) == 64


@pytest.mark.parametrize("version", ["2.8.2", "2.8.2-hotfix", "2.10.0"])
def test_bundled_cases_and_opposite_expression_domain_outcomes(version):
    assert s2.reporting_catalog(technical_version=version)["metric_reference_cases"] == [
        case for case in CASES if case["technical_version"] == version]
    forbidden_currency = {"qname": {"namespace": "http://eiopa.europa.eu/xbrl/s2c/dict/dom/CU", "local_name": "x7"}}
    assert s2.reporting_metric_value_check("ei1024", forbidden_currency, technical_version=version)["value"] is True
    assert s2.reporting_bound_rule_check("BV1339", {"v0": forbidden_currency}, technical_version=version,
                                        binding_reference="synthetic://separate-domain-and-business-rule")["value"] is False
    invalid_peril = {"qname": {"namespace": "http://eiopa.europa.eu/xbrl/s2c/dict/dom/RT", "local_name": "x256"}}
    assert s2.reporting_metric_value_check("ei2578", invalid_peril, technical_version=version)["value"] is False
    assert s2.reporting_bound_rule_check("BV1853", {"v0": invalid_peril, "v1": {"text": "synthetic"}},
                                        technical_version=version, binding_reference="synthetic://invalid-domain")["value"] is True


@pytest.mark.parametrize("metric", [None, [], {}, "", "s2md_MET:ei2578", "unknownMetric"])
def test_exact_unqualified_metric_code_is_not_guessed(metric):
    with pytest.raises(s2.CalculationError):
        s2.reporting_metric_value_check(metric, {"text": "x"}, technical_version="2.10.0")


@pytest.mark.parametrize("version", [None, [], "latest", "2026-06-30"])
def test_no_implicit_metric_version(version):
    with pytest.raises(s2.CalculationError, match="UNSUPPORTED_PARAMETER"):
        s2.reporting_metric_value_check("si2627", {"text": "x"}, technical_version=version)
