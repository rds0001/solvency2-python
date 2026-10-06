"""2027 interest assumptions only: no silent reconstruction of a complete stressed curve."""
from .core import Context, calculation, effective_resource, number, require, scalar


def _direction(direction):
    require(direction in ("up", "down"), "direction", "up or down required")


def _factor(maturity, direction, column, context):
    _direction(direction)
    maturity = number(maturity, "maturity", 0)
    require(maturity > 0, "maturity", "positive maturity required")
    table = effective_resource("profile.json", context)["tables"]["interest_2027_" + direction]
    rows = table["rows"]
    require([row[0] for row in rows] == list(range(1, 51)), "table", "annual1-50 grid required")
    values = [number(row[column], "factor", 0, 1) for row in rows]
    component = "relative" if column == 1 else "additive"
    tail_year = number(scalar("interest_2027_" + component + "_tail_year", context), "tail_year", 0)
    tail_value = number(scalar("interest_2027_" + component + "_tail", context), "tail_value", 0, 1)
    require(tail_year > 50, "tail_year", "tail must follow the50year table endpoint")
    points = [(row[0], value) for row, value in zip(rows, values)] + [(tail_year, tail_value)]
    if maturity <= 1:
        value, bracket = values[0], [1, 1]
    elif maturity >= tail_year:
        value, bracket = tail_value, [tail_year, tail_year]
    else:
        for (low, lv), (high, hv) in zip(points, points[1:]):
            if low <= maturity <= high:
                value = lv + (hv - lv) * ((maturity - low) / (high - low))
                bracket = [low, high]
                break
    return value, {"direction": direction, "component": component,
        "interpolation_bracket_years": bracket, "tail_year": tail_year,
        "scope": "parameter_only_not_stressed_curve_or_capital", "table_source": table["source"]}


@calculation("DR:article-166:2", "DR:article-167:2", unit="ratio")
def interest_relative_factor_2027(maturity: float, direction: str, *, context: Context):
    """Interpolate s using its own90year tail, not the additive60year tail."""
    return _factor(maturity, direction, 1, context)


@calculation("DR:article-166:2", "DR:article-167:2", unit="annual_rate")
def interest_additive_shift_2027(maturity: float, direction: str, *, context: Context):
    """Return the nonnegative b magnitude; its application sign belongs to the scenario."""
    return _factor(maturity, direction, 2, context)


def _down_floor(maturity, context):
    maturity = number(maturity, "maturity", 0)
    require(maturity > 0, "maturity", "positive maturity required")
    require(maturity >= 1, "maturity", "subannual floor needs source qualification", "REVIEW_REQUIRED")
    low = number(scalar("interest_2027_floor_short", context), "short_floor", -1)
    high = number(scalar("interest_2027_floor_long", context), "long_floor", -1)
    low_year = number(scalar("interest_2027_floor_short_end", context), "short_end", 1)
    high_year = number(scalar("interest_2027_floor_long_start", context), "long_start", 1)
    require(low > -1 and high > -1 and high_year > low_year, "floor", "valid floor endpoints required")
    weight = min(1, max(0, (maturity - low_year) / (high_year - low_year)))
    return low + weight * (high - low), {"scope": "floor_only_not_stressed_curve",
        "short_end_year": low_year, "long_start_year": high_year}


@calculation("DR:article-167:1", unit="annual_rate")
def interest_down_floor_2027(maturity: float, *, context: Context):
    """Published floor from1year; subannual ambiguity is not filled by extrapolation."""
    return _down_floor(maturity, context)


@calculation("DR:article-167:1-2", unit="annual_rate")
def interest_down_stress_2027(rate: float, maturity: float, first_smoothing_point: float, *,
                              qualification_reference: str, context: Context):
    """Literal downward stress only at/before an externally qualified first smoothing point."""
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
        "qualification_reference", "external basic-curve/currency/FSP qualification required", "MISSING_INPUT")
    rate = number(rate, "rate", -1)
    require(rate > -1, "rate", "annual rate must exceed-1")
    maturity = number(maturity, "maturity", 0)
    fsp = number(first_smoothing_point, "first_smoothing_point", 0)
    require(maturity > 0 and fsp > 0, "maturity", "positive maturity and FSP required")
    require(maturity <= fsp, "maturity", "beyond-FSP stress needs separate extrapolation", "UNSUPPORTED_METHOD")
    factor, relative_details = _factor(maturity, "down", 1, context)
    additive, additive_details = _factor(maturity, "down", 2, context)
    floor, _ = _down_floor(maturity, context)
    raw = rate * (1 - factor) - additive
    return max(raw, floor), {"unfloored_rate": raw, "floor": floor, "relative_factor": factor,
        "additive_shift": additive, "relative_interpolation": relative_details,
        "additive_interpolation": additive_details, "first_smoothing_point": fsp,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "basic_rate_down_at_or_before_FSP_only_not_full_curve_or_capital"}


@calculation("DR:article-166:2a:a", "DR:article-167:2a:a", unit="annual_rate")
def interest_ufr_stress_2027(ufr: float, direction: str, *, context: Context):
    """Shift an externally supplied UFR, without constructing a stressed extrapolation."""
    _direction(direction)
    base = number(ufr, "ufr", -1)
    shift = number(scalar("interest_2027_ufr_shift", context), "ufr_shift", 0)
    value = base + shift if direction == "up" else base - shift
    require(base > -1 and value > -1, "ufr", "annual rates must exceed-1")
    return value, {"direction": direction, "absolute_shift": shift,
        "scope": "ufr_assumption_only_not_extrapolated_curve", "input_qualification": "EXTERNAL_INPUT_ONLY"}
