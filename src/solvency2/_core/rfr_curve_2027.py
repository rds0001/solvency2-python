"""2027 constant-forward bootstrap and curve assembly from qualified market rates."""

import bisect
import math
from collections.abc import Mapping

from .core import Context, calculation, exact_keys, number, require
from .rfr_extrapolation import _alpha, rfr_last_liquid_forward_2027


def _swap_interval(coupon, known_sum, start_discount, count):
    """Solve the par-bond polynomial in the positive one-period discount x.

    (1+c)*x**n+c*(x+...+x**(n-1))=(1-c*known_sum)/D(start).
    With c>-1 and positive RHS, coefficients have exactly one sign change,
    including negative coupons: there is one positive root. Bisection avoids
    the zero-coupon singularity of algebraically divided source formulas.
    """
    rhs = (1 - coupon * known_sum) / start_discount
    require(rhs > 0 and math.isfinite(rhs), "swap_calibration", "no positive identifiable discount solution", "REVIEW_REQUIRED")

    def residual(x):
        value = 1 + coupon
        for _ in range(count - 1):
            value = value * x + coupon
        result = value * x - rhs
        require(math.isfinite(result), "swap_calibration", "polynomial not representable", "REVIEW_REQUIRED")
        return result

    low, high = 0.0, 1.0
    for _ in range(100):
        if residual(high) >= 0:
            break
        high *= 2
    else:
        require(False, "swap_calibration", "root could not be bracketed", "REVIEW_REQUIRED")
    for _ in range(160):
        middle = (low + high) / 2
        error = residual(middle)
        if abs(error) <= 1e-13 * max(1, abs(rhs)):
            return middle
        if middle == low or middle == high:
            break
        if error > 0:
            high = middle
        else:
            low = middle
    require(False, "swap_calibration", "root not resolved to numerical tolerance", "REVIEW_REQUIRED")


