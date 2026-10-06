"""DR104 simplification, separate from ordinary piecewise spread shocks."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _reference(value, name):
    require(isinstance(value, str) and bool(value.strip()), name,
            "external qualification reference required", "MISSING_INPUT")


def _as_float(value, field):
    try:
        return float(value)
    except OverflowError:
        require(False, field, "result not representable", "REVIEW_REQUIRED")


def _stress(duration, quality, context):
    require(isinstance(quality, str) and quality in (*map(str, range(7)), "unrated"),
            "credit_quality_step", "explicit CQS0..6 or unrated required")
    duration = number(duration, "modified_duration", 0)
    minimum = number(scalar("simplified_spread_minimum_duration", context), "minimum_duration", 0)
    effective = max(duration, minimum)
    if quality == "unrated":
        slope = number(scalar("simplified_spread_unrated_slope", context), "unrated_slope", 0)
        cap = number(scalar("simplified_spread_unrated_cap", context), "unrated_cap", 0, 1)
        factor = min(Fraction(effective) * Fraction(slope), Fraction(cap))
    else:
        table = effective_resource("profile.json", context)["tables"]["simplified_spread_slopes"]
        slope = number(dict(table["rows"])[quality], "slope", 0)
        cap = None
        factor = Fraction(effective) * Fraction(slope)
    return factor, {"modified_duration": duration, "effective_duration": effective,
                    "slope": slope, "cap": cap, "credit_quality_step": quality}


@calculation("DR:article-104:1-3", unit="ratio")
def simplified_bond_spread_stress(modified_duration: float, *, credit_quality_step: str,
                                  eligibility_reference: str, context: Context):
    """DR104 factor: rated values have no invented cap; only unrated is capped."""
    _reference(eligibility_reference, "eligibility_reference")
    factor, details = _stress(modified_duration, credit_quality_step, context)
    return _as_float(factor, "stress"), {**details, "eligibility_reference": eligibility_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "DR104_factor_not_DR176_standard_factor"}


@calculation("DR:article-104:1-3")
def simplified_bond_spread_risk(buckets: Mapping[str, dict], liability_change: float, *,
                                eligibility_reference: str, valuation_reference: str, context: Context):
    """Sum qualified bucket losses plus signed, externally valued DeltaLiab.

    Amount weighting is algebraically identical to MV times portfolio shares.
    Fractions avoid unnecessary intermediate overflow and cancellation. No
    options/guarantee model, floor or general eligibility approval is inferred.
    """
    _reference(eligibility_reference, "eligibility_reference")
    _reference(valuation_reference, "valuation_reference")
    keys = (*map(str, range(7)), "unrated")
    exact_keys(buckets, keys, "buckets")
    delta = number(liability_change, "liability_change")
    losses, details = [], {}
    for key in keys:
        row = buckets[key]
        exact_keys(row, ("market_value", "modified_duration"), f"buckets.{key}")
        amount = number(row["market_value"], f"buckets.{key}.market_value", 0)
        factor, terms = _stress(row["modified_duration"], key, context)
        loss = Fraction(amount) * factor
        losses.append(loss)
        # Record losses rather than a potentially nonrepresentable factor.
        details[key] = {**terms, "market_value": amount,
                        "loss": _as_float(loss, f"buckets.{key}.loss")}
    asset_loss = sum(losses, Fraction(0))
    return _as_float(asset_loss + Fraction(delta), "simplified_spread_risk"), {
        "buckets": details, "liability_change": delta,
        "eligibility_reference": eligibility_reference, "valuation_reference": valuation_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "DR104_prescribed_formula_not_full_market_SCR"}
