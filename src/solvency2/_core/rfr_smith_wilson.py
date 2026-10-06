"""Historical Smith-Wilson construction; not market selection or official curves.

EIOPA-BoS-24-533 sections 9.4 and 9.7–9.15. All cashflows and prices must
already reflect the externally qualified currency/credit adjustments.
"""

import math

from .core import Context, calculation, number, require, scalar


def _h(v, u, alpha):
    low = min(u, v)
    return alpha * low + 0.5 * math.exp(-alpha * abs(u - v)) * math.expm1(-2 * alpha * low)


def _g(v, u, alpha):
    # Derivative in v; nonpositive exponential arguments avoid sinh overflow.
    if v <= u:
        return alpha * (-math.expm1(-alpha * (u - v)) - math.expm1(-alpha * (u + v))) / 2
    return -alpha * math.exp(-alpha * (v - u)) * math.expm1(-2 * alpha * u) / 2


def _solve(matrix, rhs):
    """Scaled partial pivot elimination, with no silent regularization."""
    n = len(rhs)
    a = [list(row) + [value] for row, value in zip(matrix, rhs)]
    scales = [max(map(abs, row)) for row in matrix]
    require(all(s > 0 and math.isfinite(s) for s in scales), "instruments",
            "singular or unrepresentable calibration system", "REVIEW_REQUIRED")
    for k in range(n):
        pivot = max(range(k, n), key=lambda i: abs(a[i][k]) / scales[i])
        require(abs(a[pivot][k]) / scales[pivot] > 1e-14, "instruments",
                "singular or numerically unresolved calibration system", "REVIEW_REQUIRED")
        a[k], a[pivot] = a[pivot], a[k]
        scales[k], scales[pivot] = scales[pivot], scales[k]
        for i in range(k + 1, n):
            factor = a[i][k] / a[k][k]
            for j in range(k + 1, n + 1):
                a[i][j] -= factor * a[k][j]
            a[i][k] = 0.0
    result = [0.0] * n
    for i in range(n - 1, -1, -1):
        result[i] = (a[i][n] - math.fsum(a[i][j] * result[j] for j in range(i + 1, n))) / a[i][i]
    require(all(math.isfinite(x) for x in result), "calibration", "nonfinite solution", "REVIEW_REQUIRED")
    return result


def _sequence(value, name):
    require(isinstance(value, (list, tuple)), name, "explicit list or tuple required")
    return value


