"""One shared, qualified insurer-solvency ratio for spread and default rules."""
from fractions import Fraction
import sys

from .core import Context, calculation, effective_resource, number, require


@calculation("DR:article-180:4", "DR:article-182:6", "DR:article-199:3", unit="ratio")
def counterparty_solvency_ratio(eligible_own_funds: float, scr: float, *,
                                qualification_reference: str, context: Context):
    """Divide externally qualified latest eligible funds by latest positive SCR.

    Values must refer to the correct counterparty, currency and unit. Their
    recency and regulatory eligibility are not established by this division.
    Signed funds are preserved; neither MCR compliance nor a rating is inferred.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "latest eligible own funds and SCR qualification required", "MISSING_INPUT")
    funds = number(eligible_own_funds, "eligible_own_funds")
    capital = number(scr, "scr", 0)
    require(capital > 0, "scr", "zero SCR does not define this ratio", "REVIEW_REQUIRED")
    exact = Fraction(str(funds)) / Fraction(str(capital))
    require(abs(exact) <= Fraction(str(sys.float_info.max)), "solvency_ratio",
            "quotient outside finite numeric range", "REVIEW_REQUIRED")
    value = float(exact)
    require(value != 0 or funds == 0, "solvency_ratio", "nonzero quotient lost to underflow", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return value, {
        "eligible_own_funds": funds, "scr": capital, "zero_floor_applied": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "latest_values_verified": False, "own_funds_eligibility_verified": False,
        "mcr_compliance_inferred": False, "rating_assigned": False,
        "scope": "latest_qualified_values_ratio_not_counterparty_classification",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":" + ref
                     for ref in ("article-180-4", "article-182-6", "article-199-3")]}
