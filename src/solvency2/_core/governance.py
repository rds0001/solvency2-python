"""Declared governance evidence and prescribed limits, not a compliance opinion."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory, _reference
from .national_de import _de_ppp_assessment
from .governance_liquidity import liquidity_assessment as _liquidity_assessment


_CONDITIONS = (
    "leadership_change", "unfit_person_event", "fit_proof_required", "matching_adjustment",
    "volatility_adjustment", "zero_adjustment_scr_breach", "internal_model", "external_ratings",
    "lending", "mortgage_insurance", "infrastructure_investments", "material_infrastructure",
    "infrastructure_debt", "alternative_valuation", "independent_valuation_requested",
    "outsourcing", "critical_outsourcing", "intragroup_outsourcing", "variable_remuneration",
    "small_non_complex", "combination_approved", "function_combination", "audit_combination",
    "combination_conditions_met", "sustainability_group_exemption", "sustainability_disclosure",
)


def _guidance_assessment(assessment, facts, context):
    """Reuse the declared-evidence contract for an explicitly qualified archive.

    No national applicability or continued future legal force is inferred from
    an archived guideline. Primary profile restrictions remain independently
    enforced by the caller, including future function-combination restrictions.
    """
    if assessment is None:
        return True, {"status": "NOT_ASSESSED"}
    exact_keys(assessment, ("source_version", "applicability_reference", "group", "evidence"),
               "guidance_assessment")
    version = assessment["source_version"]
    require(version in ("EIOPA-BoS-14/253", "BaFin-09/2025"), "source_version",
            "explicit archived governance guideline required", "UNSUPPORTED_RULESET")
    _reference(assessment["applicability_reference"], "applicability_reference")
    national = version == "BaFin-09/2025"
    if national:
        require(context.as_of >= "2025-10-14", "source_version",
                "MaGo09/2025 not applicable before14Oct2025", "UNSUPPORTED_RULESET")
    conditions = {**facts, "group": _declared_bool(assessment["group"], "guidance_assessment.group")}
    profile = effective_resource("profile.json", context)
    table = profile["tables"]["de_mago_controls" if national else "governance_guidance_controls"]
    active = [row[:3] for row in table["rows"] if row[3] == "always" or conditions[row[3]]]
    complete, details = _evidence_inventory(assessment["evidence"], {"rows": active},
                                          assessment["applicability_reference"])
    numeric = {}
    if national:
        for key, value, unit, source in profile["tables"]["de_mago_numeric_requirements"]["rows"]:
            value = number(value, key, 0)
            require(value > 0 and (unit != "count" or float(value).is_integer()), key,
                    "positive requirement and whole person count required")
            numeric[key] = {"value": value, "unit": unit, "source": source}
        minimum = numeric["material_decision_minimum_participants"]["value"]
    else:
        minimum = number(scalar("governance_material_decision_minimum_participants", context),
                         "minimum_participants", 1)
    require(float(minimum).is_integer(), "minimum_participants", "whole participant count required")
    return bool(complete), {**details, "status": "DECLARED_EVIDENCE_INVENTORY",
        "source_version": assessment["source_version"], "group": conditions["group"],
        "applicability_reference": assessment["applicability_reference"],
        "material_decision_minimum_participants": minimum,
        "national_numeric_requirements": numeric,
        "national_profile_reconciliation_required": national,
        "archive_not_before": "2025-10-14" if national else None,
        "actual_decision_participation_verified": False, "legal_applicability_verified": False,
        "primary_profile_restrictions_waived": False,
        "inactive_controls": [row[0] for row in table["rows"]
                              if row[3] != "always" and not conditions[row[3]]],
        "source_notes": table["source_notes"],
        "_sources": details["_sources"] + [s["source_id"] + ":" + s["sha256"]
                                             for s in table["source_bindings"]]}


@calculation("DIR:articles-40-49", "DR:articles-258-275a", unit="indicator")
def governance_evidence_check(evidence: Mapping, conditions: Mapping, *, assessment_reference: str,
                              supervisory_policy_interval_years: float | None = None,
                              non_snc_policy_approval_reference: str | None = None,
                              de_ppp_assessment: Mapping | None = None,
                              guidance_assessment: Mapping | None = None,
                              liquidity_assessment: Mapping | None = None, context: Context):
    """Inventory applicable declared controls and expose versioned review periods.

