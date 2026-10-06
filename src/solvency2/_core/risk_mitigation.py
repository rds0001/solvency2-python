"""Article208/209 recognition boundaries, not valuation or legal certification."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .loss_given_default import _known_flag, _reference


def _finite_ids(ids, contracts):
    """An empty declaration means no finite/similar transfers, not unknown scope."""
    require(isinstance(ids, (list, tuple)), "finite_reinsurance_ids", "explicit ID sequence required")
    require(all(isinstance(k, str) and k in contracts for k in ids), "finite_reinsurance_ids", "known contract IDs required")
    require(len(set(ids)) == len(ids), "finite_reinsurance_ids", "duplicate IDs")
    return set(ids)


@calculation("DR:article-208", "DR:article-209", "DR:article-211", unit="factor")
def risk_mitigation_recognition_factor(remaining_months: float, conditions: Mapping, *,
        purpose: str, instrument_kind: str, finite_or_similar: bool | None,
        replacement: Mapping | None = None, proportional_factor: float | None = None,
        counterparty_factor: float = 1, residential_guarantee_payment_months: float | None = None,
        qualification_reference: str, context: Context):
    """Full, excluded, or externally qualified time-proportionate recognition.

    Proportional_factor is required only for a qualified short contract without
    valid209(3) replacement. Its exposure-dependent time basis is external.
    Finite/similar arrangements are excluded from volume/USP even if209 passes.
    Scenario valuation must already reflect only the actually transferred risk;
    this factor is NOT applied blindly to recoverables, LGD or capital amounts.
    counterparty_factor may bind the separately calculated211 haircut. Default1
    explicitly declares full counterparty recognition, never verifies it.
    Optional residential mortgage guarantee payment window implements only
    future215(c)(iii)/(d); all other guarantee criteria remain in qualification.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(purpose, str) and purpose in {"scenario", "premium_reserve", "usp"}, "purpose", "supported recognition purpose required")
    require(isinstance(instrument_kind, str) and instrument_kind in {"financial", "reinsurance", "spv"}, "instrument_kind", "qualified instrument type required")
    finite = _known_flag(finite_or_similar, "finite_or_similar")
    counterparty = number(counterparty_factor, "counterparty_factor", 0, 1)
    require(instrument_kind != "financial" or counterparty == 1, "counterparty_factor",
            "211 counterparty reduction applies to reinsurance/SPV, not financial instruments")
    months = number(remaining_months, "remaining_months", 0)
    keys = ("legal_enforceability", "effectiveness_actions", "ongoing_monitoring", "direct_claim",
            "no_double_count", "other_section10_conditions")
    exact_keys(conditions, keys, "conditions")
    facts = {k: _known_flag(conditions[k], k) for k in keys}
    horizon = number(scalar("mitigation_full_horizon_months", context), "horizon", 0)
    require(horizon > 0, "horizon", "positive horizon required")
    renewal_ok = False
    renewal = None
    if replacement is not None:
        bools = ("written_policy", "controlled_future_events", "past_practice_consistent", "liquidity_sufficient",
                 "cost_risk_in_scr", "management_actions_consistent", "material_event_exception")
        exact_keys(replacement, (*bools, "interval_days", "original_months"), "replacement")
        renewal = {k: _known_flag(replacement[k], "replacement." + k) for k in bools}
        days = number(replacement["interval_days"], "interval_days", 0)
        original = number(replacement["original_months"], "original_months", 0)
        minimum = number(scalar("mitigation_original_" + ("financial" if instrument_kind == "financial" else "reinsurance") + "_months", context), "original_minimum", 0)
        weekly = number(scalar("mitigation_replacement_interval_days", context), "weekly_interval", 0)
        renewal_ok = (all(renewal[k] for k in bools if k != "material_event_exception")
                      and (days >= weekly or renewal["material_event_exception"]) and original >= minimum)
        renewal.update(interval_days=days, original_months=original, minimum_original_months=minimum,
                       minimum_interval_days=weekly, conditions_satisfied=renewal_ok)
    guarantee = None
    if residential_guarantee_payment_months is not None:
        require(context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1", "residential_guarantee_payment_months",
                "Article215 residential window unavailable historically", "UNSUPPORTED_RULESET")
        require(instrument_kind == "financial", "instrument_kind", "explicit financial guarantee route required", "UNSUPPORTED_METHOD")
        payment = number(residential_guarantee_payment_months, "residential_guarantee_payment_months", 0)
        maximum = number(scalar("residential_guarantee_payment_max_months", context), "guarantee_payment_maximum", 0)
        require(maximum > 0, "guarantee_payment_maximum", "positive time limit required")
        guarantee = {"payment_months": payment, "maximum_months": maximum,
                     "numeric_timing_satisfied": payment <= maximum,
                     "residential_mortgage_and_other_criteria_status": "EXTERNAL_UNVERIFIED"}
    qualified = all(facts.values()) and (guarantee is None or guarantee["numeric_timing_satisfied"])
    excluded = finite and purpose in {"premium_reserve", "usp"}
    if not qualified or excluded:
        require(proportional_factor is None, "proportional_factor", "ineligible arrangement cannot use a time factor")
        value, route = 0, "FINITE_EXCLUDED" if excluded else "QUALITATIVE_CONDITIONS_FAILED"
    elif months >= horizon or renewal_ok:
        require(proportional_factor is None, "proportional_factor", "full recognition must not have an unused time factor")
        value, route = 1, "FULL_TERM" if months >= horizon else "QUALIFIED_REPLACEMENT"
    else:
        require(proportional_factor is not None, "proportional_factor", "qualified exposure-dependent time proportion required", "REVIEW_REQUIRED")
        value = number(proportional_factor, "proportional_factor", 0, 1)
        require(months > 0 or value == 0, "proportional_factor", "expired unrenewed cover cannot receive positive recognition")
        route = "EXTERNAL_TIME_PROPORTION"
    return value * counterparty, {"route": route, "purpose": purpose, "instrument_kind": instrument_kind,
        "time_and_purpose_factor": value, "counterparty_factor": counterparty,
        "finite_or_similar": finite, "conditions": facts, "remaining_months": months,
        "full_horizon_months": horizon, "replacement": renewal, "proportional_factor": proportional_factor,
        "residential_guarantee": guarantee,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "actual_risk_transfer_or_legal_effectiveness_verified": False,
        "scope": "recognition_factor_not_contract_valuation",
        "_sources": ["DR:article-215"] if guarantee is not None else []}