@calculation("DR:article-44:1", "DR:article-46:1a-1c", "DR:article-46a:1-2", unit="rate")
def rfr_curve_spot_2027(market_rates: Mapping, first_smoothing_point: float,
                        maturity: float, *, instrument_kind: str,
                        coupon_frequency: int | None = None, average_notionals: Mapping | None = None,
                        ufr: float, phase_in: bool | None, approval_reference: str | None = None,
                        volatility_adjustment: float | None = None, matching_adjustment: float | None = None,
                        interest_stress: str | None = None,
                        output_maturities=(), qualification_reference: str, context: Context):
    """Build a basic/VA/MA curve once, including all requested output maturities.

    Market rates are already CRA/CURA-adjusted and selected under external
    DLT, FSP/RVC and missing-data/previous-trading-day qualification. Keys are
    canonical positive integer years. VA is an annual decimal rate already
    rounded to whole basis points; its continuous equivalent enters LLFR.
    This is a numerical engine component, not an official publication.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external market/FSP qualification required", "MISSING_INPUT")
    require(isinstance(market_rates, Mapping) and bool(market_rates), "market_rates", "nonempty maturity/rate mapping required")
    require(all(isinstance(key, str) and key.isascii() and key.isdecimal()
                and str(int(key)) == key and int(key) > 0 for key in market_rates),
            "market_rates", "canonical positive integer-year keys required")
    tenors = sorted(int(key) for key in market_rates)
    rates = {t: number(market_rates[str(t)], "market_rates." + str(t)) for t in tenors}
    fsp = number(first_smoothing_point, "first_smoothing_point", 0)
    require(fsp.is_integer() and int(fsp) in rates, "first_smoothing_point", "FSP must be an available market tenor")
    fsp = int(fsp)
    require(instrument_kind in {"par_swap", "zero_coupon"}, "instrument_kind", "par_swap or zero_coupon required")
    require(volatility_adjustment is None or matching_adjustment is None, "adjustments", "VA and MA are mutually exclusive")
    require(interest_stress is None or interest_stress == "down", "interest_stress",
            "only the source-qualified down scenario is supported", "UNSUPPORTED_METHOD")
    if interest_stress is not None:
        require(volatility_adjustment is None and matching_adjustment is None, "adjustments",
                "interest stress builds the basic curve; VA/MA treatment must be separately qualified",
                "UNSUPPORTED_METHOD")
    va = 0.0 if volatility_adjustment is None else number(volatility_adjustment, "volatility_adjustment")
    require(va > -1, "volatility_adjustment", "annual VA must exceed -1")
    require(math.isclose(va * 10000, round(va * 10000), rel_tol=0, abs_tol=1e-8),
            "volatility_adjustment", "VA must already be qualified in whole basis points")
    ma = 0.0 if matching_adjustment is None else number(matching_adjustment, "matching_adjustment")
    ultimate = number(ufr, "ufr")
    require(ultimate > -1, "ufr", "annual UFR must exceed -1")
    target = number(maturity, "maturity", 0)
    require(isinstance(output_maturities, (list, tuple)), "output_maturities", "explicit sequence required")
    grid = [number(v, "output_maturities", 0) for v in output_maturities]
    require(len(set(grid)) == len(grid), "output_maturities", "unique maturities required")
    if interest_stress is not None:
        require(all(t >= 1 for t in [target, *grid]), "maturity",
                "Article167 floor below one year is unresolved", "REVIEW_REQUIRED")
    # Logs retain the interpolation convention and avoid unnecessary annual
    # round trips. Swap discount factors also serve the repricing audit.
    knot_logs = {0: 0.0}
    price_errors = {}
    if instrument_kind == "par_swap":
        frequency = number(coupon_frequency, "coupon_frequency", 1)
        require(frequency.is_integer(), "coupon_frequency", "positive integer frequency required")
        frequency = int(frequency)
        discounts = [1.0]
        previous = 0
        for tenor in tenors:
            coupon = rates[tenor] / frequency
            require(coupon > -1, "swap_rate", "periodic coupon must exceed -1")
            count = (tenor - previous) * frequency
            known_sum = math.fsum(discounts[1:])
            start = discounts[-1]
            x = 1 / (1 + coupon) if previous == 0 else _swap_interval(coupon, known_sum, start, count)
            require(x > 0 and math.isfinite(x), "swap_discount", "positive finite discount required", "REVIEW_REQUIRED")
            for j in range(1, count + 1):
                discount = start * x ** j
                require(discount > 0 and math.isfinite(discount), "swap_discount", "unrepresentable coupon discount", "REVIEW_REQUIRED")
                discounts.append(discount)
            price = coupon * math.fsum(discounts[1:]) + discounts[-1]
            require(math.isfinite(price) and abs(price - 1) <= 1e-9,
                    "swap_repricing", "par-swap residual exceeds numerical tolerance", "REVIEW_REQUIRED")
            price_errors[str(tenor)] = price - 1
            knot_logs[tenor] = math.log(discounts[-1])
            previous = tenor
    else:
        require(coupon_frequency is None, "coupon_frequency", "omit frequency for zero-coupon inputs")
        for tenor in tenors:
            require(rates[tenor] > -1, "zero_rate", "annual zero rate must exceed -1")
            knot_logs[tenor] = -tenor * math.log1p(rates[tenor])

    knots = [0, *tenors]

    def log_discount(t):
        if t in knot_logs:
            return knot_logs[t]
        index = bisect.bisect_left(knots, t)
        left, right = knots[index - 1], knots[index]
        weight = (t - left) / (right - left)
        return math.fsum(((1 - weight) * knot_logs[left], weight * knot_logs[right]))

    stress_nodes = {}

    def scenario_log_discount(t):
        if interest_stress is None or t == 0:
            return log_discount(t)
        from .interest_future import interest_down_stress_2027
        if t not in stress_nodes:
            original_spot = math.expm1(-log_discount(t) / t)
            # Art167(2a)b explicitly applies paragraph2 also to the liquid
            # maturities beyond FSP used for LLFR. Keep the ORIGINAL weights.
            stressed = interest_down_stress_2027(original_spot, t, max(fsp, t),
                qualification_reference=qualification_reference, context=context)
            stress_nodes[t] = {"base_spot": original_spot, "stressed_spot": stressed.value}
        return -t * math.log1p(stress_nodes[t]["stressed_spot"])

    base_ufr = ultimate
    if interest_stress is not None:
        from .interest_future import interest_ufr_stress_2027
        ultimate = interest_ufr_stress_2027(ultimate, "down", context=context).value

    later = [t for t in tenors if t > fsp]
    if later:
        exact_keys(average_notionals, [str(t) for t in [fsp, *later]], "average_notionals")
        forward_inputs = {str(t): {"forward_rate": (scenario_log_discount(fsp) - scenario_log_discount(t)) / (t - fsp),
                                  "average_notional": average_notionals[str(t)]} for t in later}
        fsp_notional = average_notionals[str(fsp)]
    else:
        require(average_notionals is None, "average_notionals", "omit unused notionals when FSP is last tenor")
        forward_inputs, fsp_notional = {}, None
    llfr = rfr_last_liquid_forward_2027(
        scenario_log_discount(fsp - 1) - scenario_log_discount(fsp), forward_inputs,
        liquid_swaps_beyond_fsp=bool(later), fsp_average_notional=fsp_notional,
        apply_volatility_adjustment=volatility_adjustment is not None,
        volatility_adjustment=math.log1p(va) if volatility_adjustment is not None else None,
        qualification_reference=qualification_reference, context=context)
    alpha, alpha_details = _alpha(phase_in, approval_reference, context)
    omega, continuous_va = math.log1p(ultimate), math.log1p(va)
    fsp_intensity = -scenario_log_discount(fsp) / fsp + continuous_va

    def node(t):
        if t <= fsp:
            intensity = -knot_logs[tenors[0]] / tenors[0] if t == 0 else -scenario_log_discount(t) / t
            intensity += continuous_va
            average_forward = None
        else:
            horizon = t - fsp
            product = alpha * horizon
            weight = 1.0 if product == 0 else -math.expm1(-product) / product
            average_forward = math.fsum((weight * llfr.value, (1 - weight) * omega))
            # Same weighted-intensity composition as the existing isolated
            # rfr_extrapolated_forward/spot_2027 APIs; no per-node recalibration.
            intensity = math.fsum(((fsp / t) * fsp_intensity, (horizon / t) * average_forward))
        spot = math.expm1(intensity) + ma
        before_floor = spot
        if interest_stress is not None:
            from .interest_future import interest_down_floor_2027
            # The paragraph1 floor also applies to the extrapolated curve.
            spot = max(spot, interest_down_floor_2027(t, context=context).value)
        require(math.isfinite(spot) and spot > -1, "spot", "unrepresentable adjusted annual spot", "REVIEW_REQUIRED")
        discount = math.exp(-t * math.log1p(spot))
        require(math.isfinite(discount) and discount > 0, "discount_factor", "unrepresentable discount factor", "REVIEW_REQUIRED")
        return {"maturity": t, "annual_spot": spot, "discount_factor": discount,
                "spot_before_final_floor": before_floor if interest_stress is not None else None,
                "average_forward_from_fsp_before_ma": average_forward}

    primary = node(target)
    curve = [node(t) for t in grid]
    return primary["annual_spot"], {
        "primary_node": primary, "curve": curve,
        "instrument_kind": instrument_kind, "market_tenors": tenors, "swap_price_residuals": price_errors,
        "bootstrapped_market_spots": {str(t): math.expm1(-knot_logs[t] / t) for t in tenors},
        "first_smoothing_point": fsp, "llfr_calculation": llfr.to_dict(),
        "alpha": alpha, "alpha_details": alpha_details, "ufr": ultimate,
        "interest_stress": interest_stress, "base_ufr": base_ufr,
        "stressed_liquid_nodes": {str(t): row for t, row in sorted(stress_nodes.items())},
        "llfr_base_weights_preserved": interest_stress is not None,
        "volatility_adjustment": volatility_adjustment, "continuous_volatility_adjustment": continuous_va,
        "matching_adjustment": matching_adjustment,
        "adjustment_application_status": "EXTERNAL_UNVERIFIED",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": ("qualified_2027_down_basic_curve_not_BOF_revaluation" if interest_stress is not None
                  else "qualified_2027_curve_construction_not_official_market_selection_or_approval"),
        "_sources": ["SRC-0211:8.1-8.5;AnnexD;10.1-10.2;11.1", "DIR:article-77d:5"]
                    + (["DR:article-167:1-2a"] if interest_stress is not None else []),
    }
