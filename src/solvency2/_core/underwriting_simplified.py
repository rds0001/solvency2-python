"""Printed life/health capital simplifications, not insurer projection models.

The same arithmetic serves distinct source articles; parameters and provenance
remain article-specific. Article88 and all weighted input bases are external.
"""
import math
from decimal import Decimal, DecimalException, localcontext
from typing import Mapping

from .capital import _contract_capital_at_risk
from .core import Context, calculation, exact_keys, number, require, scalar


def _qualification(kind, allowed, satisfied, reference):
    require(isinstance(kind, str) and kind in allowed, "kind", "supported explicit kind required",
            "UNSUPPORTED_METHOD")
    require(satisfied is not None, "proportionality_satisfied", "Article88 assessment unresolved",
            "REVIEW_REQUIRED")
    require(isinstance(satisfied, bool), "proportionality_satisfied", "explicit boolean required")
    require(satisfied, "proportionality_satisfied", "Article88 conditions not satisfied", "UNSUPPORTED_METHOD")
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "Article88, contract scope and weighted input basis reference required", "MISSING_INPUT")
    return {"kind": kind, "qualification_reference": reference,
            "qualification_status": "EXTERNAL_UNVERIFIED", "proportionality_satisfied": satisfied,
            "scope": "simplified_capital_component_not_projection_or_total_scr"}


def _finite(value):
    result = float(value)
    require(math.isfinite(result) and result >= 0, "result",
            "negative or unrepresentable capital requires review; no implicit floor", "REVIEW_REQUIRED")
    return result


@calculation()
def simplified_lapse_risk(contracts: Mapping, average_lapse_rate: float, runoff_period: float, *,
                          kind: str, direction: str, proportionality_satisfied: bool | None,
                          qualification_reference: str, context: Context):
    """Art95/102 up: half * max(qualified rate, source threshold) * years * S+.

    Each contract provides termination_payment_net (after amounts recoverable
    from the policyholder/intermediary) and technical_provisions_excluding_rm.
    Negative strains never offset positive ones. Rate and period must describe
    the positive-strain population. The printed down formula has an unresolved
    sign issue and is deliberately not converted to positive capital.
    """
    details = _qualification(kind, {"life", "health_slt"}, proportionality_satisfied, qualification_reference)
    article = "95" if kind == "life" else "102"
    require(direction in ("up", "down"), "direction", "up or down required")
    require(direction == "up", "direction", "printed negative Sdown capital requires source qualification",
            "REVIEW_REQUIRED")
    rate = number(average_lapse_rate, "average_lapse_rate", 0, 1)
    period = number(runoff_period, "runoff_period", 0)
    require(isinstance(contracts, Mapping), "contracts", "explicit contract mapping required", "MISSING_INPUT")
    strains = {}
    for key, row in contracts.items():
        require(isinstance(key, str) and bool(key.strip()), "contracts", "nonempty contract identifiers required")
        exact_keys(row, ["termination_payment_net", "technical_provisions_excluding_rm"], f"contracts/{key}")
        payment = number(row["termination_payment_net"], f"contracts/{key}/termination_payment_net")
        tp = number(row["technical_provisions_excluding_rm"], f"contracts/{key}/technical_provisions_excluding_rm")
        strain = payment - tp
        require(math.isfinite(strain), "strain", "unrepresentable contract strain", "REVIEW_REQUIRED")
        strains[key] = strain
    threshold = number(scalar(f"simplified_{article}_up_minimum", context), "up_minimum", 0, 1)
    factor = number(scalar(f"simplified_{article}_factor", context), "factor", 0)
    effective_rate = max(rate, threshold)  # Both supplied DE/EN sources say higher, not lower.
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            total = sum((Decimal(str(v)) for v in strains.values() if v > 0), Decimal(0))
            result = _finite(Decimal(str(factor)) * Decimal(str(effective_rate)) * Decimal(str(period)) * total)
            positive_sum = _finite(total)
    except (DecimalException, OverflowError):
        require(False, "result", "simplified lapse result not representable", "REVIEW_REQUIRED")
    return result, {**details, "direction": direction, "contract_strains": strains,
                    "selected_contracts": [k for k, v in strains.items() if v > 0],
                    "positive_strain_sum": positive_sum, "effective_lapse_rate": effective_rate,
                    "runoff_period": period, "factor": factor,
                    "_sources": ["DR:article-88", f"DR:article-{article}"]}


