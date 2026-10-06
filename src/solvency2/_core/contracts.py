"""Narrow contract timing/screens, not a complete recognition or boundary decision."""
from datetime import date
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, require


def _reference(reference, field):
    require(isinstance(reference, str) and bool(reference.strip()), field,
            "nonempty external evidence reference required", "MISSING_INPUT")


def _date(value, field):
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        require(False, field, "canonical ISO YYYY-MM-DD date required")
    require(value == parsed.isoformat(), field, "canonical ISO YYYY-MM-DD date required")
    return parsed


@calculation("DR:article-17", unit="indicator")
def contract_recognition_due(contract_party_date: str, coverage_start_date: str, *,
                              evidence_reference: str, context: Context):
    """Has the first recognition time arrived? This does not reverse later derecognition."""
    party = _date(contract_party_date, "contract_party_date")
    cover = _date(coverage_start_date, "coverage_start_date")
    _reference(evidence_reference, "evidence_reference")
    first = min(party, cover)
    return int(date.fromisoformat(context.as_of) >= first), {
        "contract_party_date": party.isoformat(), "coverage_start_date": cover.isoformat(),
        "recognition_date": first.isoformat(), "evidence_reference": evidence_reference,
        "evidence_status": "EXTERNAL_UNVERIFIED", "scope": "initial_recognition_timing_only"}


@calculation("DR:article-18:3", unit="indicator")
def contract_boundary_exclusion(*, coverage_after_qualifying_right: bool | None,
                                 premium_payment_enforceable: bool | None,
                                 assessment_reference: str, context: Context):
    """Only the Article 18(3) negative screen; zero never proves contract membership.

    'After' concerns coverage, not payment dates. Qualification of unilateral
    rights, repricing and legal enforceability is supplied externally.
    """
    facts = {"coverage_after_qualifying_right": coverage_after_qualifying_right,
             "premium_payment_enforceable": premium_payment_enforceable}
    for field, value in facts.items():
        require(value is None or isinstance(value, bool), field, "boolean or None required")
    _reference(assessment_reference, "assessment_reference")
    if coverage_after_qualifying_right is False or premium_payment_enforceable is True:
        excluded = 0
    else:
        require(coverage_after_qualifying_right is not None and premium_payment_enforceable is not None,
                "boundary_facts", "unknown facts prevent exclusion decision", "REVIEW_REQUIRED")
        excluded = 1
    return excluded, {**facts, "assessment_reference": assessment_reference,
                      "assessment_status": "EXTERNAL_UNVERIFIED",
                      "decision": "EXCLUDED_BY_ARTICLE_18_3" if excluded else "NOT_EXCLUDED_BY_ARTICLE_18_3",
                      "scope": "article_18_3_screen_only_not_contract_membership"}

@calculation("DR:article-17", unit="indicator")
def obligation_derecognition_condition(obligation_status: str | None, *,
                                       evidence_reference: str, context: Context):
    """Qualified obligation state only, never automatic contract-end derecognition.

    A terminated policy can retain claims obligations. The supplied status must
    concern the specific obligation assessed, and remains externally unverified.
    """
    _reference(evidence_reference, "evidence_reference")
    require(obligation_status is not None, "obligation_status", "obligation state unresolved", "REVIEW_REQUIRED")
    require(isinstance(obligation_status, str), "obligation_status", "explicit status code required")
    require(obligation_status != "UNKNOWN", "obligation_status", "obligation state unresolved", "REVIEW_REQUIRED")
    states = {"EXTINGUISHED", "DISCHARGED", "CANCELLED", "EXPIRED"}
    require(obligation_status in states | {"ACTIVE"}, "obligation_status", "unknown obligation status")
    profile = effective_resource("profile.json", context)
    return int(obligation_status in states), {
        "obligation_status": obligation_status, "evidence_reference": evidence_reference,
        "evidence_status": "EXTERNAL_UNVERIFIED", "automatic_derecognition": False,
        "scope": "specific_obligation_state_condition_not_contract_coverage_end",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-17"]}


@calculation("DR:article-18:3", "CB_GUIDANCE:guideline-2", unit="indicator")
def contract_unilateral_right(right_type: str, facts: Mapping[str, bool | None], *,
                               assessment_reference: str, context: Context):
    """Guideline2 unilateral-right screen, not full contract-boundary membership.

    Restrictions must be externally qualified effective restrictions, including
    the Article18 economic-effect assessment. Relevant third parties exclude
    supervisors/governance bodies. Mere reputation or competition is not a veto.
    Full risk reflection and the profile-specific life repricing clause remain
    separate for an amendment right, even when this screen returns1.
    """
    require(isinstance(right_type, str) and right_type in {"terminate", "reject_premium", "amend"},
            "right_type", "supported contractual right required", "UNSUPPORTED_PARAMETER")
    keys = ("right_exists", "policyholder_or_third_party_restriction", "national_law_restriction",
            "sole_policyholder_or_beneficiary_decision", "claim_event_condition")
    exact_keys(facts, keys, "facts")
    for key in keys:
        require(facts[key] is None or isinstance(facts[key], bool), key, "boolean or None required")
    _reference(assessment_reference, "assessment_reference")
    restriction_keys = ["policyholder_or_third_party_restriction", "national_law_restriction",
                        "sole_policyholder_or_beneficiary_decision" if right_type == "amend"
                        else "claim_event_condition"]
    excluded = facts["right_exists"] is False or any(facts[key] is True for key in restriction_keys)
    if not excluded:
        require(all(facts[key] is not None for key in ["right_exists", *restriction_keys]),
                "facts", "unresolved effective right/restriction", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return int(not excluded), {"right_type": right_type, "facts": dict(facts),
        "assessment_reference": assessment_reference, "assessment_status": "EXTERNAL_UNVERIFIED",
        "full_risk_reflection_assessed": False, "contract_membership_decided": False,
        "scope": "guideline2_unilateral_right_screen_only",
        "guidance_legal_applicability": "PENDING",
        "source_warning": profile["sources"]["CB_GUIDANCE"].get("source_warning"),
        "_sources": [context.profile_id + ":" + profile["sources"]["CB_GUIDANCE"]["sha256"] + ":guideline-2"]}
