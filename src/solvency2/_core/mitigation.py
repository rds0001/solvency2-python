"""Prescribed simplified mitigation; scenario valuations and eligibility are external."""
from fractions import Fraction
import math
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar


@calculation("DR:article-111a", "DR:article-196", "DR:article-88")
def simplified_single_segment_mitigation(cat_hyp: float, cat_without: float,
                                         premium_hyp: float, premium_without: float,
                                         sigma: float, recoverables: float, *,
                                         single_segment: bool | None, eligibility_reference: str,
                                         valuation_reference: str, context: Context):
    """Literal111a quadratic formula; preserve signed differences, no subfloors.

    'hyp' is the scenario without the arrangement. Despite its source label,
    'without' denotes the ordinary capital/volume defined in111a(b/e).
    Recoverables are the qualified best estimate plus corresponding receivables.
    Segment sigma follows117(3)/148(3), not total premium/reserve sigma.
    """
    _references(eligibility_reference, valuation_reference)
    require(single_segment is None or isinstance(single_segment, bool), "single_segment", "boolean or unresolved None")
    require(single_segment is not None, "single_segment", "scope unresolved", "REVIEW_REQUIRED")
    require(single_segment, "single_segment", "111a requires a single AnnexII/XIV segment", "UNSUPPORTED_METHOD")
    a = number(cat_hyp, "cat_hyp", 0) - number(cat_without, "cat_without", 0)
    b = number(premium_hyp, "premium_hyp", 0) - number(premium_without, "premium_without", 0) + number(recoverables, "recoverables")
    sd = number(sigma, "sigma", 0)
    multiplier = number(scalar("single_segment_mitigation_premium_multiplier", context), "premium_multiplier", 0)
    interaction = number(scalar("single_segment_mitigation_interaction", context), "interaction", 0)
    require(multiplier > 0 and interaction <= 2 * multiplier, "coefficients", "positive-semidefinite prescribed quadratic required")
    y = multiplier * sd * b
    rho = interaction / (2 * multiplier)
    value = math.hypot(a + rho * y, y * math.sqrt(1 - rho * rho))
    return value, {**_details(eligibility_reference, valuation_reference, "article111a_single_segment_effect_not_full_default_SCR"),
        "catastrophe_difference": a, "premium_and_recoverable_difference": b,
        "premium_multiplier": multiplier, "interaction_coefficient": interaction,
        "component_differences_floored": False}


def _references(eligibility, valuation):
    for key, value in (("eligibility_reference", eligibility), ("valuation_reference", valuation)):
        require(isinstance(value, str) and bool(value.strip()), key,
                "external scope/qualification/valuation reference required", "MISSING_INPUT")


def _values(values, name, minimum=None, maximum=None):
    require(isinstance(values, Mapping), name, "labelled mapping required")
    require(bool(values), name, "explicit scope entries required", "MISSING_INPUT")
    result = {}
    for key, value in values.items():
        require(isinstance(key, str) and bool(key.strip()), name, "nonempty string identifier required")
        result[key] = number(value, f"{name}.{key}", minimum, maximum)
    return result


def _target(values, target):
    require(isinstance(target, str) and bool(target.strip()), "target_counterparty", "nonempty identifier required")
    require(target in values, "target_counterparty", "target absent from declared scope", "MISSING_INPUT")
    return Fraction(values[target])


def _float(value):
    try:
        return float(value)
    except OverflowError:
        require(False, "mitigation", "result not representable", "REVIEW_REQUIRED")


def _details(eligibility, valuation, scope):
    return {"eligibility_reference": eligibility, "valuation_reference": valuation,
            "qualification_status": "EXTERNAL_UNVERIFIED", "scope": scope}


