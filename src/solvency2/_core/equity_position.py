"""Article169 position decrease; not short pricing, balance valuation or SCR."""
from .core import Context, calculation, number, require
from .evidence import _declared_bool, _reference


@calculation("DR:article-169:5")
def equity_stress_amount_2027(equity_value: float, shock: float, *, short_position: bool,
                              losses_can_exceed_investment: bool,
                              qualification_reference: str, context: Context):
    """Apply an externally qualified169 factor to the prescribed position basis.

    A negative investment with losses beyond the invested amount uses its
    absolute value; other negative non-short investments have a zero stress
    basis, not a zero balance-sheet value. Short pricing is deliberately not
    inferred from a signed value or from the absolute-value exception.
    """
    _reference(qualification_reference, "qualification_reference")
    value = number(equity_value, "equity_value")
    factor = number(shock, "shock", 0, 1)
    short = _declared_bool(short_position, "short_position")
    beyond = _declared_bool(losses_can_exceed_investment, "losses_can_exceed_investment")
    require(not short, "short_position", "short positions require qualified instrument revaluation",
            "UNSUPPORTED_METHOD")
    basis = value if value >= 0 else abs(value) if beyond else 0.0
    return basis * factor, {"equity_value": value, "shock": factor, "stress_basis": basis,
        "basis_rule": "nonnegative" if value >= 0 else "absolute" if beyond else "zero",
        "short_position": short, "losses_can_exceed_investment": beyond,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "article169_position_decrease_only_not_balance_value_or_bof_capital"}