@calculation()
def simplified_capital_at_risk(contracts: Mapping, *, kind: str,
                               proportionality_satisfied: bool | None,
                               qualification_reference: str, context: Context):
    """Sum per-contract max(current net benefit + additional future PV - net BE,0).

    Inputs refer to the year/event specified by the chosen article. A net
    portfolio difference is not a substitute for individually floored contracts.
    """
    articles = {"life_mortality": "91", "health_mortality": "97", "life_disability": "93",
                "health_income": "100", "life_catastrophe": "96"}
    details = _qualification(kind, articles, proportionality_satisfied, qualification_reference)
    value, contract_details = _contract_capital_at_risk(contracts, qualification_reference=qualification_reference)
    return value, {**contract_details, **details,
                   "scope": "qualified_contract_capital_at_risk_not_scr_or_projection",
                   "_sources": ["DR:article-88", f"DR:article-{articles[kind]}"]}


@calculation()
def simplified_mortality_risk(capital_at_risk: list[float], basic_spot_rates: list[float],
                              mortality_rate: float, modified_duration: float, *, kind: str,
                              proportionality_satisfied: bool | None,
                              qualification_reference: str, context: Context):
    """Art91/97 finite annual sum with midyear discount and survival weighting.

    q is the sum-assured weighted rate over all future years, unlike longevity.
    The printed upper index is modified duration: fractional values remain
    unqualified, never silently rounded, truncated or prorated.
    """
    details = _qualification(kind, {"life", "health"}, proportionality_satisfied, qualification_reference)
    article = "91" if kind == "life" else "97"
    n = number(modified_duration, "modified_duration", 0)
    require(n.is_integer(), "modified_duration", "fractional summation horizon requires source qualification",
            "REVIEW_REQUIRED")
    require(isinstance(capital_at_risk, (list, tuple)) and isinstance(basic_spot_rates, (list, tuple)),
            "projection", "ordered explicit annual vectors required", "MISSING_INPUT")
    require(len(capital_at_risk) == len(basic_spot_rates) == n, "projection",
            "one CAR and basic spot rate for every year through duration required")
    q = number(mortality_rate, "mortality_rate", 0, 1)
    cars = [number(v, f"capital_at_risk[{k}]", 0) for k, v in enumerate(capital_at_risk)]
    rates = [number(v, f"basic_spot_rates[{k}]") for k, v in enumerate(basic_spot_rates)]
    require(all(r > -1 for r in rates), "basic_spot_rates", "positive discount base required")
    factor = number(scalar(f"simplified_{article}_factor", context), "factor", 0)
    offset = number(scalar(f"simplified_{article}_discount_offset", context), "discount_offset", 0, 1)
    terms = []
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            dq, df, do = map(lambda x: Decimal(str(x)), (q, factor, offset))
            for k, (car, rate) in enumerate(zip(cars, rates), 1):
                survival = Decimal(1) if k == 1 else (1 - dq) ** (k - 1)
                # q=1 means no later survivors; avoid Decimal's undefined0**0 at k1.
                term = Decimal(0) if not car or not survival or not dq or not df else (
                    df * dq * Decimal(str(car)) * survival /
                    (1 + Decimal(str(rate))) ** (Decimal(k) - do))
                terms.append(term)
            result = _finite(sum(terms, Decimal(0)))
    except (DecimalException, OverflowError):
        require(False, "result", "simplified mortality result not representable", "REVIEW_REQUIRED")
    return result, {**details, "annual_charges": [float(t) for t in terms], "mortality_rate": q,
                    "modified_duration": n, "discount_offset": offset, "factor": factor,
                    "rate_horizon": "ALL_FUTURE_YEARS_WEIGHTED",
                    "_sources": ["DR:article-88", f"DR:article-{article}"]}


