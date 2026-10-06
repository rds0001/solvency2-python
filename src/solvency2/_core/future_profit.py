"""Qualified EPIFP valuation differences with explicit historical/2027 netting.

These components do not project insurance cashflows, classify homogeneous
groups, approve assumptions or add the result to the own-funds surplus again.
"""
from fractions import Fraction
import sys
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require


def _reference(value):
    require(isinstance(value, str) and bool(value.strip()), "qualification_reference",
            "qualified homogeneous scope and risk-margin-free scenario valuations required", "MISSING_INPUT")


def _finite(value, field):
    require(abs(value) <= Fraction(str(sys.float_info.max)), field,
            "valuation difference outside finite numeric range", "REVIEW_REQUIRED")
    return float(value)


def _difference(with_value, without_value, label):
    # Both signed liability values are allowed. Decimal-string fractions avoid
    # overflowing the subtraction or losing decimal cancellation unnecessarily.
    before = number(with_value, label + ".with")
    after = number(without_value, label + ".without")
    return before, after, Fraction(str(after)) - Fraction(str(before))


def _sources(profile, context, *references):
    return [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":" + r for r in references]


@calculation("DR:article-1:46", "DR:article-260:2:3:4", unit="currency")
def own_funds_expected_future_premium_profit(group_valuations: Mapping, *,
                                             qualification_reference: str, context: Context):
    """Aggregate without-minus-with valuations in externally qualified groups.

    Each row has exactly with_future_premiums and without_future_premiums,
    both WITHOUT risk margin. Historical losses cannot offset other groups;
    the published 2027 rule requires signed cross-group netting. No invented
    total zero floor, insurer valuation model or additional own-funds credit.
    """
    _reference(qualification_reference)
    profile = effective_resource("profile.json", context)
    method = profile.get("methods", {}).get("future_premium_profit_netting")
    require(method in {"WITHIN_GROUP_ONLY", "ACROSS_GROUPS_2027"}, "profile_id",
            "explicit versioned EPIFP netting method required", "UNSUPPORTED_RULESET")
    require(isinstance(group_valuations, Mapping) and bool(group_valuations), "group_valuations",
            "nonempty explicitly qualified homogeneous-group mapping required")
    require(all(isinstance(k, str) and bool(k.strip()) for k in group_valuations), "group_valuations",
            "nonempty string group identifiers required")
    rows, contributions = {}, []
    for label in sorted(group_valuations):
        row = group_valuations[label]
        exact_keys(row, ("with_future_premiums", "without_future_premiums"), "group_valuations." + label)
        before, after, difference = _difference(row["with_future_premiums"], row["without_future_premiums"], label)
        contribution = max(Fraction(0), difference) if method == "WITHIN_GROUP_ONLY" else difference
        rows[label] = {"with_future_premiums": before, "without_future_premiums": after,
                       "signed_profit": _finite(difference, label + ".signed_profit"),
                       "included_profit": _finite(contribution, label + ".included_profit")}
        contributions.append(contribution)
    total = _finite(sum(contributions, Fraction(0)), "expected_future_premium_profit")
    return total, {
        "groups": rows, "netting_method": method,
        "difference_orientation": "without_future_premiums_minus_with_future_premiums",
        "cross_group_loss_offset_applied": method == "ACROSS_GROUPS_2027",
        "group_zero_floor_applied": method == "WITHIN_GROUP_ONLY", "total_zero_floor_applied": False,
        "negative_total": total < 0, "risk_margin_included": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scenario_valuations_computed": False, "homogeneous_grouping_verified": False,
        "actuarial_assumptions_verified": False, "own_funds_surplus_increased": False,
        "regulatory_total_released": False,
        "scope": "qualified_EPIFP_valuation_difference_not_valuation_or_own_funds_approval",
        "_sources": _sources(profile, context, "article-1-46", "article-260-2-3-4", "article-70-2")}


@calculation("DR:article-1:46a", "DR:article-260:2a", unit="currency")
def own_funds_expected_future_fee_profit_2027(with_future_fees: float, without_future_fees: float, *,
                                             qualification_reference: str, context: Context):
    """Signed fee-scenario difference for one qualified index/unit-linked scope.

    Both input valuations exclude risk margin. No transfer of the premium-only
    grouping clause to fees, and no automatic addition of fee profit to EPIFP.
    """
    profile = effective_resource("profile.json", context)
    require(profile.get("methods", {}).get("future_premium_profit_netting") == "ACROSS_GROUPS_2027",
            "profile_id", "future fee-profit provision only in the 2027 reference profile", "UNSUPPORTED_RULESET")
    _reference(qualification_reference)
    before, after, difference = _difference(with_future_fees, without_future_fees, "fee_valuation")
    total = _finite(difference, "expected_future_fee_profit")
    return total, {
        "with_future_fees": before, "without_future_fees": after,
        "difference_orientation": "without_future_fees_minus_with_future_fees",
        "zero_floor_applied": False, "negative_total": total < 0, "risk_margin_included": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scenario_valuations_computed": False, "index_unit_linked_scope_verified": False,
        "actuarial_assumptions_verified": False, "premium_profit_added": False,
        "own_funds_surplus_increased": False, "regulatory_total_released": False,
        "scope": "single_qualified_future_fee_valuation_difference_not_scope_or_own_funds_approval",
        "_sources": _sources(profile, context, "article-1-46a", "article-260-2a")}
