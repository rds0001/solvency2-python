"""Specified UFR arithmetic from qualified observations, not economic modelling."""

import math
from collections.abc import Mapping
from fractions import Fraction

from .core import Context, calculation, exact_keys, number, require, scalar


def _decimal(value, name):
    return Fraction(str(number(value, name)))


@calculation("DR:article-47:1-2", unit="rate")
def rfr_ultimate_forward_rate(annual_rates: Mapping, previous_real_rate: float,
                             previous_ufr: float, inflation: Mapping, *,
                             qualification_reference: str, context: Context):
    """Derive the context year's UFR using the prior year's annual calculation.

    Annual history ends one year before that calculation, hence two years
    before application. AMECO/OECD source qualification and any no-target
    ARMA projection remain external. No term premium is added. Fractions
    preserve decimal grid/threshold boundaries and never fill missing years.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external data and inflation qualification required", "MISSING_INPUT")
    future = context.validate().get("methods", {}).get("volatility_adjustment") == "VA_2027"
    source = "SRC-0211:AnnexC" if future else "SRC-0205:AnnexE"

    def parameter(key):
        return _decimal(scalar("rfr_ufr_" + key, context), key)

    start = parameter("history_start_year")
    require(start.denominator == 1 and start > 0, "history_start_year", "positive integer year required")
    application_year = int(context.as_of[:4])
    calculation_year = application_year - 1
    require(calculation_year > start, "application_year", "history must precede annual calculation")
    years = [str(year) for year in range(int(start), calculation_year)]
    exact_keys(annual_rates, years, "annual_rates")
    countries = ("BE", "DE", "FR", "IT", "NL", "GB", "US")
    annual_real = {}
    for year in years:
        exact_keys(annual_rates[year], countries, year)
        real = []
        for country in countries:
            row = annual_rates[year][country]
            exact_keys(row, ("nominal_rate", "inflation_rate"), year + "." + country)
            nominal = _decimal(row["nominal_rate"], "nominal_rate")
            observed_inflation = _decimal(row["inflation_rate"], "inflation_rate")
            require(observed_inflation > -1, "inflation_rate", "observed inflation must exceed -1")
            real.append((nominal - observed_inflation) / (1 + observed_inflation))
        annual_real[year] = sum(real) / len(countries)
    mean = sum(annual_real.values()) / len(years)
    previous_real = _decimal(previous_real_rate, "previous_real_rate")
    rounding = parameter("real_rounding")
    require(rounding > 0 and (previous_real / rounding).denominator == 1,
            "previous_real_rate", "previous rounded real rate must lie on positive rounding grid")
    rounded = (math.ceil(mean / rounding) if mean < previous_real else math.floor(mean / rounding)) * rounding
    require(isinstance(inflation, Mapping), "inflation", "explicit inflation selection required")
    mode = inflation.get("mode")
    require(mode in {"target", "corridor", "no_target"}, "inflation.mode", "target, corridor or no_target required")
    low, middle, high, top = [parameter("inflation_" + k) for k in ("low", "middle", "high", "top")]
    require(low < middle < high < top, "inflation_buckets", "strictly ordered inflation buckets required")
    target = None
    history_mean = None
    projection = None
    if mode == "target":
        exact_keys(inflation, ("mode", "target"), "inflation")
        target = _decimal(inflation["target"], "inflation.target")
    elif mode == "corridor":
        exact_keys(inflation, ("mode", "lower", "upper"), "inflation")
        lower, upper = (_decimal(inflation[k], "inflation." + k) for k in ("lower", "upper"))
        require(lower <= upper, "inflation.corridor", "ordered corridor required")
        target = (lower + upper) / 2
    if target is not None:
        expected_inflation = low if target <= low else middle if target < high else high if target < top else top
    else:
        exact_keys(inflation, ("mode", "history", "arma_projection", "history_and_arma_support", "expected_long_term"), "inflation")
        count = parameter("inflation_history_years")
        require(count.denominator == 1 and count > 0, "inflation_history_years", "positive integer window required")
        history = inflation["history"]
        require(isinstance(history, Mapping), "inflation.history", "dated annual inflation history required")
        keys = [str(y) for y in range(calculation_year - int(count), calculation_year)]
        exact_keys(history, keys, "inflation.history")
        values = [_decimal(history[y], "inflation.history." + y) for y in keys]
        require(all(x > -1 for x in values), "inflation.history", "inflation must exceed -1")
        history_mean = sum(values) / len(values)
        projection = _decimal(inflation["arma_projection"], "arma_projection")
        support = inflation["history_and_arma_support"]
        require(isinstance(support, bool), "history_and_arma_support", "explicit external support assessment required", "REVIEW_REQUIRED")
        if support:
            expected = _decimal(inflation["expected_long_term"], "expected_long_term")
            deviation, step = parameter("inflation_exception_deviation"), parameter("inflation_exception_rounding")
            require(deviation > 0 and step > 0, "inflation_exception_parameters", "positive thresholds required")
            require(abs(expected - middle) >= deviation, "expected_long_term", "exception must differ by the specified minimum", "REVIEW_REQUIRED")
            expected_inflation = math.floor(expected / step) * step
        else:
            require(inflation["expected_long_term"] is None, "expected_long_term", "omit unused exception input")
            expected_inflation = middle
    raw = rounded + expected_inflation
    previous = _decimal(previous_ufr, "previous_ufr")
    require(previous > -1, "previous_ufr", "annual UFR must exceed -1")
    step = parameter("annual_change")
    require(step > 0, "annual_change", "positive annual step required")
    change = step if raw >= previous + step else -step if raw <= previous - step else Fraction(0)
    value = previous + change
    require(value > -1, "ufr", "derived annual UFR must exceed -1", "REVIEW_REQUIRED")
    return float(value), {
        "application_year": application_year, "calculation_year": calculation_year,
        "history_start_year": int(start), "history_end_year": calculation_year - 1,
        "annual_real_rates": {year: float(rate) for year, rate in annual_real.items()},
        "unrounded_real_rate": float(mean), "rounded_real_rate": float(rounded),
        "previous_real_rate": float(previous_real), "real_rounding": float(rounding),
        "inflation_mode": mode, "inflation_target_or_midpoint": None if target is None else float(target),
        "inflation_history_mean": None if history_mean is None else float(history_mean),
        "arma_projection": None if projection is None else float(projection),
        "expected_inflation": float(expected_inflation), "unlimited_ufr": float(raw),
        "previous_ufr": float(previous), "annual_step": float(step), "annual_change": float(change),
        "term_premium": 0, "method_source": source,
        "required_nominal_source_basis": "OECD_KEY_SHORT_TERM_INDICATORS" if future else "AMECO",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "specified_ufr_arithmetic_not_official_publication_or_arma_estimation", "_sources": [source],
    }