@calculation("DR:article-211", unit="factor")
def reinsurance_counterparty_recognition_factor(counterparty_type: str, coverage_ratio: float | None, *,
        conditions: Mapping, months_since_breach: float | None = None,
        credit_quality_step: int | None = None, qualification_reference: str, context: Context):
    """Prescribed211 eligibility/haircut; not PD, LGD or recoverable valuation.

    Coverage is SCR/local-equivalent solvency coverage for the insurer route,
    or assets/equivalent eligible amount divided by aggregate maximum SPV
    exposure. Solvency dates, equivalence, legal status and credible restoration
    evidence are external. Months are completed regulatory calendar periods;
    at the expiry of6/3months an unresolved shortfall receives zero recognition.
    Non-equivalent insurers use the separate CQS route, not an invented SCR.
    """
    _reference(qualification_reference, "qualification_reference")
    kinds = {"insurer_scr", "insurer_equivalent", "insurer_non_equivalent", "spv", "public_scheme"}
    require(isinstance(counterparty_type, str) and counterparty_type in kinds,
            "counterparty_type", "explicit211 counterparty route required")
    keys = ("legal_and_equivalence_conditions", "post_contract_breach", "mcr_met", "restoration_expected")
    exact_keys(conditions, keys, "conditions")
    facts = {k: _known_flag(conditions[k], k) for k in keys}
    profile = effective_resource("profile.json", context)
    if counterparty_type == "public_scheme":
        require(profile["methods"].get("default_lgd_rules") == "2027", "counterparty_type",
                "public-interest scheme211(2a) is a2027 route", "UNSUPPORTED_RULESET")
    rating_route = counterparty_type == "insurer_non_equivalent"
    ordinary_only = rating_route or counterparty_type == "public_scheme"
    if rating_route:
        rating = number(credit_quality_step, "credit_quality_step", 0, 6)
        require(rating.is_integer(), "credit_quality_step", "integer CQS required")
        cap = number(scalar("mitigation_non_equivalent_max_cqs", context), "maximum_cqs", 0, 6)
        require(cap.is_integer(), "maximum_cqs", "integer CQS limit required")
    else:
        require(credit_quality_step is None, "credit_quality_step", "unused CQS for this route")
        rating, cap = None, None
    if ordinary_only:
        require(coverage_ratio is None and months_since_breach is None, "coverage_ratio", "no invented SCR/SPV ratio on this route")
        require(not facts["post_contract_breach"], "post_contract_breach",
                "a separately qualified SCR-breach route is required for211(3)", "REVIEW_REQUIRED")
        ratio, months, limit = None, None, None
        allowed = facts["legal_and_equivalence_conditions"] and (not rating_route or (rating <= cap and facts["mcr_met"]))
        value, route = int(allowed), "ORDINARY_ELIGIBILITY" if allowed else "NOT_ELIGIBLE"
    else:
        ratio = number(coverage_ratio, "coverage_ratio", 0)
        limit = number(scalar("mitigation_spv_restoration_months" if counterparty_type == "spv" else
                              "mitigation_insurer_restoration_months", context), "restoration_months", 0)
        require(limit > 0, "restoration_months", "positive restoration period required")
        months = None if months_since_breach is None else number(months_since_breach, "months_since_breach", 0)
        if facts["post_contract_breach"] and ratio < 1:
            require(months is not None, "months_since_breach", "breach age required", "MISSING_INPUT")
        if not facts["legal_and_equivalence_conditions"] or (counterparty_type != "spv" and not facts["mcr_met"]):
            value, route = 0, "LEGAL_OR_MCR_FAILURE"
        elif ratio >= 1:
            value, route = 1, "FULL_COVERAGE"
        elif facts["post_contract_breach"] and facts["restoration_expected"] and months < limit:
            value, route = ratio, "TEMPORARY_PROPORTIONAL_RECOGNITION"
        else:
            value, route = 0, "SHORTFALL_NOT_RECOGNISABLE"
    return value, {"counterparty_type": counterparty_type, "coverage_ratio": ratio,
        "credit_quality_step": rating, "maximum_credit_quality_step": cap, "conditions": facts,
        "months_since_breach": months, "restoration_limit_months": limit, "route": route,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "article211_recognition_only_not_recoverables_PD_or_LGD"}
