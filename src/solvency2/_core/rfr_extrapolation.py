"""2027 extrapolation components, not official curve calibration or market selection."""
import math
from collections.abc import Mapping
from fractions import Fraction

from .core import Context, calculation, number, require, scalar


def _reference(value):
    require(isinstance(value, str) and bool(value.strip()), "qualification_reference",
            "external currency, curve and input qualification reference required", "MISSING_INPUT")


@calculation("DR:article-43a", unit="ratio")
def rfr_fsp_currency_percentage_2027(minimum_euro_share: float, *,
        calibration: str = "initial", last_liquid_maturity_2027: float | None = None,
        rounded_preserves_fsp: bool | None = None, lower_preserving_share: float | None = None,
        qualification_reference: str, context: Context):
    """Prescribed percentage, not a market-data calibration or an FSP maturity.

    Initial EUR minimum is qualified at28Jan2025 for20years. A EUR source-change
    minimum is qualified at the first new-source date against the previous
    calendar-year FSP. A next-lower preserving value is externally identified;
    Article43a(2) does not justify inventing a market selection algorithm here.
    Other-currency initial LLP is qualified at29Jan2027, not today's maturity.
    """
    _reference(qualification_reference)
    require(isinstance(calibration, str) and calibration in {"initial", "euro_source_change"}, "calibration", "qualified calibration route required")
    minimum = number(minimum_euro_share, "minimum_euro_share", 0, 1)
    uplift = number(scalar("rfr_fsp_share_uplift", context), "uplift", 0, 1)
    step = number(scalar("rfr_fsp_share_step", context), "step", 0, 1)
    require(step > 0, "step", "positive rounding grid required")
    grid = Fraction(str(step))
    # Decimal arithmetic avoids rounding an exact half-percent boundary twice.
    rounded = math.ceil((Fraction(str(minimum)) + Fraction(str(uplift))) / grid) * grid
    require(rounded <= 1, "euro_percentage", "qualified calibration outside percentage range", "REVIEW_REQUIRED")
    euro = float(rounded)
    if calibration == "euro_source_change":
        require(context.currency == "EUR", "calibration", "43a(2) is the EUR source-change route", "UNSUPPORTED_METHOD")
        require(rounded_preserves_fsp is not None, "rounded_preserves_fsp", "preservation assessment required", "REVIEW_REQUIRED")
        require(isinstance(rounded_preserves_fsp, bool), "rounded_preserves_fsp", "explicit boolean required")
        if not rounded_preserves_fsp:
            euro = number(lower_preserving_share, "lower_preserving_share", minimum, float(rounded))
            require(Fraction(str(euro)) < rounded, "lower_preserving_share", "strictly lower preserving value required")
        else:
            require(lower_preserving_share is None, "lower_preserving_share", "unused fallback")
    else:
        require(rounded_preserves_fsp is None and lower_preserving_share is None,
                "source_change", "preservation fallback is source-change-only")
    multiplier = 1.0
    if context.currency == "EUR":
        require(last_liquid_maturity_2027 is None, "last_liquid_maturity_2027", "EUR does not use other-currency LLP")
    else:
        llp = number(last_liquid_maturity_2027, "last_liquid_maturity_2027", 0)
        cutoff = number(scalar("rfr_fsp_llp_cutoff_years", context), "llp_cutoff", 0)
        if llp < cutoff:
            multiplier = number(scalar("rfr_fsp_other_currency_fraction", context), "other_fraction", 0, 1)
    return euro * multiplier, {"minimum_euro_share": minimum, "rounded_euro_share": float(rounded),
        "applied_euro_share": euro, "currency_multiplier": multiplier, "calibration": calibration,
        "last_liquid_maturity_2027": last_liquid_maturity_2027,
        "rounded_preserves_fsp": rounded_preserves_fsp, "lower_preserving_share": lower_preserving_share,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "official_calibration_performed": False, "scope": "currency_percentage_not_FSP_selection"}