No references are retrieved, substantive evidence reviewed, or actual calendar
deadlines monitored. Combination eligibility is conditional on external facts.
The optional29d/327d approval changes only the policy-review maximum, not
function-combination approval or any other governance interval.
Optional archived guidance requires its own explicit applicability reference;
omission is NOT_ASSESSED, never a statement that the guidelines do not apply.
Optional2027 liquidity_assessment separates solo/group plans, exemptions and
supervisory measures; no cashflow projection or supervisory decision is made.
"""
    exact_keys(conditions, _CONDITIONS, "conditions")
    facts = {key: _declared_bool(conditions[key], key) for key in _CONDITIONS}
    profile = effective_resource("profile.json", context)
    future = "governance_snc_policy_interval_years" in profile["scalars"]
    approved_non_snc = non_snc_policy_approval_reference is not None
    if approved_non_snc:
        _reference(non_snc_policy_approval_reference, "non_snc_policy_approval_reference")
        require(future and not facts["small_non_complex"], "non_snc_policy_approval_reference",
                "prior Article29d/327d approval requires2027 non-SNC route", "UNSUPPORTED_METHOD")
    if not future:
        require(not any(facts[key] for key in ("small_non_complex", "combination_approved", "sustainability_group_exemption")),
                "conditions", "future governance exemption asserted in historical profile", "UNSUPPORTED_RULESET")
    for child, parent in (("critical_outsourcing", "outsourcing"), ("intragroup_outsourcing", "outsourcing"),
                          ("material_infrastructure", "infrastructure_investments"),
                          ("infrastructure_debt", "infrastructure_investments"),
                          ("audit_combination", "function_combination")):
        require(not facts[child] or facts[parent], child, "requires declared " + parent)
    facts["adjustments"] = facts["matching_adjustment"] or facts["volatility_adjustment"]
    require(not facts["zero_adjustment_scr_breach"] or facts["adjustments"], "zero_adjustment_scr_breach",
            "requires applicable MA or VA")
    facts["individual_sustainability_plan"] = not facts["sustainability_group_exemption"]
    facts["critical_intragroup_outsourcing"] = facts["critical_outsourcing"] and facts["intragroup_outsourcing"]
    rows = profile["tables"]["governance_controls"]["rows"]
    active = [row[:3] for row in rows if row[3] == "always" or facts[row[3]]]
    complete, details = _evidence_inventory(evidence, {"rows": active}, assessment_reference)
    combined = facts["function_combination"]
    combination_allowed = (not combined or facts["combination_conditions_met"] and
        (not future or (not facts["audit_combination"] and
                        (facts["small_non_complex"] or facts["combination_approved"]))))
    periods = {}
    for key in ("governance_policy_interval_years", "governance_tp_validation_interval_years",
                "governance_audit_report_interval_years", "governance_actuarial_report_interval_years"):
        periods[key] = number(scalar(key, context), key, 0)
        require(periods[key] > 0, key, "positive maximum interval required")
    if future and (facts["small_non_complex"] or approved_non_snc):
        periods["governance_policy_interval_years"] = number(scalar("governance_snc_policy_interval_years", context),
                                                            "snc_policy_interval", 0)
        require(periods["governance_policy_interval_years"] > 0, "snc_policy_interval", "positive interval required")
    if supervisory_policy_interval_years is not None:
        interval = number(supervisory_policy_interval_years, "supervisory_policy_interval_years", 0,
                          periods["governance_policy_interval_years"])
        require(interval > 0, "supervisory_policy_interval_years", "positive interval required")
        periods["governance_policy_interval_years"] = interval
    limits = {key: number(scalar(key, context), key, 0) for key in
              ("governance_fit_proof_max_months", "governance_minimum_managers")}
    if future:
        limits["governance_board_lookback_years"] = number(scalar("governance_board_lookback_years", context),
                                                        "governance_board_lookback_years", 0)
        limits["governance_malus_max_share"] = number(scalar("governance_malus_max_share", context),
                                                     "governance_malus_max_share", 0, 1)
    national_complete, national_details = _de_ppp_assessment(de_ppp_assessment, context)
    national_sources = national_details.pop("_sources", [])
    guidance_complete, guidance_details = _guidance_assessment(guidance_assessment, facts, context)
    guidance_sources = guidance_details.pop("_sources", [])
    liquidity_complete, liquidity_details = _liquidity_assessment(liquidity_assessment, facts, context)
    liquidity_sources = liquidity_details.pop("_sources", [])
    return int(bool(complete) and combination_allowed and national_complete and guidance_complete and liquidity_complete), {**details, "conditions": facts,
        "liquidity": liquidity_details,
        "de_ppp": national_details,
        "guidance": guidance_details,
        "non_snc_policy_approval_reference": non_snc_policy_approval_reference,
        "function_combination_allowed_on_declared_facts": combination_allowed,
        "maximum_intervals_years": periods, "prescribed_limits": limits,
        "material_change_policy_update_required": True, "deadlines_monitored": False,
        "actual_staff_assignments_verified": False, "regulatory_total_released": False,
        "scope": "declared_governance_evidence_and_periods_not_substantive_compliance",
        "_sources": details["_sources"] + national_sources + guidance_sources + liquidity_sources + (["DIR:article-29d", "DR:article-327d"] if approved_non_snc else [])
                    + [context.profile_id + ":" + profile["sources"][s]["sha256"]
                                            + ":governance" for s in ("DIR", "DR")]}


@calculation("DR:article-275:2:c", unit="years")
def governance_remuneration_deferral_years(annual_variable: float, annual_total: float, *,
                                          supervisory_exception_denied: bool,
                                          qualification_reference: str, context: Context):
    """Minimum deferral period for an externally qualified relevant staff member.

