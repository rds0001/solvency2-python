"""Joint component evidence does not silently become a filing certificate."""

import pytest
from solvency2.catalogue import reference_dataset
import solvency2 as s2

PORTFOLIOS = reference_dataset("reference_reporting_portfolios.json")["portfolios"]


@pytest.mark.parametrize("portfolio", PORTFOLIOS, ids=lambda value: value["id"])
def test_reporting_component_chain(portfolio):
    version = portfolio["technical_version"]
    expected = portfolio["expected"]
    assert portfolio in s2.reporting_catalog(technical_version=version)["reporting_reference_portfolios"]
    status = s2.reporting_validation_status(portfolio["validation_code"], technical_version=version, module=portfolio["module"])
    condition = s2.reporting_rule_precondition(portfolio["validation_code"], portfolio["filing_indicators"],
                                               technical_version=version, module=portfolio["module"])
    original = s2.reporting_table("S.26.13.01.14", technical_version=version)
    cells = {cell["BusinessCode"]: cell for cell in original["cells"]}
    metric_results = []
    for fact in portfolio["facts"]:
        code = portfolio["metric_codes"][fact["cell"]]
        # Explicit reference-fixture identity, not a generic prefix converter.
        assert cells[fact["cell"]]["DatapointSignature"].startswith("MET(s2md_met:" + code + ")|")
        metric_results.append(s2.reporting_metric_value_check(code, fact["fact"], technical_version=version))
    expression = s2.reporting_closed_rule_check(portfolio["validation_code"], portfolio["facts"],
                                                technical_version=version, fact_context=portfolio["fact_context"],
                                                binding_reference=portfolio["binding_reference"])
    assert status["active_in_snapshot"] is expected["archived_rule_active"]
    assert condition["precondition_met"] is expected["filing_precondition_met"]
    assert [result["value"] for result in metric_results] == expected["metric_values"]
    assert expression["value"] is expected["expression"]
    conjunction = all([status["active_in_snapshot"], condition["precondition_met"],
                       *[result["value"] for result in metric_results], expression["value"]])
    assert conjunction is expected["all_checked_components_pass"]
    for result in (status, condition, *metric_results, expression):
        assert result["full_report_validated"] is False
        assert result["legal_applicability_verified"] is False


@pytest.mark.parametrize("portfolio", PORTFOLIOS, ids=lambda value: value["id"])
def test_reporting_same_facts_to_xml_and_selected_rule(portfolio):
    """New join only: reuse the existing independently specified portfolio."""
    facts = [{"business_code": item["cell"], "atom": item["fact"]} for item in portfolio["facts"]]
    options = dict(technical_version=portfolio["technical_version"], module=portfolio["module"],
                   entity={"scheme": "SC", "identifier": "SYNTHETIC-NOT-FOR-SUBMISSION"},
                   instant=portfolio["fact_context"]["period"], indicators=portfolio["filing_indicators"],
                   qualification_reference=portfolio["binding_reference"],
                   validation_codes=[portfolio["validation_code"]])
    if not all(portfolio["expected"]["metric_values"]):
        with pytest.raises(s2.CalculationError, match="datatype/domain"):
            s2.reporting_instance(facts, **options)
        return
    result = s2.reporting_instance(facts, **options)
    expected = "PASS" if portfolio["expected"]["expression"] else "FAIL"
    assert result["selected_rule_checks"][0]["status"] == expected
    assert len(result["reconciliation"]) == len(facts)
    assert result["xml_well_formed"]
    assert not result["full_report_validated"] and not result["submission_ready"]
    assert not result["all_archived_rules_executed"]