@calculation()
def simplified_disability_risk(capital_at_risk_1: float, capital_at_risk_2: float,
                               incidence_rate_1: float, incidence_rate_2: float,
                               termination_rate: float, modified_duration: float, best_estimate: float, *,
                               kind: str, proportionality_satisfied: bool | None,
                               qualification_reference: str, context: Context):
    """Three printed terms under Art93/100; no period inference or term floors.

    Health Art100(d) has conflicting DE/EN d2 descriptions. The supplied d2
    basis must be explicitly externally qualified; its numeric value is retained.
    """
    details = _qualification(kind, {"life", "health_income"}, proportionality_satisfied, qualification_reference)
    article = "93" if kind == "life" else "100"
    names = ("capital_at_risk_1", "capital_at_risk_2", "incidence_rate_1", "incidence_rate_2",
             "termination_rate", "modified_duration", "best_estimate")
    values = (capital_at_risk_1, capital_at_risk_2, incidence_rate_1, incidence_rate_2,
              termination_rate, modified_duration, best_estimate)
    checked = [number(v, name, 0, 1 if name in names[2:5] else None) for name, v in zip(names, values)]
    parameters = {key: number(scalar(f"simplified_{article}_{key}", context), key, 0)
                  for key in ("first", "later", "termination", "growth")}
    require(parameters["growth"] > 0, "growth", "positive exponential base required")
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            c1, c2, d1, d2, t, n, be = map(lambda x: Decimal(str(x)), checked)
            first, later, termination, growth = (Decimal(str(parameters[k]))
                                                 for k in ("first", "later", "termination", "growth"))
            terms = [first * c1 * d1,
                     Decimal(0) if not c2 or not d2 or n == 1 or not later else
                     later * growth ** ((n - 3) / 2) * (n - 1) * c2 * d2,
                     Decimal(0) if not t or not n or not be or not termination else
                     termination * growth ** ((n - 1) / 2) * t * n * be]
            result = _finite(sum(terms))
            term_values = [float(term) for term in terms]
            require(all(math.isfinite(v) for v in term_values), "terms",
                    "component values not representable", "REVIEW_REQUIRED")
    except (DecimalException, OverflowError):
        require(False, "result", "simplified disability result not representable", "REVIEW_REQUIRED")
    return result, {**details, "terms": term_values, "parameters": parameters,
                    "d2_basis_status": "EXTERNALLY_QUALIFIED_DE_EN_SOURCE_DIFFERENCE" if kind == "health_income"
                    else "SECOND_TWELVE_MONTHS_EXTERNALLY_QUALIFIED",
                    "_sources": ["DR:article-88", f"DR:article-{article}"]}


@calculation("DR:article-88", "DR:article-96")
def simplified_life_catastrophe_risk(capital_at_risk: float, *, proportionality_satisfied: bool | None,
                                     qualification_reference: str, context: Context):
    """Art96 factor times the already contract-floored CAR sum, not death benefits."""
    details = _qualification("life_catastrophe", {"life_catastrophe"}, proportionality_satisfied,
                             qualification_reference)
    car = number(capital_at_risk, "capital_at_risk", 0)
    factor = number(scalar("simplified_96_factor", context), "factor", 0)
    return _finite(car * factor), {**details, "capital_at_risk": car, "factor": factor}