No prescribed significant-deferred-share percentage is invented. This is not
permission to ignore payment sustainability, vesting or malus/clawback rules.
"""
    _reference(qualification_reference, "qualification_reference")
    denied = _declared_bool(supervisory_exception_denied, "supervisory_exception_denied")
    variable, total = number(annual_variable, "annual_variable", 0), number(annual_total, "annual_total", 0)
    require(variable <= total, "annual_variable", "variable remuneration cannot exceed total")
    minimum = number(scalar("governance_remuneration_deferral_years", context), "deferral_years", 0)
    require(minimum > 0, "deferral_years", "positive minimum required")
    profile = effective_resource("profile.json", context)
    future = "governance_remuneration_exemption_eur" in profile["scalars"]
    exempt = False
    sources, thresholds = [], {}
    if future:
        require(context.currency == "EUR", "currency", "explicit EUR remuneration for printed threshold required",
                "UNSUPPORTED_CURRENCY")
        cap = number(scalar("governance_remuneration_exemption_eur", context), "remuneration_cap", 0)
        denominator = number(scalar("governance_remuneration_share_denominator", context), "share_denominator", 1)
        exempt = (not denied and variable <= cap and
                  Fraction(str(variable)) * Fraction(str(denominator)) <= Fraction(str(total)))
        thresholds = {"amount_eur": cap, "total_share_denominator": denominator}
        sources = ["DR:article-275:2a", "DR:article-275:2b"]
    return (0 if variable == 0 or exempt else minimum), {
        "annual_variable": variable, "annual_total": total, "small_remuneration_exception": exempt,
        "supervisory_exception_denied": denied, "thresholds": thresholds,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "deferred_share_specified": False, "other_remuneration_conditions_waived": False,
        "scope": "minimum_deferral_period_not_payment_or_employment_approval", "_sources": sources}
