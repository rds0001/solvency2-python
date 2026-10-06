"""Regulatory interfaces to insurer-owned models; no model is constructed here."""
from collections.abc import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory


_CONDITIONS = (
    "standard_formula_estimate_requested", "transition_plan_requested",
    "major_change_or_policy_change", "return_to_standard_formula", "noncompliance_present",
    "diversification_used", "risk_mitigation_used", "future_management_actions_used",
    "approximation_used", "benchmark_requested", "third_party_used", "va_spread_effects_used",
)


def _reference(value, name):
    require(isinstance(value, str) and bool(value.strip()), name,
            "versioned external model/scope reference required", "MISSING_INPUT")


@calculation("DIR:articles-112-126")
def external_model_checked_value(value: float, evidence: Mapping, *, model_kind: str,
                                  output_kind: str, conditions: Mapping,
                                  model_reference: str, assessment_reference: str,
                                  scope_reference: str, context: Context):
    """Forward an externally computed value after declared-evidence checks.

    AVAILABLE references do not prove their contents, model approval, adequacy
    or lawful integration. Partial-model results must already follow the
    externally approved integration; this function applies no correlations.
    Period metadata is not a calendar-deadline monitor or submission service.
    """
    _reference(model_reference, "model_reference")
    _reference(scope_reference, "scope_reference")
    require(isinstance(model_kind, str) and model_kind in ("full", "partial"),
            "model_kind", "full or partial model required")
    require(isinstance(output_kind, str) and output_kind in
            ("scr", "bscr_module", "bscr_submodule", "operational", "adjustment"),
            "output_kind", "explicit supported model output required")
    require(model_kind == "partial" or output_kind == "scr", "output_kind",
            "full-model interface supports SCR only", "UNSUPPORTED_METHOD")
    amount = number(value, "value", None if output_kind == "adjustment" else 0)
    exact_keys(conditions, _CONDITIONS, "conditions")
    facts = {key: _declared_bool(conditions[key], key) for key in _CONDITIONS}
    facts["partial"] = model_kind == "partial"
    require(facts["partial"] or not facts["transition_plan_requested"], "transition_plan_requested",
            "Article113 transition plan belongs to a partial-model scope")
    profile = effective_resource("profile.json", context)
    future = "model_standard_formula_report_interval_years" in profile["scalars"]
    require(future or not facts["va_spread_effects_used"], "va_spread_effects_used",
            "new Article122(5) branch unavailable in historical profile", "UNSUPPORTED_RULESET")
    rows = profile["tables"]["external_model_controls"]["rows"]
    active = [row[:3] for row in rows if row[3] == "always" or facts[row[3]]]
    complete, details = _evidence_inventory(evidence, {"rows": active}, assessment_reference)
    unresolved = [key for key, row in details["controls"].items() if row["status"] != "AVAILABLE"]
    require(bool(complete), "evidence", "model evidence missing or unresolved: " + ", ".join(unresolved),
            "REVIEW_REQUIRED")
    periods = {}
    for key in ("model_data_update_interval_years", "model_profit_loss_review_interval_years",
                "model_standard_formula_report_interval_years", "model_risk_coverage_review_interval_years",
                "model_experience_test_interval_years", "model_management_report_interval_years"):
        if key == "model_management_report_interval_years" and not facts["future_management_actions_used"]:
            continue
        if key in profile["scalars"]:
            period = number(scalar(key, context), key, 0)
            require(period > 0, key, "positive period required")
            periods[key] = period
    adaptation_max = number(scalar("model_supervisory_adaptation_max_months", context),
                            "model_supervisory_adaptation_max_months", 0)
    require(adaptation_max > 0, "model_supervisory_adaptation_max_months", "positive maximum required")
    return amount, {**details, "model_kind": model_kind, "output_kind": output_kind,
        "conditions": facts, "model_reference": model_reference, "scope_reference": scope_reference,
        "inactive_controls": [row[0] for row in rows if row[3] != "always" and not facts[row[3]]],
        "required_periods_years": periods, "deadlines_monitored": False,
        "supervisory_adaptation_limit": {"maximum_months": adaptation_max,
            "source": "DR:article-281", "applicability": "EXTERNAL_SUPERVISORY_DECISION_REQUIRED",
            "deadline_assigned": False, "general_noncompliance_grace_period": False},
        "model_generated": False, "model_approval_verified": False, "regulatory_total_released": False,
        "scope": "declared_external_model_evidence_and_value_not_model_or_integration_approval",
        "_sources": details["_sources"] + [context.profile_id + ":" + profile["sources"]["DIR"]["sha256"]
                                           + ":articles-112-126", "DR:article-281"]}


@calculation("DIR:article-122:5", unit="indicator")
def model_va_scr_floor_2027(model_scr: float, standard_va_scr: float, own_portfolio_va_scr: float, *,
                            permitted_by_member_state: bool, excludes_company_adjustment: bool,
                            excludes_macro_va: bool, qualification_reference: str, context: Context):
    """Check declared method conditions and two external SCR floors, not raise SCR."""
    _reference(qualification_reference, "qualification_reference")
    conditions = {key: _declared_bool(flag, key) for key, flag in (
        ("permitted_by_member_state", permitted_by_member_state),
        ("excludes_company_adjustment", excludes_company_adjustment),
        ("excludes_macro_va", excludes_macro_va))}
    actual = number(model_scr, "model_scr", 0)
    standard = number(standard_va_scr, "standard_va_scr", 0)
    own = number(own_portfolio_va_scr, "own_portfolio_va_scr", 0)
    floor = max(standard, own)
    profile = effective_resource("profile.json", context)
    return int(all(conditions.values()) and actual >= floor), {
        "model_scr": actual, "standard_va_scr": standard, "own_portfolio_va_scr": own,
        "comparison_floor": floor, "conditions": conditions, "scr_adjusted": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "portfolio_or_comparison_models_verified": False, "regulatory_total_released": False,
        "scope": "declared_dynamic_VA_conditions_and_SCR_comparison_only",
        "_sources": [context.profile_id + ":" + profile["sources"]["DIR"]["sha256"] + ":article-122-5"]}
