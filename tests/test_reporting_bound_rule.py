"""Public check of a rule expression with declared, already resolved facts."""
import pytest
import solvency2 as s2


def facts(total=1005):
    return {"v1": {"value": total, "decimals": 0},
            "v2": {"values": [{"value": x, "decimals": 0} for x in (100, 200, 300, 400)]}}


def check(bindings=None, version="2.10.0", code="BV1053-1", reference="synthetic://resolved-single-entity-EUR-2027"):
    return s2.reporting_bound_rule_check(code, facts() if bindings is None else bindings,
        technical_version=version, binding_reference=reference)


@pytest.mark.parametrize("version,expected", [("2.8.2", False), ("2.8.2-hotfix", False), ("2.10.0", True)])
def test_original_rule_version_boundary(version, expected):
    result = check(version=version)
    assert result["value"] is expected
    assert result["technical_version"] == version
    assert result["status"] == "REFERENCE_EXPRESSION_COMPONENT"
    assert result["binding_qualification_verified"] is False
    assert result["full_report_validated"] is False
    assert result["current_deactivations_checked"] is False
    assert set(result["selectors"]) == {"v1", "v2"}
    assert len(result["rule_hash"]) == len(result["input_hash"]) == 64


@pytest.mark.parametrize("total,expected", [(1010, True), ("1010.001", False), (990, True), ("989.999", False)])
def test_inclusive_margin(total, expected):
    assert check(facts(total))["value"] is expected


@pytest.mark.parametrize("bindings", [None, [], {}, {"v1": {"value": 0, "decimals": 0}},
    {**facts(), "v3": {"value": 0, "decimals": 0}}])
def test_incomplete_or_extra_bindings_rejected(bindings):
    with pytest.raises(s2.CalculationError):
        s2.reporting_bound_rule_check("BV1053-1", bindings, technical_version="2.10.0", binding_reference="synthetic")


@pytest.mark.parametrize("record", [
    None, {"value": True, "decimals": 0}, {"value": float("nan"), "decimals": 0},
    {"value": 0}, {"value": 0, "decimals": None}, {"values": []},
    {"value": 0, "decimals": 0, "extra": 1},
])
def test_invalid_scalar_binding_rejected(record):
    with pytest.raises(s2.CalculationError):
        check({**facts(), "v1": record})


@pytest.mark.parametrize("reference", [None, "", " ", 4])
def test_qualification_reference_required(reference):
    with pytest.raises(s2.CalculationError):
        check(reference=reference)


@pytest.mark.parametrize("code", [None, [], "UNKNOWN", "bv1053-1"])
def test_unknown_rule_rejected(code):
    with pytest.raises(s2.CalculationError):
        check(code=code)


def test_global_filter_join_not_silently_ignored():
    with pytest.raises(s2.CalculationError, match="UNSUPPORTED_METHOD"):
        check(code="BV364-1")


def test_input_trace_changes_with_value_or_reference():
    assert check()["input_hash"] != check(facts(1000))["input_hash"]
    assert check()["input_hash"] != check(reference="synthetic-other")["input_hash"]


def test_oversized_decimal_exponent_is_controlled_input_error():
    with pytest.raises(s2.CalculationError, match="TECHNICAL_LIMIT"):
        check(facts("1e1000000000"))


@pytest.mark.parametrize("version", ["2.8.2", "2.8.2-hotfix", "2.10.0"])
def test_typed_original_rule_reference_cases(version):
    catalog = s2.reporting_catalog(technical_version=version)
    cases = catalog["typed_reference_cases"]
    assert len(cases) == 10
    for case in cases:
        result = s2.reporting_bound_rule_check(case["validation_code"], case["bindings"],
            technical_version=version, binding_reference=case["binding_reference"])
        assert result["value"] is case["expected"], case["id"]
        assert result["full_report_validated"] is False
        assert result["binding_qualification_verified"] is False


@pytest.mark.parametrize("record", [{"text": None}, {"boolean": 1}, {"absent": False},
    {"qname": "s2c_CU:x7"}, {"qname": {"namespace": "urn:x", "local_name": "a:b"}},
    {"text": "x", "decimals": 0}])
def test_invalid_explicit_type_tag(record):
    with pytest.raises(s2.CalculationError):
        s2.reporting_bound_rule_check("BV1339", {"v0": record}, technical_version="2.10.0", binding_reference="synthetic")


def test_absence_is_not_a_declared_sequence_item():
    with pytest.raises(s2.CalculationError):
        check({"v1": {"value": 0, "decimals": "INF"}, "v2": {"values": [{"absent": True}]}})


@pytest.mark.parametrize("version", ["2.8.2", "2.8.2-hotfix", "2.10.0"])
def test_portable_synthetic_reference_cases(version):
    catalog = s2.reporting_catalog(technical_version=version)
    assert catalog["reference_cases_status"] == "SYNTHETIC_BOUND_EXPRESSION_CASES_NOT_FULL_REPORTS"
    cases = catalog["reference_cases"]
    assert len(cases) == (8 if version == "2.10.0" else 4)
    for case in cases:
        result = s2.reporting_bound_rule_check(case["validation_code"], case["bindings"],
            technical_version=case["technical_version"], binding_reference=case["binding_reference"])
        assert result["value"] is case["expected"]
        assert result["full_report_validated"] is False