@calculation("DR:article-46:1c", unit="rate")
def rfr_last_liquid_forward_2027(fsp_forward: float, later_forwards: Mapping, *,
                                liquid_swaps_beyond_fsp: bool | None,
                                fsp_average_notional: float | None = None,
                                apply_volatility_adjustment: bool | None,
                                volatility_adjustment: float | None = None,
                                qualification_reference: str, context: Context):
    """Aggregate externally qualified continuous forwards using swap notionals.

    Component a is the one-year forward immediately preceding FSP in the
    SRC-0211 construction; components b run
    from FSP to later liquid maturities. Only a receives the explicit VA.
    Market selection, forward derivation and VA qualification are external.
    Here volatility_adjustment is a CONTINUOUS forward increment; the
    integrated rfr_curve_spot_2027 converts annual VA using log1p first.
    """
    _reference(qualification_reference)
    for name, flag in (("liquid_swaps_beyond_fsp", liquid_swaps_beyond_fsp),
                       ("apply_volatility_adjustment", apply_volatility_adjustment)):
        require(flag is not None, name, "external decision unresolved", "REVIEW_REQUIRED")
        require(isinstance(flag, bool), name, "explicit boolean required")
    require(isinstance(later_forwards, Mapping), "later_forwards", "explicit mapping required")
    first = number(fsp_forward, "fsp_forward")
    if apply_volatility_adjustment:
        va = number(volatility_adjustment, "volatility_adjustment")
    else:
        require(volatility_adjustment is None, "volatility_adjustment", "omit unused VA input")
        va = 0.0
    adjusted = first + va
    require(math.isfinite(adjusted), "adjusted_fsp_forward", "adjusted forward not representable", "REVIEW_REQUIRED")
    details = {"fsp_forward": first, "adjusted_fsp_forward": adjusted,
               "volatility_adjustment": va, "apply_volatility_adjustment": apply_volatility_adjustment,
               "liquid_swaps_beyond_fsp": liquid_swaps_beyond_fsp,
               "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
               "scope": "continuous_llfr_aggregation_not_market_selection_or_forward_derivation"}
    if not liquid_swaps_beyond_fsp:
        require(not later_forwards, "later_forwards", "omit later forwards when no liquid swaps exist")
        require(fsp_average_notional is None, "fsp_average_notional", "omit unused fallback notional")
        return adjusted, {**details, "fsp_weight": 1.0, "later_weights": {}}
    require(bool(later_forwards), "later_forwards", "qualified later forwards required", "MISSING_INPUT")
    notionals = [number(fsp_average_notional, "fsp_average_notional", 0)]
    rates = [adjusted]
    labels = []
    for label, row in later_forwards.items():
        require(isinstance(label, str) and bool(label.strip()), "later_forwards", "nonempty instrument labels required")
        require(isinstance(row, Mapping) and set(row) == {"forward_rate", "average_notional"},
                label, "exact forward_rate and average_notional fields required")
        rates.append(number(row["forward_rate"], label + ".forward_rate"))
        notionals.append(number(row["average_notional"], label + ".average_notional", 0))
        labels.append(label)
    # Exact arithmetic on finite binary inputs prevents a tiny weight from
    # underflowing before multiplication by a large rate. No float sum overflow.
    exact_notionals = [Fraction(value) for value in notionals]
    total = sum(exact_notionals)
    require(total > 0, "average_notionals", "positive total notional required", "REVIEW_REQUIRED")
    weights = [float(value / total) for value in exact_notionals]
    value = float(sum(notional * Fraction(rate) for notional, rate in zip(exact_notionals, rates)) / total)
    return value, {**details, "fsp_weight": weights[0], "later_weights": dict(zip(labels, weights[1:])),
                   "fsp_average_notional": notionals[0], "later_average_notionals": dict(zip(labels, notionals[1:]))}


def _alpha(phase_in, approval_reference, context):
    require(phase_in is not None, "phase_in", "phase-in decision unresolved", "REVIEW_REQUIRED")
    require(isinstance(phase_in, bool), "phase_in", "explicit boolean required")
    group = "sek" if context.currency == "SEK" else "other"
    terminal = number(scalar("rfr_extrapolation_alpha_" + group, context), "terminal_alpha", 0)
    require(terminal > 0, "terminal_alpha", "positive convergence parameter required")
    year = int(context.as_of[:4])
    details = {"currency_group": group, "calendar_year": year, "phase_in": phase_in,
               "terminal_alpha": terminal, "approval_reference": approval_reference,
               "approval_status": "EXTERNAL_UNVERIFIED" if phase_in else "NOT_APPLICABLE"}
    if not phase_in:
        require(approval_reference is None, "approval_reference", "omit unused phase-in approval")
        return terminal, details
    require(isinstance(approval_reference, str) and bool(approval_reference.strip()), "approval_reference",
            "external supervisory phase-in approval reference required", "MISSING_INPUT")
    initial = number(scalar("rfr_extrapolation_phase_start_" + group, context), "initial_alpha", 0)
    require(initial > 0, "initial_alpha", "positive initial convergence parameter required")
    start = number(scalar("rfr_extrapolation_phase_start_year", context), "phase_start_year")
    end = number(scalar("rfr_extrapolation_phase_end_year", context), "phase_end_year")
    require(start.is_integer() and end.is_integer() and start < end,
            "phase_years", "ordered integer calendar years required")
    elapsed_fraction = min(1, max(0, (year - start) / (end - start)))
    alpha = math.fsum(((1 - elapsed_fraction) * initial, elapsed_fraction * terminal))
    return alpha, {**details, "initial_alpha": initial, "phase_start_year": start,
                   "phase_end_year": end, "elapsed_fraction": elapsed_fraction}


