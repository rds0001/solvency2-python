"""Shared payment-date/discount-factor validation, without curve construction."""
from datetime import date

from .core import number, require


def payment_discount_factor(label, value, context):
    """Require a future canonical payment date and its externally supplied factor."""
    try:
        payment_date = date.fromisoformat(label)
    except (TypeError, ValueError):
        require(False, "cashflows.date", "ISO YYYY-MM-DD payment date required")
    require(label == payment_date.isoformat(), "cashflows.date", "canonical ISO date required")
    valuation_date = date.fromisoformat(context.as_of)
    require(payment_date >= valuation_date, label, "past cashflow outside future runoff")
    factor = number(value, f"{label}.discount_factor", 0)
    require(factor > 0, f"{label}.discount_factor", "strictly positive discount factor required")
    require(payment_date != valuation_date or factor == 1, f"{label}.discount_factor",
            "discount factor at valuation date must be one")
    return factor