@calculation("DR:article-86:a")
def underwriting_currency_basis_risk(capital_charge: float, joint_currency_stress_charge: float, *,
                                      single_component_only: bool | None,
                                      eligibility_reference: str, valuation_reference: str, context: Context):
    """Art86(a) lowest-level charge plus a fraction of its joint-FX difference.

    The hypothetical charge is externally valued under simultaneous Art188.
    Multiple affected components need86(b)'s common capacity treatment, not
    independent repeated limits or an invented allocation of shared capacity.
    """
    _references(eligibility_reference, valuation_reference)
    require(single_component_only is None or isinstance(single_component_only, bool),
            "single_component_only", "boolean or unresolved None required")
    require(single_component_only is True, "single_component_only",
            "multiple/unknown component capacity scope requires separate Article86(b) qualification",
            "REVIEW_REQUIRED")
    base, joint = number(capital_charge, "capital_charge", 0), number(joint_currency_stress_charge,
                                                                   "joint_currency_stress_charge", 0)
    factor = number(scalar("underwriting_currency_basis_fraction", context), "factor", 0, 1)
    value = Fraction(str(base)) + Fraction(str(factor)) * (Fraction(str(joint)) - Fraction(str(base)))
    return _float(value), {**_details(eligibility_reference, valuation_reference,
                                     "article86a_single_component_adjusted_capital_not_total_scr"),
                           "base_charge": base, "joint_currency_stress_charge": joint, "factor": factor,
                           "adjustment": _float(value - Fraction(str(base))), "multi_component_cap_applied": False}


@calculation("DR:article-107:1-2", "DR:article-196")
def simplified_reinsurance_mitigation(recoverables: Mapping[str, float], target_counterparty: str,
                                      scr_without: float, scr_with: float, *,
                                      eligibility_reference: str, valuation_reference: str, context: Context):
    """Allocate underwriting mitigation using BE recoverables plus related debtors.

    Only the target's nonnegative condition is imposed on individual recoveries;
    other signed entries are not silently floored or the resulting share capped.
    """
    _references(eligibility_reference, valuation_reference)
    values = _values(recoverables, "recoverables")
    target = _target(values, target_counterparty)
    require(target >= 0, "target_recoverables", "negative target excluded by Article107", "UNSUPPORTED_METHOD")
    total = sum(map(Fraction, values.values()), Fraction(0))
    require(total > 0, "total_recoverables", "nonpositive denominator needs separate interpretation", "REVIEW_REQUIRED")
    without = number(scr_without, "scr_without", 0)
    with_agreement = number(scr_with, "scr_with", 0)
    mitigation = max(Fraction(without) - Fraction(with_agreement), Fraction(0))
    return _float(mitigation * target / total), {
        **_details(eligibility_reference, valuation_reference, "DR107_underwriting_recovery_allocation_only"),
        "recoverables": values, "target_counterparty": target_counterparty,
        "total_mitigation": _float(mitigation), "recoverables_basis": "BE_plus_related_debtors"}


@calculation("DR:article-108", "DR:article-196")
def simplified_proportional_mitigation(gross_best_estimate: float, recoverables: Mapping[str, float],
                                       submodule_scr: float, target_counterparty: str, *,
                                       eligibility_reference: str, valuation_reference: str, context: Context):
    """Article108 proportional-contract amount with the prescribed net-BE denominator."""
    _references(eligibility_reference, valuation_reference)
    gross = number(gross_best_estimate, "gross_best_estimate")
    scr = number(submodule_scr, "submodule_scr", 0)
    values = _values(recoverables, "recoverables")
    target = _target(values, target_counterparty)
    require(target >= 0, "target_recoverables", "negative target excluded by Article108", "UNSUPPORTED_METHOD")
    net = Fraction(gross) - sum(map(Fraction, values.values()), Fraction(0))
    require(net > 0, "net_best_estimate", "nonpositive denominator needs separate interpretation", "REVIEW_REQUIRED")
    return _float(target * Fraction(scr) / net), {
        **_details(eligibility_reference, valuation_reference, "DR108_proportional_contract_specific_risk_only"),
        "gross_best_estimate": gross, "recoverables": values, "submodule_scr": scr,
        "target_counterparty": target_counterparty, "recoverables_basis": "BE_plus_related_debtors"}


