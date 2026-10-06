"""Combine prescribed176a screens for an explicitly chosen route, not a credit model."""
from typing import Mapping

from .assigned_credit_numeric import assigned_credit_issuer_financial_screen, assigned_credit_yield_screen
from .core import Context, calculation, effective_resource, exact_keys, require
from .loss_given_default import _known_flag, _reference


def _assessment_evidence(assessment, target_cqs):
    """Validate declared176b evidence, never perform or certify a credit assessment.

    Regular review has no invented numerical frequency. Factor references may
    explain immateriality; the engine does not assign materiality or weights.
    """
    if assessment is None:
        return {"status": "NOT_ASSESSED"}, True
    exact_keys(assessment, ("assigned_cqs", "assessment_reference", "information_reference",
                           "conditions", "factor_references"), "assessment")
    require(assessment["assigned_cqs"] == target_cqs, "assessment.assigned_cqs",
            "externally assigned CQS must match the explicitly selected route", "REVIEW_REQUIRED")
    for key in ("assessment_reference", "information_reference"):
        _reference(assessment[key], "assessment." + key)
    names = ("reliability_and_spread_risk_demonstrable", "all_material_factors_considered",
             "all_relevant_quantitative_qualitative_information_used", "rated_comparables_considered",
             "financial_trends_considered", "procedurally_independent_of_underwriting", "regular_review")
    exact_keys(assessment["conditions"], names, "assessment.conditions")
    flags = {key: _known_flag(assessment["conditions"][key], "assessment.conditions." + key) for key in names}
    factors = ("competitive_position", "management_quality", "financing_policy", "country_risk",
               "covenants", "financial_history_and_operating_age", "size_and_diversification",
               "issuance_impact", "ownership_structure", "business_model_complexity")
    exact_keys(assessment["factor_references"], factors, "assessment.factor_references")
    for key in factors:
        _reference(assessment["factor_references"][key], "assessment.factor_references." + key)
    return {"status": "DECLARED_EVIDENCE_CHECKED_CONTENT_UNVERIFIED",
            "assigned_cqs": target_cqs, "assessment_reference": assessment["assessment_reference"],
            "information_reference": assessment["information_reference"], "conditions": flags,
            "factor_references": dict(assessment["factor_references"])}, all(flags.values())


@calculation("DR:article-176a:1-9", unit="indicator")
def assigned_credit_eligibility_screen(issuer_financials: Mapping, yield_inputs: Mapping,
        conditions: Mapping, *, target_cqs: str, qualification_reference: str, context: Context,
        assessment: Mapping | None = None):
    """Return eligibility for the CHOSEN route, never an internally modelled CQS.

    Route3 excludes already assigned176a(1)-CQS2 instruments, not every instrument
    that might hypothetically qualify for2. Choice and substantive assessments
    are explicit external inputs. Existing numeric screens remain authoritative
    for their limited arithmetic and profile-specific analyst overrides.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(target_cqs, str) and target_cqs in ("2", "3"), "target_cqs",
            "explicit176a route2 or3 required", "UNSUPPORTED_METHOD")
    table = effective_resource("profile.json", context)["tables"]["assigned_credit_eligibility_conditions"]
    rows = [row for row in table["rows"] if row[1] in ("both", target_cqs)]
    names = [row[0] for row in rows]
    require(bool(names) and len(set(names)) == len(names), "assigned_credit_eligibility_conditions",
            "nonempty unique route controls required", "RESOURCE_INTEGRITY")
    exact_keys(conditions, names, "conditions")
    declared = {key: _known_flag(conditions[key], key) for key in names}
    assessment_audit, assessment_met = _assessment_evidence(assessment, target_cqs)
    exact_keys(issuer_financials, ("financial_years", "latest_financials",
               "eligible_currency_revenue_share", "years_without_credit_event"), "issuer_financials")
    exact_keys(yield_inputs, ("yield_observations", "index_yields", "current_issue_id"), "yield_inputs")
    financial = assigned_credit_issuer_financial_screen(**issuer_financials,
        qualification_reference=qualification_reference, context=context)
    yields = assigned_credit_yield_screen(**yield_inputs, target_cqs=target_cqs,
        qualification_reference=qualification_reference, context=context)
    return int(all(declared.values()) and assessment_met and financial.value == 1 and yields.value == 1), {
        "target_cqs": target_cqs, "declared_conditions": declared,
        "assessment_evidence": assessment_audit,
        "financial_screen": {"value": financial.value, "details": financial.details},
        "yield_screen": {"value": yields.value, "details": yields.details},
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "internal_assessment_performed": False, "substantive_article176b_verification_performed": False,
        "credit_quality_step_assigned": False, "automatic_route_selection_performed": False,
        "scope": "chosen176a_route_numeric_and_declared_eligibility_not_rating_or_supervisory_approval",
        "_sources": [*(row[2] for row in rows), *financial.sources, *yields.sources,
                     *(["DR:article-176b:a-i"] if assessment is not None else [])]}
