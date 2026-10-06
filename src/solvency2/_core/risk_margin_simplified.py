"""Archived source-specific simplifications, not institution-specific projections."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


def _qualified(method, conditions, reference, context):
    _reference(reference, "eligibility_reference")
    profile = effective_resource("profile.json", context)
    rows = [row for row in profile["tables"]["risk_margin_simplification_conditions"]["rows"] if row[0] == method]
    keys = [row[1] for row in rows]
    require(bool(keys), "method", "method conditions not qualified", "UNSUPPORTED_METHOD")
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        require(conditions[key] is not None, key, "external qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")
    require(all(conditions.values()), "conditions", "simplification conditions not satisfied", "UNSUPPORTED_METHOD")
    source = profile["sources"]["RM_GUIDANCE"]
    return {"method": method, "conditions": dict(conditions), "eligibility_reference": reference,
            "qualification_status": "EXTERNAL_UNVERIFIED", "source_warning": source.get("source_warning"),
            "guidance_legal_applicability": "PENDING",
            "_sources": [row[2] for row in rows] + [
                context.profile_id + ":" + source["sha256"] + ":annex-IV-method-" + method]}


def _finite(value):
    try:
        return float(value)
    except OverflowError:
        require(False, "result", "simplified result outside representable range", "REVIEW_REQUIRED")


@calculation("DR:article-58:a", "RM_GUIDANCE:annex-IV:method-2", unit="currency")
def risk_margin_proportional_scr(initial_scr: float, initial_net_best_estimate: float,
                                 future_net_best_estimate: float, conditions: Mapping[str, bool], *,
                                 eligibility_reference: str, projection_reference: str, context: Context):
    """SCR(t)=SCR(0)*BE_net(t)/BE_net(0); never apply lambda inside SCR(t).

    BE(t) is valued AT time t, not a time-zero discounted cashflow surrogate.
    Whole-path nonnegative BE and risk-profile assumptions are externally
    qualified. No BE forecast or automatic method selection is produced.
    """
    details = _qualified("2", conditions, eligibility_reference, context)
    _reference(projection_reference, "projection_reference")
    scr = number(initial_scr, "initial_scr", 0)
    initial = number(initial_net_best_estimate, "initial_net_best_estimate")
    future = number(future_net_best_estimate, "future_net_best_estimate")
    require(initial >= 0 and future >= 0, "best_estimates", "negative best estimates exclude this method",
            "UNSUPPORTED_METHOD")
    require(initial > 0, "initial_net_best_estimate", "positive ratio denominator required", "REVIEW_REQUIRED")
    value = Fraction(str(scr)) * Fraction(str(future)) / Fraction(str(initial))
    return _finite(value), {**details, "initial_scr": scr, "initial_net_best_estimate": initial,
        "future_net_best_estimate": future, "projection_reference": projection_reference,
        "lambda_applied_to_projected_scr": False, "scope": "qualified_proportional_SCR_component_only"}


@calculation("DR:article-58:b", "RM_GUIDANCE:annex-IV:method-4", unit="currency")
def risk_margin_percentage(net_best_estimate: float, percentage: float, conditions: Mapping[str, bool], *,
                            eligibility_reference: str, percentage_reference: str, context: Context):
    """Externally calibrated alpha_lob * BE_net(0), not a prescribed default alpha.

    Percentage is a fraction (0.03 means3%). No unsupported100% cap is invented.
    Scope, calibration, hierarchy, future BE and options/guarantees restrictions
    are documented external qualifications, not inferred from the two numbers.
    """
    details = _qualified("4", conditions, eligibility_reference, context)
    _reference(percentage_reference, "percentage_reference")
    be = number(net_best_estimate, "net_best_estimate")
    require(be >= 0, "net_best_estimate", "negative best estimate excludes this method", "UNSUPPORTED_METHOD")
    alpha = number(percentage, "percentage", 0)
    value = Fraction(str(be)) * Fraction(str(alpha))
    return _finite(value), {**details, "net_best_estimate": be, "percentage": alpha,
        "percentage_reference": percentage_reference, "percentage_calibration": "EXTERNAL_UNVERIFIED",
        "scope": "qualified_line_of_business_percentage_component_only"}

@calculation("DR:article-58:b", "RM_GUIDANCE:annex-IV:method-3", unit="currency")
def risk_margin_duration(initial_scr: float, modified_duration: float, discount_rate: float,
                         conditions: Mapping[str, bool], *, eligibility_reference: str,
                         basis_reference: str, context: Context):
    """Baseline life formula including the divisor printed in archived Annex IV.

    Duration and rate conventions are externally qualified. No curve fitting,
    runoff model or automatic suitability determination is performed.
    """
    profile = effective_resource("profile.json", context)
    require(profile.get("methods", {}).get("risk_margin") == "UNDAMPED_BASELINE",
            "profile", "baseline duration formula only", "UNSUPPORTED_METHOD")
    details = _qualified("3", conditions, eligibility_reference, context)
    _reference(basis_reference, "basis_reference")
    scr = number(initial_scr, "initial_scr", 0)
    duration = number(modified_duration, "modified_duration", 0)
    rate = number(discount_rate, "discount_rate")
    require(rate > -1, "discount_rate", "annual rate must exceed -1")
    cost = number(scalar("cost_of_capital", context), "cost_of_capital", 0)
    value = (Fraction(str(cost)) * Fraction(str(scr)) * Fraction(str(duration))
             / (1 + Fraction(str(rate))))
    return _finite(value), {**details, "initial_scr": scr, "modified_duration": duration,
        "discount_rate": rate, "cost_of_capital": cost, "basis_reference": basis_reference,
        "basis_qualification": "EXTERNAL_UNVERIFIED",
        "scope": "qualified_life_duration_component_only"}


@calculation("DR:article-58:b", "RM_GUIDANCE:annex-IV:method-3", unit="currency")
def risk_margin_adjusted_duration_2027(initial_scr: float, cashflows: list[float],
                                      internal_rate: float, conditions: Mapping[str, bool], *,
                                      eligibility_reference: str, basis_reference: str,
                                      context: Context):
    """Future life formula from deterministic annual net cashflows, first at k=1.

    The supplied rate is the externally qualified IRR under the basic RFR term
    structure. Signed individual cashflows are allowed; whole-path BE suitability
    remains an external condition. Lambda is included in adjusted duration ONCE.
    """
    profile = effective_resource("profile.json", context)
    require(profile.get("methods", {}).get("risk_margin") == "TIME_ADJUSTED_2027",
            "profile", "adjusted future duration formula only", "UNSUPPORTED_METHOD")
    details = _qualified("3", conditions, eligibility_reference, context)
    _reference(basis_reference, "basis_reference")
    scr = number(initial_scr, "initial_scr", 0)
    rate = number(internal_rate, "internal_rate")
    require(rate > -1, "internal_rate", "annual rate must exceed -1")
    require(isinstance(cashflows, (list, tuple)) and bool(cashflows),
            "cashflows", "nonempty annual cashflow vector required")
    flows = [number(value, f"cashflows[{i}]") for i, value in enumerate(cashflows)]
    cost = number(scalar("cost_of_capital", context), "cost_of_capital", 0)
    decay = number(scalar("risk_margin_time_decay", context), "time_decay", 0, 1)
    floor = number(scalar("risk_margin_time_floor", context), "time_floor", 0, 1)
    # Exact intermediate ratios avoid overflow/cancellation before the final
    # representability check; all three policy parameters remain overrideable.
    discount = 1 + Fraction(str(rate))
    decay_fraction, floor_fraction = Fraction(str(decay)), Fraction(str(floor))
    discount_power = Fraction(1)
    decay_power = Fraction(1)
    alpha = Fraction(0)
    be = Fraction(0)
    weighted = Fraction(0)
    for cashflow in flows:
        discount_power *= discount
        alpha += max(decay_power, floor_fraction)
        pv = Fraction(str(cashflow)) / discount_power
        be += pv
        weighted += alpha * pv
        decay_power *= decay_fraction
    require(be >= 0, "net_best_estimate", "negative best estimate excludes method3", "UNSUPPORTED_METHOD")
    require(be > 0, "net_best_estimate", "positive duration denominator required", "REVIEW_REQUIRED")
    duration = weighted / (be * discount)
    require(duration >= 0, "adjusted_duration", "negative implied duration needs qualification", "REVIEW_REQUIRED")
    value = Fraction(str(cost)) * Fraction(str(scr)) * duration
    return _finite(value), {**details, "initial_scr": scr, "internal_rate": rate,
        "net_best_estimate": _finite(be), "adjusted_modified_duration": _finite(duration),
        "cost_of_capital": cost, "time_decay": decay, "time_floor": floor,
        "cashflow_count": len(flows), "lambda_applied_in_duration": True,
        "additional_lambda_applied": False, "basis_reference": basis_reference,
        "basis_qualification": "EXTERNAL_UNVERIFIED",
        "scope": "qualified_deterministic_life_duration_component_only"}


@calculation("DR:article-58:a", "RM_GUIDANCE:annex-IV:method-1", unit="currency")
def risk_margin_reserve_scr(net_claims_best_estimate: float, aggregated_reserve_sigma: float,
                            premium_volume: float, conditions: Mapping[str, bool], *,
                            eligibility_reference: str, projection_reference: str, context: Context):
    """Reserve-only 3*sigma_res_mod*PCO_net(t), never the whole nonlife SCR.

    Zero premium volume must be externally justified; no materiality threshold
    is invented. Sigma and claims projections are external, including any USP
    or profile-specific reinsurance adjustments. No lambda is applied here.
    """
    details = _qualified("1-reserve", conditions, eligibility_reference, context)
    _reference(projection_reference, "projection_reference")
    claims = number(net_claims_best_estimate, "net_claims_best_estimate")
    require(claims >= 0, "net_claims_best_estimate", "negative reserve basis requires separate review",
            "REVIEW_REQUIRED")
    sigma = number(aggregated_reserve_sigma, "aggregated_reserve_sigma", 0)
    premium = number(premium_volume, "premium_volume", 0)
    require(premium == 0, "premium_volume", "reserve-only method requires qualified zero premiums",
            "UNSUPPORTED_METHOD")
    multiplier = number(scalar("premium_reserve_multiplier", context), "multiplier", 0)
    value = Fraction(str(multiplier)) * Fraction(str(sigma)) * Fraction(str(claims))
    return _finite(value), {**details, "net_claims_best_estimate": claims,
        "aggregated_reserve_sigma": sigma, "premium_volume": premium, "multiplier": multiplier,
        "projection_reference": projection_reference, "lambda_applied_to_projected_scr": False,
        "scope": "reserve_component_only_excludes_catastrophe_lapse_and_other_risks"}