@calculation("DR:article-107a:1-3", "DR:article-196")
def simplified_ead_mitigation_2027(exposures: Mapping[str, float], target_counterparty: str,
                                  bscr_without: float, bscr_with: float, *, default_module_zero_in_both: bool,
                                  eligibility_reference: str, valuation_reference: str, context: Context):
    """Allocate default-zero BSCR mitigation using absolute EAD by external counterparty.

    Reinsurance/securitisation EAD here is BE recoverables under107a(2), not
    automatically the BE-plus-debtors basis of107. Derivative/SPV EAD is external.
    A complete scoped portfolio and both hypothetical BSCR valuations are required.
    """
    _references(eligibility_reference, valuation_reference)
    require(default_module_zero_in_both is not None, "default_module_zero_in_both",
            "hypothetical BSCR basis unresolved", "REVIEW_REQUIRED")
    require(isinstance(default_module_zero_in_both, bool), "default_module_zero_in_both", "explicit boolean required")
    require(default_module_zero_in_both, "default_module_zero_in_both",
            "both hypothetical BSCRs must set default module to zero", "UNSUPPORTED_METHOD")
    values = _values(exposures, "exposures")
    target = abs(_target(values, target_counterparty))
    total = sum((abs(Fraction(v)) for v in values.values()), Fraction(0))
    require(total > 0, "absolute_exposures", "zero absolute EAD sum", "REVIEW_REQUIRED")
    without = number(bscr_without, "bscr_without", 0)
    with_agreement = number(bscr_with, "bscr_with", 0)
    mitigation = max(Fraction(without) - Fraction(with_agreement), Fraction(0))
    weight = target / total
    return _float(weight * mitigation), {
        **_details(eligibility_reference, valuation_reference, "DR107a_default_zero_BSCR_allocation_only"),
        "exposures": values, "target_counterparty": target_counterparty, "absolute_weight": _float(weight),
        "total_mitigation": _float(mitigation), "default_module_zero_in_both": True}


@calculation("DR:article-110", unit="probability")
def simplified_default_group_pd(probabilities: Mapping[str, float], *,
                                eligibility_reference: str, valuation_reference: str, context: Context,
                                pool_rating_group: Mapping[str, dict] | None = None):
    """Conservative grouping PD, not LGD-weighted single-name PD under Article199."""
    _references(eligibility_reference, valuation_reference)
    values = _values(probabilities, "probabilities", 0, 1)
    grouping = {}
    if pool_rating_group is not None:
        exact_keys(pool_rating_group, tuple(values), "pool_rating_group")
        for label, row in pool_rating_group.items():
            exact_keys(row, ("nominated_ecai", "rating", "pool_type"), label)
            for field in ("nominated_ecai", "rating"):
                require(isinstance(row[field], str) and bool(row[field].strip()),
                        f"{label}.{field}", "nonempty external rating/agency required", "MISSING_INPUT")
            require(isinstance(row["pool_type"], str) and row["pool_type"] in ("A", "B", "C"),
                    f"{label}.pool_type", "explicit pool exposure type A/B/C required")
            grouping[label] = dict(row)
        signatures = {(row["nominated_ecai"], row["rating"], row["pool_type"]) for row in grouping.values()}
        require(len(signatures) == 1, "pool_rating_group",
                "Article109(d) requires separate groups by nominated rating and pool type A/B/C", "REVIEW_REQUIRED")
    return max(values.values()), {**_details(eligibility_reference, valuation_reference,
        "DR110_group_PD_only_not_group_LGD_valuation"), "probabilities": values,
        "pool_rating_group": grouping,
        "pool_grouping_status": "DECLARED_SEPARATION_CHECKED_EXTERNAL_UNVERIFIED" if grouping else "NOT_ASSESSED",
        "_sources": ["DR:article-109:d"] if grouping else []}