@calculation("DR:article-43:1-2", "DR:article-44:1", "DR:article-46:1", unit="rate")
def rfr_smith_wilson_spot(payment_times, cashflows, prices, maturity, *, ufr,
                         qualification_reference: str, output_maturities=(),
                         alpha_search_max=2.0, volatility_adjustment=None,
                         matching_adjustment=None, context: Context):
    """Fit qualified instruments once and return annual spot plus optional grid.

    Cashflow rows are payment dates, columns are instruments. Prices share
    their cashflows' nominal basis. Signed coupons are allowed (section9.15).
    The last payment time is the externally qualified LLP. Qualification
    includes DLT selection, input availability, dates, CRA and currency basis.
    Alpha search is the documented heuristic, not a global optimality proof.
    The technical search bound is explicit and is NOT a regulatory alpha cap.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external market/UFR/LLP qualification required", "MISSING_INPUT")
    times = [number(x, "payment_times", 0) for x in _sequence(payment_times, "payment_times")]
    require(bool(times) and times[0] > 0 and all(a < b for a, b in zip(times, times[1:])),
            "payment_times", "strictly positive increasing payment times required")
    observed = [number(x, "prices", 0) for x in _sequence(prices, "prices")]
    require(bool(observed) and all(x > 0 for x in observed), "prices", "positive instrument prices required")
    rows = _sequence(cashflows, "cashflows")
    require(len(rows) == len(times), "cashflows", "one row per payment date required")
    c = [[number(x, "cashflows") for x in _sequence(row, "cashflows.row")] for row in rows]
    n = len(observed)
    require(all(len(row) == n for row in c) and n <= len(times), "cashflows", "consistent identifiable instrument columns required")
    require(all(any(row) for row in c), "cashflows", "omit unused payment dates, including false LLP")
    require(all(any(row[j] for row in c) for j in range(n)), "cashflows", "nonempty instrument columns required")
    ultimate = number(ufr, "ufr")
    require(ultimate > -1, "ufr", "annual UFR must exceed -1")
    omega = math.log1p(ultimate)
    target = number(maturity, "maturity", 0)
    grid = [number(x, "output_maturities", 0) for x in _sequence(output_maturities, "output_maturities")]
    require(len(set(grid)) == len(grid), "output_maturities", "unique maturities required")
    require(volatility_adjustment is None or matching_adjustment is None,
            "adjustments", "VA and MA cannot apply to the same obligations")
    if volatility_adjustment is not None or matching_adjustment is not None:
        return _adjusted(times, c, observed, target, ultimate, grid,
                         volatility_adjustment, matching_adjustment,
                         qualification_reference, alpha_search_max, context)
    floor = number(scalar("rfr_sw_alpha_floor", context), "alpha_floor", 0)
    tolerance = number(scalar("rfr_sw_convergence_tolerance", context), "convergence_tolerance", 0)
    digits = number(scalar("rfr_sw_alpha_digits", context), "alpha_digits", 0)
    require(floor > 0 and tolerance > 0 and digits.is_integer() and 0 <= digits <= 9,
            "convergence_parameters", "positive floor/tolerance and supported integer precision required")
    scale = 10 ** int(digits)
    require(math.isclose(floor * scale, round(floor * scale), abs_tol=1e-9, rel_tol=0),
            "alpha_floor", "floor must lie on selected decimal grid")
    bound = number(alpha_search_max, "alpha_search_max", floor)
    if context.currency == "SEK":
        period = number(scalar("rfr_sw_sek_convergence_period", context), "convergence_period", 0)
        convergence = times[-1] + period
    else:
        period = number(scalar("rfr_sw_convergence_period", context), "convergence_period", 0)
        point = number(scalar("rfr_sw_convergence_point", context), "convergence_point", 0)
        convergence = max(times[-1] + period, point)
    require(period > 0 and math.isfinite(convergence), "convergence_point", "finite point beyond LLP required")
    discounts = [math.exp(-omega * u) for u in times]
    q = [[d * x for x in row] for d, row in zip(discounts, c)]
    rhs = [observed[j] - math.fsum(row[j] for row in q) for j in range(n)]
    evaluations = 0

    def fit(alpha):
        nonlocal evaluations
        evaluations += 1
        h = [[_h(v, u, alpha) for u in times] for v in times]
        hq = [[math.fsum(hrow[k] * q[k][j] for k in range(len(times))) for j in range(n)] for hrow in h]
        system = [[math.fsum(q[k][i] * hq[k][j] for k in range(len(times))) for j in range(n)] for i in range(n)]
        b = _solve(system, rhs)
        beta = [math.fsum(x * y for x, y in zip(row, b)) for row in q]
        factor = 1 + math.fsum(_h(convergence, u, alpha) * x for u, x in zip(times, beta))
        require(factor > 0 and math.isfinite(factor), "convergence_discount",
                "nonpositive or nonfinite convergence discount factor", "REVIEW_REQUIRED")
        gap = abs(math.fsum(_g(convergence, u, alpha) * x for u, x in zip(times, beta)) / factor)
        require(math.isfinite(gap), "convergence_gap", "nonfinite convergence gap", "REVIEW_REQUIRED")
        return beta, gap

    alpha = floor
    beta, gap = fit(alpha)
    if gap > tolerance:
        # Decimal refinement: first bracket on a 0.1 grid, then refine the
        # first passing interval down to the profile's precision. This is a
        # heuristic under ordinary curve inputs; arbitrary nonmonotonic
        # feasible islands between scan points are not certified absent.
        low = round(floor * scale)
        high = None
        step = max(1, scale // 10)
        max_tick = math.floor(bound * scale)
        while high is None:
            tick = min(low + step, max_tick)
            require(tick > low, "alpha_search_max", "no converged alpha within explicit search bound", "REVIEW_REQUIRED")
            candidate, candidate_gap = fit(tick / scale)
            if candidate_gap <= tolerance:
                high, beta, gap = tick, candidate, candidate_gap
            else:
                low = tick
        while high - low > 1:
            step = max(1, step // 10)
            while low + step < high:
                tick = low + step
                candidate, candidate_gap = fit(tick / scale)
                if candidate_gap <= tolerance:
                    high, beta, gap = tick, candidate, candidate_gap
                    break
                low = tick
        alpha = high / scale

    def node(v):
        factor = 1 + math.fsum(_h(v, u, alpha) * x for u, x in zip(times, beta))
        require(factor > 0 and math.isfinite(factor), "discount_factor", "nonpositive or nonfinite curve value", "REVIEW_REQUIRED")
        forward = omega - math.fsum(_g(v, u, alpha) * x for u, x in zip(times, beta)) / factor
        intensity = forward if v == 0 else omega - math.log(factor) / v
        spot = math.expm1(intensity)
        discount = math.exp(-v * intensity)
        require(discount > 0 and all(math.isfinite(x) for x in (spot, discount, forward)),
                "curve", "unrepresentable curve node", "REVIEW_REQUIRED")
        return {"maturity": v, "annual_spot": spot, "discount_factor": discount, "forward_intensity": forward}

    payment_nodes = [node(v) for v in times]
    fitted = [math.fsum(c[i][j] * payment_nodes[i]["discount_factor"] for i in range(len(times))) for j in range(n)]
    errors = [abs(a - b) / max(1, abs(a)) for a, b in zip(observed, fitted)]
    require(max(errors) <= 1e-9, "instrument_repricing", "calibration residual exceeds numerical tolerance", "REVIEW_REQUIRED")
    primary = node(target)
    return primary["annual_spot"], {
        "primary_node": primary, "curve": [node(v) for v in grid],
        "alpha": alpha, "alpha_floor": floor, "alpha_digits": int(digits),
        "alpha_search_max": bound, "calibration_evaluations": evaluations,
        "alpha_search_method": "DECIMAL_REFINEMENT_HEURISTIC_NOT_GLOBAL_CERTIFICATE",
        "ufr": ultimate, "last_liquid_point": times[-1], "convergence_point": convergence,
        "convergence_gap": gap, "convergence_tolerance": tolerance,
        "fitted_prices": fitted, "max_scaled_repricing_error": max(errors),
        "method_source": "SRC-0205:9.4;9.7-9.15;AnnexD",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "historical_qualified_instrument_curve_not_official_publication_or_market_selection",
        "adjustment_status": "INPUTS_ALREADY_CRA_CURRENCY_ADJUSTED_NO_AUTOMATIC_VA_MA",
    }


def _adjusted(times, cashflows, prices, target, ufr, grid, va, ma, reference, bound, context):
    common = {"ufr": ufr, "qualification_reference": reference,
              "alpha_search_max": bound, "context": context}
    if va is not None:
        adjustment = number(va, "volatility_adjustment")
        require(math.isclose(adjustment * 10000, round(adjustment * 10000), rel_tol=0, abs_tol=1e-8),
                "volatility_adjustment", "qualified VA rounded to whole basis points required")
        require(times[-1].is_integer(), "last_liquid_point", "integer LLP required by annual zero-coupon VA route", "REVIEW_REQUIRED")
        liquid = list(range(1, int(times[-1]) + 1))
        basic = rfr_smith_wilson_spot(times, cashflows, prices, target, output_maturities=liquid, **common)
        shifted = [node["annual_spot"] + adjustment for node in basic.details["curve"]]
        require(all(x > -1 for x in shifted), "va_spots", "shifted annual spots must exceed -1")
        zero_prices = [math.exp(-v * math.log1p(rate)) for v, rate in zip(liquid, shifted)]
        zero_cashflows = [[int(i == j) for j in liquid] for i in liquid]
        adjusted = rfr_smith_wilson_spot(liquid, zero_cashflows, zero_prices, target, output_maturities=grid, **common)
        return adjusted.value, {**adjusted.details, "adjustment_status": "VA_BEFORE_REEXTRAPOLATION",
                               "volatility_adjustment": adjustment, "basic_calibration": basic.to_dict(),
                               "liquid_adjusted_spots": shifted,
                               "adjustment_application_status": "EXTERNAL_UNVERIFIED",
                               "_sources": ["DR:article-46:2", "DIR:article-77d:3", "DIR:article-77d:5", "SRC-0205:15.1.2-6"]}
    adjustment = number(ma, "matching_adjustment")
    basic = rfr_smith_wilson_spot(times, cashflows, prices, target, output_maturities=grid, **common)

    def shift(node):
        spot = node["annual_spot"] + adjustment
        require(spot > -1, "ma_spot", "shifted annual spot must exceed -1")
        discount = math.exp(-node["maturity"] * math.log1p(spot))
        # Differentiate the shifted annual-spot discount curve, not f+MA.
        forward = math.log1p(spot) + ((1 + node["annual_spot"]) / (1 + spot)) * (
            node["forward_intensity"] - math.log1p(node["annual_spot"]))
        require(discount > 0 and all(math.isfinite(x) for x in (spot, discount, forward)),
                "ma_curve", "unrepresentable shifted curve", "REVIEW_REQUIRED")
        return {"maturity": node["maturity"], "annual_spot": spot,
                "discount_factor": discount, "forward_intensity": forward}

    primary = shift(basic.details["primary_node"])
    return primary["annual_spot"], {"primary_node": primary,
                                  "curve": [shift(node) for node in basic.details["curve"]],
                                  "matching_adjustment": adjustment, "basic_calibration": basic.to_dict(),
                                  "adjustment_status": "MA_AFTER_EXTRAPOLATION",
                                  "adjustment_application_status": "EXTERNAL_UNVERIFIED",
                                  "_sources": ["DR:article-46:3", "DIR:article-77d:5", "SRC-0205:10.6"]}
