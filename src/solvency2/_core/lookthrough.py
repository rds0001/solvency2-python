"""Look-through conditions on externally qualified fund and allocation inputs."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar


def _reference(value):
    require(isinstance(value, str) and bool(value.strip()), "qualification_reference",
            "external fund/allocation/scope qualification required", "MISSING_INPUT")


def _flag(name, value):
    require(value is not None, name, "external qualification unresolved", "REVIEW_REQUIRED")
    require(isinstance(value, bool), name, "explicit boolean required")
    return value


@calculation("DR:article-84:3", "DR:article-88", unit="indicator")
def lookthrough_fallback_conditions(conditions: Mapping[str, bool], *, allocation_basis: str,
                                    qualification_reference: str, context: Context):
    """Test target-first fallback conditions, not infer a fund's asset allocation.

    Only externally qualified collective/fund-form investments are in scope.
    Prudence and any data-grouping cap must be checked separately.
    """
    _reference(qualification_reference)
    keys = ("lookthrough_unavailable", "article88_satisfied", "target_allocation_known",
            "managed_according_to_allocation", "no_material_short_term_fluctuations")
    exact_keys(conditions, keys, "conditions")
    facts = {k: _flag(k, conditions[k]) for k in keys}
    require(allocation_basis in ("target", "last_reported"), "allocation_basis",
            "target or last_reported allocation required", "UNSUPPORTED_METHOD")
    preferred = "target" if facts["target_allocation_known"] else "last_reported"
    allowed = allocation_basis == preferred and all(facts[k] for k in keys if k != "target_allocation_known")
    return int(allowed), {"conditions": facts, "allocation_basis": allocation_basis, "preferred_basis": preferred,
                          "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                          "scope": "fund_fallback_conditions_not_lookthrough_calculation_or_asset_allocation"}


@calculation("DR:article-84:3", "DR:article-84:3a", unit="indicator")
def lookthrough_grouping_limit(grouped_assets_in_scope: float, total_assets_in_scope: float, *,
                               article84_3a_scope_qualified: bool, prudent_grouping: bool,
                               qualification_reference: str, context: Context):
    """Check an inclusive cap on externally scope-adjusted grouping amounts.

    Article84(3a) exclusion/classification and prudent risk grouping are external;
    zero/zero means only the inequality holds, not that a method is approved.
    """
    _reference(qualification_reference)
    scope = _flag("article84_3a_scope_qualified", article84_3a_scope_qualified)
    prudent = _flag("prudent_grouping", prudent_grouping)
    require(scope, "article84_3a_scope_qualified", "Article84(3a) scope must be qualified", "REVIEW_REQUIRED")
    grouped = number(grouped_assets_in_scope, "grouped_assets_in_scope", 0)
    total = number(total_assets_in_scope, "total_assets_in_scope", 0)
    require(grouped <= total, "grouped_assets_in_scope", "grouped amount exceeds qualified total")
    limit = number(scalar("lookthrough_grouping_limit", context), "lookthrough_grouping_limit", 0, 1)
    within = Fraction(str(grouped)) <= Fraction(str(limit)) * Fraction(str(total))
    return int(prudent and within), {"grouped_assets_in_scope": grouped, "total_assets_in_scope": total,
                                     "limit": limit, "maximum_grouped_amount": limit * total,
                                     "within_limit": within, "prudent_grouping": prudent,
                                     "qualification_reference": qualification_reference,
                                     "qualification_status": "EXTERNAL_UNVERIFIED",
                                     "scope": "grouping_inequality_not_exclusion_basis_or_method_approval"}
