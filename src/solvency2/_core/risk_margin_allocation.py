"""Apply qualified external lifetime shares, not an invented allocation model."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, number, require


@calculation("DR:article-37:3", "DIR:article-80", "DR:annex-I", unit="currency")
def risk_margin_lob_allocation(total_risk_margin: float, allocation_shares: Mapping[str, float],
                               lob: str, *, lifetime_contributions_qualified: bool,
                               complete_scope_confirmed: bool, allocation_reference: str,
                               context: Context):
    """Apply a nonnegative externally qualified share; never infer it from SCR0.

    Shares cover the actual portfolio's LOBs. Omitted unused LOBs are permitted
    only with explicit full-scope confirmation. A1e-12 sum tolerance is numerical,
    not a regulatory materiality threshold; shares are never renormalised.
    Signed allocations are outside this component, not declared legally banned.
    """
    require(lifetime_contributions_qualified is not None, "lifetime_contributions_qualified",
            "lifetime contribution qualification missing", "REVIEW_REQUIRED")
    require(isinstance(lifetime_contributions_qualified, bool), "lifetime_contributions_qualified",
            "explicit boolean required")
    require(lifetime_contributions_qualified, "lifetime_contributions_qualified",
            "qualified lifetime SCR contributions required", "REVIEW_REQUIRED")
    require(complete_scope_confirmed is not None, "complete_scope_confirmed",
            "full actual portfolio scope required", "MISSING_INPUT")
    require(isinstance(complete_scope_confirmed, bool), "complete_scope_confirmed", "explicit boolean required")
    require(complete_scope_confirmed, "complete_scope_confirmed",
            "full actual portfolio scope required", "MISSING_INPUT")
    require(isinstance(allocation_reference, str) and bool(allocation_reference.strip()),
            "allocation_reference", "external allocation basis reference required", "MISSING_INPUT")
    total = number(total_risk_margin, "total_risk_margin", 0)
    require(isinstance(allocation_shares, Mapping) and bool(allocation_shares),
            "allocation_shares", "nonempty share mapping required")
    profile = effective_resource("profile.json", context)
    labels = {row[0] for row in profile["tables"]["technical_provision_lobs"]["rows"]}
    require(all(isinstance(key, str) and key in labels for key in allocation_shares),
            "allocation_shares", "unknown AnnexI line of business", "UNSUPPORTED_PARAMETER")
    require(isinstance(lob, str) and lob in labels, "lob", "unknown AnnexI line of business",
            "UNSUPPORTED_PARAMETER")
    require(lob in allocation_shares, "lob", "selected share must be explicit", "MISSING_INPUT")
    shares = {key: number(value, f"allocation_shares.{key}") for key, value in allocation_shares.items()}
    require(all(value >= 0 for value in shares.values()), "allocation_shares",
            "signed allocation requires a separate qualified method", "UNSUPPORTED_METHOD")
    exact_sum = sum((Fraction(str(value)) for value in shares.values()), Fraction(0))
    tolerance = Fraction(1, 10**12)
    require(abs(exact_sum - 1) <= tolerance, "allocation_shares", "shares must sum to one")
    amount = Fraction(str(total)) * Fraction(str(shares[lob]))
    reconciled = Fraction(str(total)) * exact_sum
    try:
        value = float(amount)
        allocated_total = float(reconciled)
        residual = float(Fraction(str(total)) - reconciled)
    except OverflowError:
        require(False, "result", "allocation outside representable range", "REVIEW_REQUIRED")
    return value, {"lob": lob, "allocation_share": shares[lob], "share_sum": float(exact_sum),
        "sum_tolerance": float(tolerance), "total_risk_margin": total,
        "allocated_total": allocated_total, "reconciliation_residual": residual,
        "renormalised": False, "allocation_reference": allocation_reference,
        "basis_status": "EXTERNAL_UNVERIFIED", "classification_status": "EXTERNAL_UNVERIFIED",
        "scope": "application_of_qualified_lifetime_shares_only",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-37-3-annex-I"]}
