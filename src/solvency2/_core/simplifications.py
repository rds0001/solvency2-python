"""Prescribed simplification components, not model or supervisory approval."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, number, require, scalar


def _reference(value, name):
    require(isinstance(value, str) and bool(value.strip()), name, "external qualification reference required",
            "MISSING_INPUT")


@calculation("DIR:article-109:1-3", unit="indicator")
def simplification_share_screen_2027(risk_shares: Mapping[str, float], *, regime: str,
                                     evidence_age_years: float, small_non_complex: bool | None = None,
                                     qualification_reference: str, context: Context):
    """Check distinct strict SNC versus inclusive immaterial-risk thresholds.

    Shares refer to each risk's externally qualified reference calculation;
    never infer a common denominator or double-count nested modules. The age
    is externally qualified and covers the oldest required reference evidence.
    """
    _reference(qualification_reference, "qualification_reference")
    require(regime in ("small_non_complex", "immaterial_modules"), "regime", "explicit regime required",
            "UNSUPPORTED_METHOD")
    require(isinstance(risk_shares, Mapping), "risk_shares", "risk-labelled mapping required")
    require(bool(risk_shares), "risk_shares", "explicit risk shares required", "MISSING_INPUT")
    shares = {}
    for label, value in risk_shares.items():
        require(isinstance(label, str) and bool(label.strip()), "risk_shares", "nonempty risk identifier required")
        shares[label] = number(value, f"risk_shares.{label}", 0)
    age = number(evidence_age_years, "evidence_age_years", 0)
    snc = regime == "small_non_complex"
    if snc:
        require(small_non_complex is not None, "small_non_complex", "classification unresolved", "REVIEW_REQUIRED")
        require(isinstance(small_non_complex, bool), "small_non_complex", "explicit boolean required")
    else:
        require(small_non_complex is None, "small_non_complex", "omit unused classification")
    prefix = "snc_simplification_" if snc else "immaterial_simplification_"
    individual = number(scalar(prefix + "individual_limit", context), prefix + "individual_limit", 0, 1)
    aggregate = number(scalar(prefix + "aggregate_limit", context), prefix + "aggregate_limit", 0, 1)
    years_name = prefix + ("review_years" if snc else "max_years")
    years = number(scalar(years_name, context), years_name, 0)
    require(years > 0, years_name, "positive evidence window required")
    exact = [Fraction(str(value)) for value in shares.values()]
    limit, total_limit = Fraction(str(individual)), Fraction(str(aggregate))
    total = sum(exact, Fraction(0))
    individual_met = all(v < limit if snc else v <= limit for v in exact)
    aggregate_met = total < total_limit if snc else total <= total_limit
    age_met = age <= years
    eligible = individual_met and aggregate_met and age_met and (small_non_complex if snc else True)
    return int(eligible), {"risk_shares": shares, "regime": regime, "individual_limit": individual,
                           "aggregate_limit": aggregate, "individual_condition": individual_met,
                           "aggregate_condition": aggregate_met, "evidence_age_years": age,
                           "maximum_evidence_years": years, "evidence_current": age_met,
                           "qualification_reference": qualification_reference,
                           "qualification_status": "EXTERNAL_UNVERIFIED",
                           "scope": "numeric_share_age_screen_not_calibration_or_supervisory_approval"}


@calculation("DR:article-89a:2-3", "DIR:article-109:2-3")
def simplified_immaterial_risk_2027(base_scr: float, base_volume: float, current_volume: float, *,
                                   elapsed_years: float, is_market_risk: bool,
                                   eligibility_reference: str, volume_reference: str, context: Context):
    """Scale the reference SCR with volume, retaining its prescribed floor.

    Eligibility under DIR109(2/3), reference calculation and suitability of the
    company-specific volume are externally established. A factor ratio in the
    details avoids overflow/underflow from an unnecessary intermediate float.
    """
    _reference(eligibility_reference, "eligibility_reference")
    _reference(volume_reference, "volume_reference")
    require(is_market_risk is not None, "is_market_risk", "risk classification unresolved", "REVIEW_REQUIRED")
    require(isinstance(is_market_risk, bool), "is_market_risk", "explicit boolean required")
    require(not is_market_risk, "is_market_risk", "market module/submodules excluded", "UNSUPPORTED_METHOD")
    base = number(base_scr, "base_scr", 0)
    initial = number(base_volume, "base_volume", 0)
    require(initial > 0, "base_volume", "positive reference volume required")
    current = number(current_volume, "current_volume", 0)
    age = number(elapsed_years, "elapsed_years", 0)
    years = number(scalar("immaterial_simplification_max_years", context), "immaterial_simplification_max_years", 0)
    require(years > 0, "immaterial_simplification_max_years", "positive window required")
    require(age <= years, "elapsed_years", "reference calculation outside allowed window", "UNSUPPORTED_METHOD")
    scaled = Fraction(base) * Fraction(current) / Fraction(initial)
    try:
        value = float(max(Fraction(base), scaled))
    except OverflowError:
        require(False, "simplified_scr", "scaled SCR not representable", "REVIEW_REQUIRED")
    return value, {"base_scr": base, "base_volume": initial, "current_volume": current,
                   "risk_factor_ratio": {"numerator": base, "denominator": initial},
                   "base_floor_binding": scaled <= Fraction(base), "elapsed_years": age,
                   "maximum_years": years, "eligibility_reference": eligibility_reference,
                   "volume_reference": volume_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "immaterial_risk_scaling_not_materiality_or_volume_model"}
