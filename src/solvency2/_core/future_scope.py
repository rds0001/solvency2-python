"""Explicit2027 scope gates; no supervisory decision or invented capital relief."""
from typing import Mapping
import math

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory, _reference


@calculation("DIR:article-212:1:f", unit="indicator")
def group_insurance_holding_conditions_2027(indicator_shares: Mapping,
        other_supervisory_shares: Mapping, conditions: Mapping, *,
        qualification_reference: str, context: Context):
    """Declared holding criteria, not an automatic group or entity classification.

    Shares must use the precisely qualified212(1)f(vi) consolidated perimeter.
    Do not cap ratios at1: offsetting consolidated amounts can change ratios.
    Ongoing satisfaction and the other legal conditions remain external facts.
    """
    _reference(qualification_reference, "qualification_reference")
    exact_keys(indicator_shares, ("equity", "assets", "revenue", "employees"), "indicator_shares")
    require(isinstance(other_supervisory_shares, Mapping), "other_supervisory_shares",
            "explicit extra supervisory indicators, or empty mapping, required")
    shares = {key: number(value, "indicator_shares." + key) for key, value in indicator_shares.items()}
    extra = {}
    for key, value in other_supervisory_shares.items():
        _reference(key, "supervisory_indicator")
        extra[key] = number(value, "other_supervisory_shares." + key)
    keys = ("parent_undertaking", "not_excluded_regulated_undertaking", "not_mixed_or_financial_holding",
            "insurance_or_reinsurance_subsidiary", "qualifying_principal_activity", "continuous_indicator_basis")
    exact_keys(conditions, keys, "conditions")
    facts = {key: _declared_bool(conditions[key], key) for key in keys}
    limit = number(scalar("group_insurance_holding_indicator_share", context), "indicator_limit", 0, 1)
    share_met = any(value > limit for value in (*shares.values(), *extra.values()))
    return int(all(facts.values()) and share_met), {
        "indicator_shares": shares, "other_supervisory_shares": extra, "conditions": facts,
        "strict_indicator_limit": limit, "indicator_condition_met": share_met,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "declared_continuous_holding_conditions_not_supervisory_classification"}


