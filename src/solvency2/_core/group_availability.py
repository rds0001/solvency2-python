"""DR330 amount components: no inferred availability, consolidation or capital allocation."""
from fractions import Fraction
import sys
from collections.abc import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _reference(value):
    require(isinstance(value, str) and bool(value.strip()), "qualification_reference",
            "external group scope and amount qualification required", "MISSING_INPUT")


def _amount(value, field):
    require(abs(value) <= Fraction(str(sys.float_info.max)), field,
            "group amount outside finite range", "REVIEW_REQUIRED")
    result = float(value)
    require(not value or result != 0, field, "nonzero group amount lost to underflow", "REVIEW_REQUIRED")
    return result


@calculation("DR:article-330:6:b")
def group_model_scr_contribution(entity: str, model_outputs: Mapping, *,
                                 complete_scope_confirmed: bool, model_reference: str,
                                 qualification_reference: str, context: Context):
    """Apply externally supplied model percentages; never develop an insurer model.

    The full declared entity set is checked before selecting one contribution.
    A1e-12 numerical sum tolerance is not regulatory materiality. Percentages
    are never renormalised, and neither ownership weights nor the future6a
    standard-formula cap are applied to this separate6b branch.
    """
    _reference(qualification_reference)
    require(isinstance(model_reference, str) and bool(model_reference.strip()), "model_reference",
            "versioned external model and approved scope reference required", "MISSING_INPUT")
    require(complete_scope_confirmed is not None, "complete_scope_confirmed",
            "external model entity scope unresolved", "REVIEW_REQUIRED")
    require(isinstance(complete_scope_confirmed, bool), "complete_scope_confirmed", "explicit boolean required")
    require(complete_scope_confirmed, "complete_scope_confirmed", "complete external scope required", "MISSING_INPUT")
    require(isinstance(model_outputs, Mapping) and bool(model_outputs), "model_outputs", "nonempty entity mapping required")
    require(all(isinstance(key, str) and bool(key.strip()) for key in model_outputs),
            "model_outputs", "nonempty entity IDs required")
    require(isinstance(entity, str) and entity in model_outputs, "entity", "selected entity missing", "MISSING_INPUT")
    values = {}
    for key, row in model_outputs.items():
        exact_keys(row, ("scr", "allocation_share"), key)
        scr = number(row["scr"], key + ".scr", 0)
        share = number(row["allocation_share"], key + ".allocation_share")
        require(0 <= share <= 1, key + ".allocation_share",
                "signed or above-one allocations outside supported branch", "UNSUPPORTED_METHOD")
        values[key] = {"scr": scr, "allocation_share": share}
    target = number(scalar("group_model_allocation_total", context), "allocation_total", 0)
    require(target > 0, "allocation_total", "positive allocation total required")
    exact_sum = sum((Fraction(str(row["allocation_share"])) for row in values.values()), Fraction(0))
    difference = exact_sum - Fraction(str(target))
    tolerance = Fraction(1, 10**12)
    require(abs(difference) <= tolerance, "allocation_shares", "external percentages do not sum to required total")
    selected = values[entity]
    value = _amount(Fraction(str(selected["scr"])) * Fraction(str(selected["allocation_share"])), "contribution")
    profile = effective_resource("profile.json", context)
    return value, {"entity": entity, "model_outputs": values, "share_sum": float(exact_sum),
        "required_share_sum": target, "sum_difference": float(difference), "sum_tolerance": float(tolerance),
        "renormalised": False, "ownership_share_applied": False, "standard_formula_cap_applied": False,
        "model_reference": model_reference, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "model_or_approval_verified": False,
        "complete_scope_confirmed": complete_scope_confirmed,
        "scope": "external_model_contribution_not_model_development_or_group_own_funds_approval",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-330-6-b"]}


@calculation("DR:article-330:5", unit="currency")
def group_nonavailable_own_funds_cap(amount: float, scr_contribution: float, *,
                                    qualification_reference: str, context: Context,
                                    related_insurer_scr: float | None = None):
    """Cap ONE externally qualified availability scope, without repeating the cap.

    The caller must not re-use one entity contribution across separate items
    and sum the individual results. This is neither an Article330(4) exemption
    nor a computation of total available group own funds.
    Historical DIR222(4) additionally limits its qualified(2)/(3)pool to the
    related insurer SCR. That optional scope is not imposed on other pools,
    nor carried into the future wording which instead uses the contribution.
    """
    _reference(qualification_reference)
    own_funds = number(amount, "amount", 0)
    contribution = number(scr_contribution, "scr_contribution", 0)
    value = min(own_funds, contribution)
    profile = effective_resource("profile.json", context)
    sources = [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-330-5"]
    related_cap = None
    if related_insurer_scr is not None:
        require(profile.get("methods", {}).get("group_rules") != "2027", "related_insurer_scr",
                "future222(4) uses the contribution, not this historical extra cap", "UNSUPPORTED_METHOD")
        related_cap = number(related_insurer_scr, "related_insurer_scr", 0)
        value = min(value, related_cap)
        sources.append("DIR:article-222:4")
    return value, {"amount": own_funds, "scr_contribution": contribution,
        "related_insurer_scr_cap": related_cap,
        "historical_article222_pool_scope_declared": related_cap is not None,
        "excluded_amount": _amount(Fraction(str(own_funds)) - Fraction(str(value)), "excluded_amount"),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "availability_determined": False, "share_applied": False, "tier_allocation_performed": False,
        "scope": "single_qualified_nonavailable_amount_cap_not_total_group_eligibility",
        "reuse_warning": "Do not reuse one SCR contribution to release multiple independent amounts.",
        "_sources": sources}


@calculation("DR:article-330:4a", unit="currency")
def group_minority_excess_2027(eligible_own_funds_net: float, other_nonavailable_own_funds_net: float,
                               scr_contribution: float, parent_subscribed_capital_share: float, *,
                               qualification_reference: str, context: Context):
    """Literal 2027 minority formula, on explicitly pre-qualified net amounts.

    Both own-funds inputs exclude intra-group subordinated liabilities and
    ancillary own funds. The other-nonavailable input also excludes paragraph4
    items. A negative formula result is NOT an automatic own-funds credit.
    """
    profile = effective_resource("profile.json", context)
    require(profile.get("methods", {}).get("group_rules") == "2027", "profile",
            "Article330(4a) formula belongs only to the future profile", "UNSUPPORTED_RULESET")
    _reference(qualification_reference)
    funds = number(eligible_own_funds_net, "eligible_own_funds_net", 0)
    unavailable = number(other_nonavailable_own_funds_net, "other_nonavailable_own_funds_net", 0)
    require(unavailable <= funds, "other_nonavailable_own_funds_net",
            "qualified unavailable subset cannot exceed own funds on the same net basis")
    contribution = number(scr_contribution, "scr_contribution", 0)
    share = number(parent_subscribed_capital_share, "parent_subscribed_capital_share", 0, 1)
    threshold = max(contribution, unavailable)
    difference = Fraction(str(funds)) - Fraction(str(threshold))
    minority_share = 1 - Fraction(str(share))
    value = _amount(difference * minority_share, "minority_excess")
    return value, {"eligible_own_funds_net": funds, "other_nonavailable_own_funds_net": unavailable,
        "scr_contribution": contribution, "binding_threshold": threshold,
        "parent_subscribed_capital_share": share, "minority_share": float(minority_share),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "net_basis_verified": False, "floor_applied": False, "own_funds_adjustment_applied": False,
        "negative_result_requires_interpretation": value < 0,
        "share_basis": "direct_indirect_subscribed_capital_not_inferred_voting_rights",
        "scope": "literal_2027_minority_excess_not_automatic_group_own_funds_adjustment",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-330-4a"]}


@calculation("DR:article-330:1:c", unit="indicator")
def group_own_funds_transfer_timing_screen(months_to_availability: float, *,
                                           qualification_reference: str, context: Context):
    """Check only the declared nine-month horizon, not effective availability."""
    _reference(qualification_reference)
    months = number(months_to_availability, "months_to_availability", 0)
    profile = effective_resource("profile.json", context)
    horizon = number(profile["scalars"]["group_own_funds_transfer_months"]["value"], "horizon_months", 0)
    return int(months <= horizon), {"months_to_availability": months, "horizon_months": horizon,
        "boundary_inclusive": True, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "effective_availability_verified": False,
        "scope": "declared_transfer_timing_only_not_full_group_own_funds_availability",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-330-1-c"]}


@calculation("DR:article-331:5", "DR:article-332:3", "DR:article-333:4", unit="indicator")
def group_pre_acquisition_scr_exception_2027(related_financial_years: float, *, issued_before_joining: bool,
                                             included_in_group_calculation: bool,
                                             qualification_reference: str, context: Context,
                                             group_supervision_years: float | None = None,
                                             orsa_support_confirmed: bool | None = None,
                                             issuer_type: str = "eu_insurer"):
    """Future pre-acquisition exception with an explicit issuer-specific effect.

    The elapsed FINANCIAL-year measure is externally qualified. This screen
    does not rewrite MCR, assign a tier, or waive other own-funds conditions.
    Three YEARS of group supervision and the prescribed forward ORSA evidence
    are additional mandatory gates. Insurers use331/332's solo-SCR definition;
    qualified intermediate holdings/ancillary subsidiaries instead use333(4)'s
    temporary disapplication of333(2)(a). These are not interchangeable effects.
    """
    profile = effective_resource("profile.json", context)
    require(profile.get("methods", {}).get("group_rules") == "2027", "profile",
            "Article331(5) exception belongs only to the future profile", "UNSUPPORTED_RULESET")
    _reference(qualification_reference)
    issuer_articles = {"eu_insurer": "331-5", "third_country_insurer": "332-3",
                       "intermediate_insurance_holding": "333-4",
                       "intermediate_mixed_financial_holding": "333-4",
                       "ancillary_subsidiary": "333-4"}
    require(isinstance(issuer_type, str) and issuer_type in issuer_articles, "issuer_type",
            "explicit331/332 insurer or333 intermediate-holding/ancillary route required", "UNSUPPORTED_METHOD")
    holding_route = issuer_articles[issuer_type] == "333-4"
    for key, value in (("issued_before_joining", issued_before_joining),
                       ("included_in_group_calculation", included_in_group_calculation),
                       ("orsa_support_confirmed", orsa_support_confirmed)):
        require(value is not None, key, "explicit qualified flag required", "REVIEW_REQUIRED")
        require(isinstance(value, bool), key, "boolean required")
    years = number(related_financial_years, "related_financial_years", 0)
    supervision = number(group_supervision_years, "group_supervision_years", 0)
    minimum = number(scalar("group_pre_acquisition_min_supervision_years", context), "minimum_supervision_years", 0)
    threshold = number(profile["scalars"]["group_pre_acquisition_scr_exception_years"]["value"],
                       "exception_years", 0)
    return int(issued_before_joining and included_in_group_calculation and years < threshold
               and supervision >= minimum and orsa_support_confirmed), {
        "related_financial_years": years, "exception_years": threshold, "boundary_strict": True,
        "issuer_type": issuer_type, "group_supervision_years": supervision,
        "minimum_group_supervision_years": minimum, "orsa_support_confirmed": orsa_support_confirmed,
        "orsa_content_verified": False,
        "issued_before_joining": issued_before_joining,
        "included_in_group_calculation": included_in_group_calculation,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "calendar_to_financial_year_conversion_performed": False, "tier_assigned": False,
        "scope": ("temporary_disapplication_of_article333_2_a_not_other_classification_conditions"
                  if holding_route else "temporary_solo_SCR_definition_in_articles71_73_77_not_MCR_or_tier_exemption"),
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                     + ":article-" + issuer_articles[issuer_type]]}