@calculation("DR:article-46:1b", "DR:article-46a:1-2", unit="ratio")
def rfr_extrapolation_alpha_2027(*, phase_in: bool | None, approval_reference: str | None = None,
                                 qualification_reference: str, context: Context):
    """Own versioned alpha, with annual approved transition and no post-2032 trend."""
    _reference(qualification_reference)
    alpha, details = _alpha(phase_in, approval_reference, context)
    return alpha, {**details, "qualification_reference": qualification_reference,
                   "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "convergence_parameter_only_not_phase_in_permission"}


@calculation("DR:article-46:1b", "DR:article-46a:1-2", unit="rate")
def rfr_extrapolated_forward_2027(ufr: float, last_liquid_forward: float, time_after_fsp: float,
                                 *, phase_in: bool | None, approval_reference: str | None = None,
                                 qualification_reference: str, context: Context):
    """Return the continuous forward from annual-discrete UFR and continuous LLFR.

    LLFR determination, UFR publication and VA treatment are external. Alpha
    comes from the profile, not an untracked arbitrary caller coefficient.
    """
    _reference(qualification_reference)
    ultimate = number(ufr, "ufr")
    require(ultimate > -1, "ufr", "annual discrete UFR must exceed -1")
    liquid = number(last_liquid_forward, "last_liquid_forward")
    years = number(time_after_fsp, "time_after_fsp", 0)
    require(years > 0, "time_after_fsp", "strictly positive extrapolation horizon required")
    alpha, details = _alpha(phase_in, approval_reference, context)
    product = alpha * years
    # Stable near zero; infinity from a finite-input product has weight zero.
    weight = 1.0 if product == 0 else -math.expm1(-product) / product
    continuous_ufr = math.log1p(ultimate)
    value = math.fsum((weight * liquid, (1 - weight) * continuous_ufr))
    return value, {**details, "alpha": alpha, "ufr": ultimate, "continuous_ufr": continuous_ufr,
                   "last_liquid_forward": liquid, "time_after_fsp": years,
                   "llfr_weight": weight, "ufr_weight": 1 - weight,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "continuous_extrapolated_forward_not_llfr_or_official_curve"}


@calculation("DR:article-46:1a", unit="rate")
def rfr_extrapolated_spot_2027(fsp_years: float, spot_at_fsp: float, time_after_fsp: float,
                              extrapolated_forward: float, *, qualification_reference: str, context: Context):
    """Convert the FSP spot and a matching continuous forward to an annual spot.

    Scaled time weights avoid overflow. This API is strictly beyond FSP; it
    neither selects FSP nor adds VA/MA automatically.
    """
    _reference(qualification_reference)
    fsp = number(fsp_years, "fsp_years", 0)
    horizon = number(time_after_fsp, "time_after_fsp", 0)
    require(fsp > 0 and horizon > 0, "maturities", "FSP and extrapolation horizon must be positive")
    spot = number(spot_at_fsp, "spot_at_fsp")
    require(spot > -1, "spot_at_fsp", "annual spot must exceed -1")
    forward = number(extrapolated_forward, "extrapolated_forward")
    scale = max(fsp, horizon)
    fsp_weight = (fsp / scale) / (fsp / scale + horizon / scale)
    horizon_weight = (horizon / scale) / (fsp / scale + horizon / scale)
    continuous_spot = math.fsum((fsp_weight * math.log1p(spot), horizon_weight * forward))
    try:
        result = math.expm1(continuous_spot)
    except OverflowError:
        require(False, "extrapolated_spot", "annual spot not representable", "REVIEW_REQUIRED")
    require(math.isfinite(result) and result > -1, "extrapolated_spot",
            "annual spot not representable above -1", "REVIEW_REQUIRED")
    return result, {"fsp_years": fsp, "spot_at_fsp": spot, "time_after_fsp": horizon,
                    "extrapolated_forward": forward, "fsp_weight": fsp_weight,
                    "horizon_weight": horizon_weight, "continuous_spot": continuous_spot,
                    "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                    "scope": "annual_extrapolated_spot_not_official_curve_or_va_ma_application"}