@calculation("DIR:article-233b", "DR:article-336a")
def group_long_term_equity_limit_2027(full_amounts: Mapping, proportional_amounts: Mapping, *,
        supervisory_recalculation_required: bool, recalculated_full_amount: float | None,
        qualification_reference: str, context: Context):
    """Method1/combined LTE cap, not group SCR or an automatic classification.

    Article335(1)a amounts enter in full,335(1)c proportionally. On a qualified
    supervisory request replace only1(a) with the externally recomputed amount.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(full_amounts, Mapping) and isinstance(proportional_amounts, Mapping),
            "amounts", "explicit disjoint entity mappings required")
    require(not set(full_amounts) & set(proportional_amounts), "amounts", "entity appears in both scopes")
    full, proportional = {}, {}
    for key, value in full_amounts.items():
        _reference(key, "entity_id")
        full[key] = number(value, key, 0)
    for key, row in proportional_amounts.items():
        _reference(key, "entity_id")
        exact_keys(row, ("amount", "share"), key)
        proportional[key] = number(row["amount"], key + ".amount", 0) * number(row["share"], key + ".share", 0, 1)
    recalculate = _declared_bool(supervisory_recalculation_required, "supervisory_recalculation_required")
    original = number(math.fsum(full.values()), "full_sum", 0)
    if recalculate:
        selected = number(recalculated_full_amount, "recalculated_full_amount", 0)
    else:
        require(recalculated_full_amount is None, "recalculated_full_amount", "unused recalculation input")
        selected = original
    value = number(math.fsum([selected, *proportional.values()]), "group_limit", 0)
    return value, {"standalone_full_sum": original, "selected_full_amount": selected,
        "proportional_contributions": proportional, "supervisory_recalculation_required": recalculate,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "maximum_group_long_term_equity_amount_not_capital_or_classification"}


@calculation("DIR:article-152aa:1", unit="indicator")
def significant_cross_border_activity_2027(host_gross_premiums: float, *,
        small_non_complex: bool, host_authority_significant: bool,
        qualification_reference: str, context: Context):
    """One host state's establishment AND services premiums; strict EUR threshold.

    The host authority's materiality decision is explicit, never inferred from
    market shares. SNC exclusion applies to both branches. This definition is
    not the different significant-branch screen in delegated Article354.
    """
    _reference(qualification_reference, "qualification_reference")
    require(context.currency == "EUR", "currency", "EUR-qualified premiums required", "UNSUPPORTED_CURRENCY")
    premium = number(host_gross_premiums, "host_gross_premiums", 0)
    snc = _declared_bool(small_non_complex, "small_non_complex")
    significant = _declared_bool(host_authority_significant, "host_authority_significant")
    limit = number(scalar("cross_border_significant_premium_eur", context), "premium_limit", 0)
    require(limit > 0, "premium_limit", "positive limit required")
    return int(not snc and (premium > limit or significant)), {
        "host_gross_premiums": premium, "strict_premium_limit": limit,
        "small_non_complex": snc, "host_authority_significant": significant,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "supervisory_cooperation_performed": False}


@calculation("DR:article-215a", unit="indicator")
def public_counter_guarantee_conditions_2027(conditions: Mapping, *,
        qualification_reference: str, context: Context):
    """Article215a equivalence gate, not guarantee valuation or zero capital.

    Only the directness requirement is waived for the counter-guarantee;
    original guarantee requirements and all other counter-guarantee conditions
    remain. Any downstream Article180/192 treatment needs its own scope checks.
    """
    _reference(qualification_reference, "qualification_reference")
    keys = ("counter_guarantor_article180_2_first_subparagraph", "all_credit_risk_covered",
            "original_guarantee_article215", "counter_guarantee_article215_except_directness",
            "robust_protection_no_lower_effectiveness_evidence")
    exact_keys(conditions, keys, "conditions")
    facts = {key: _declared_bool(conditions[key], key) for key in keys}
    return int(all(facts.values())), {"conditions": facts,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "guarantee_amount_determined": False, "capital_relief_determined": False,
        "scope": "declared_article215a_equivalence_conditions_only"}


@calculation("DIR:articles-29c-29e", unit="indicator")
def proportionality_application_evidence_2027(evidence: Mapping, *, route: str,
        measure_list_changed: bool, measure_ceased: bool, supervisory_restriction: bool,
        qualification_reference: str, context: Context):
    """Application/notification inventory, separate from annual size screens.

    The qualification reference identifies the actual measure, classification,
    specific approval/conditions or pre-existing2025 transitional entitlement.
    Metadata exposes authority periods without calculating a decision deadline
    or manufacturing approval through silence. Fiscal-year counting is external.
    """
    _reference(qualification_reference, "qualification_reference")
    require(route in ("snc", "non_snc", "legacy"), "route", "explicit application route required")
    changed = _declared_bool(measure_list_changed, "measure_list_changed")
    ceased = _declared_bool(measure_ceased, "measure_ceased")
    restricted = _declared_bool(supervisory_restriction, "supervisory_restriction")
    profile = effective_resource("profile.json", context)
    active = {"always", route}
    if route == "snc" and changed:
        active.add("snc_changed")
    if route == "non_snc" and ceased:
        active.add("non_snc_ceased")
    rows = profile["tables"]["proportionality_application_controls"]["rows"]
    complete, details = _evidence_inventory(evidence, {"rows": [r[:3] for r in rows if r[3] in active]},
                                          qualification_reference)
    periods = {key: number(scalar(key, context), key, 0) for key in (
        "proportionality_scr_lookahead_months", "proportionality_no_strategy_change_years",
        "proportionality_approval_months", "proportionality_early_approval_months",
        "proportionality_snc_notification_years", "proportionality_legacy_max_financial_years")}
    require(all(value > 0 for value in periods.values()), "periods", "positive periods required")
    return int(bool(complete) and not restricted), {**details, "route": route,
        "measure_list_changed": changed, "measure_ceased": ceased,
        "supervisory_restriction": restricted, "periods": periods,
        "temporal_rules": profile["tables"]["proportionality_application_dates"]["rows"],
        "approval_deadline_first_information_request_suspends_only": True,
        "approval_granted": False, "calendar_or_fiscal_years_counted": False,
        "scope": "declared_application_and_notification_evidence_not_eligibility_or_approval"}