@calculation("DR:article-111", "DR:article-196")
def simplified_submodule_mitigation(scr_without: Mapping[str, float], scr_with: Mapping[str, float], *,
                                    eligibility_reference: str, valuation_reference: str, context: Context):
    """Floor the difference of submodule sums once, not each submodule separately."""
    _references(eligibility_reference, valuation_reference)
    without = _values(scr_without, "scr_without", 0)
    with_agreement = _values(scr_with, "scr_with", 0)
    exact_keys(with_agreement, tuple(without), "scr_with")
    difference = sum((Fraction(without[key]) - Fraction(with_agreement[key]) for key in without), Fraction(0))
    return _float(max(difference, Fraction(0))), {
        **_details(eligibility_reference, valuation_reference, "DR111_affected_submodule_sums_only"),
        "scr_without": without, "scr_with": with_agreement, "floor_applied": difference < 0}


def _undertaking_share(value):
    share = number(value, "undertaking_share", 0, 1)
    require(share > 0, "undertaking_share", "positive undertaking pool share required")
    return share


@calculation("DR:article-109:a", "DR:article-194:1:d")
def simplified_pool_member_best_estimate(undertaking_best_estimate: float, undertaking_share: float,
                                         counterparty_share: float, *, eligibility_reference: str,
                                         valuation_reference: str, context: Context):
    """PC/PU times already externally netted BEU; do not net external recoveries twice."""
    _references(eligibility_reference, valuation_reference)
    be = number(undertaking_best_estimate, "undertaking_best_estimate")
    pu = _undertaking_share(undertaking_share)
    pc = number(counterparty_share, "counterparty_share", 0, 1)
    require(Fraction(str(pu)) + Fraction(str(pc)) <= 1, "shares", "distinct pool shares exceed total risk")
    return _float(Fraction(be) * Fraction(pc) / Fraction(pu)), {
        **_details(eligibility_reference, valuation_reference, "DR109a_member_BE_net_of_external_reinsurance"),
        "undertaking_best_estimate": be, "undertaking_share": pu, "counterparty_share": pc}


@calculation("DR:article-109:b", "DR:article-195:c")
def simplified_pool_external_best_estimate(ceded_best_estimate: float, undertaking_share: float, *,
                                           eligibility_reference: str, valuation_reference: str, context: Context):
    """Scale externally qualified BECEP to whole-pool BECE, retaining its sign."""
    _references(eligibility_reference, valuation_reference)
    be = number(ceded_best_estimate, "ceded_best_estimate")
    pu = _undertaking_share(undertaking_share)
    return _float(Fraction(be) / Fraction(pu)), {
        **_details(eligibility_reference, valuation_reference, "DR109b_whole_pool_external_BE_only"),
        "ceded_best_estimate": be, "undertaking_share": pu}


@calculation("DR:article-109:c", "DR:article-195:d")
def simplified_pool_external_mitigation(best_estimates: Mapping[str, float], target_counterparty: str,
                                        total_external_contribution: float, *, eligibility_reference: str,
                                        valuation_reference: str, context: Context):
    """Allocate signed external pool contributions; no extra floor on individual contributions."""
    _references(eligibility_reference, valuation_reference)
    values = _values(best_estimates, "best_estimates")
    target = _target(values, target_counterparty)
    total = sum(map(Fraction, values.values()), Fraction(0))
    require(total != 0, "total_best_estimate", "zero allocation denominator", "REVIEW_REQUIRED")
    contribution = number(total_external_contribution, "total_external_contribution")
    return _float(target * Fraction(contribution) / total), {
        **_details(eligibility_reference, valuation_reference, "DR109c_external_pool_contribution_only"),
        "best_estimates": values, "target_counterparty": target_counterparty,
        "total_external_contribution": contribution}