@calculation()
def simplified_longevity_risk(mortality_rate: float, modified_duration: float, best_estimate: float, *,
                              kind: str, proportionality_satisfied: bool | None,
                              qualification_reference: str, context: Context):
    """Art92/98: factor*q*n*growth**((n-1)/2)*BE on qualified selected contracts.

    q is the sum-assured weighted NEXT-twelve-month mortality rate. Fractional
    modified durations are retained; no invented rounding or contract selection.
    """
    details = _qualification(kind, {"life", "health"}, proportionality_satisfied, qualification_reference)
    article = "92" if kind == "life" else "98"
    q = number(mortality_rate, "mortality_rate", 0, 1)
    n = number(modified_duration, "modified_duration", 0)
    be = number(best_estimate, "best_estimate")
    require(be >= 0, "best_estimate", "negative selected BE needs separate assessment", "REVIEW_REQUIRED")
    factor = number(scalar(f"simplified_{article}_factor", context), "factor", 0)
    growth = number(scalar(f"simplified_{article}_growth", context), "growth", 0)
    require(growth > 0, "growth", "positive exponential base required")
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            dq, dn, db, df, dg = map(lambda x: Decimal(str(x)), (q, n, be, factor, growth))
            value = Decimal(0) if not all((dq, dn, db, df)) else df * dq * dn * dg ** ((dn - 1) / 2) * db
            result = _finite(value)
    except (DecimalException, OverflowError):
        require(False, "result", "simplified longevity result not representable", "REVIEW_REQUIRED")
    return result, {**details, "mortality_rate": q, "modified_duration": n, "best_estimate": be,
                    "factor": factor, "growth_base": growth, "_sources": ["DR:article-88", f"DR:article-{article}"]}


@calculation()
def simplified_expense_risk(previous_year_amount: float, modified_duration: float, inflation_rate: float, *,
                            kind: str, proportionality_satisfied: bool | None,
                            qualification_reference: str, context: Context):
    """Art94/99/101: factor*A*n + A*(G(i+shift,n)-G(i,n)).

    G(r,n)=((1+r)**n-1)/r, continuously extended to G(0,n)=n. The amount is
    last-year expenses (life/health) or medical payments, NOT a projected BE.
    High-precision intermediates avoid cancellation around zero inflation.
    """
    articles = {"life_expense": "94", "health_medical": "99", "health_expense": "101"}
    details = _qualification(kind, articles, proportionality_satisfied, qualification_reference)
    article = articles[kind]
    amount = number(previous_year_amount, "previous_year_amount", 0)
    n = number(modified_duration, "modified_duration", 0)
    rate = number(inflation_rate, "inflation_rate")
    factor = number(scalar(f"simplified_{article}_factor", context), "factor", 0)
    shift = number(scalar(f"simplified_{article}_inflation", context), "inflation_shift", 0)
    require(rate > -1, "inflation_rate", "positive base required for fractional-duration power")
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            da, dn, dr, df, ds = map(lambda x: Decimal(str(x)), (amount, n, rate, factor, shift))

            def growth_sum(r):
                return dn if r == 0 else ((1 + r) ** dn - 1) / r

            increment = Decimal(0) if not da or not dn or not ds else da * (growth_sum(dr + ds) - growth_sum(dr))
            base = df * da * dn
            result = _finite(base + increment)
            base_value, increment_value = float(base), float(increment)
            require(math.isfinite(base_value) and math.isfinite(increment_value), "details",
                    "component values not representable", "REVIEW_REQUIRED")
    except (DecimalException, OverflowError):
        require(False, "result", "simplified expense result not representable", "REVIEW_REQUIRED")
    return result, {**details, "previous_year_amount": amount, "modified_duration": n,
                    "inflation_rate": rate, "level_factor": factor, "inflation_shift": shift,
                    "level_charge": base_value, "inflation_charge": increment_value,
                    "zero_rate_extension": "CONTINUOUS_LIMIT_G_ZERO_EQUALS_DURATION",
                    "_sources": ["DR:article-88", f"DR:article-{article}"]}
