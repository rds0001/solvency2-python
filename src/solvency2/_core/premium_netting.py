"""Deduct only externally qualified Article116/147 reinsurance premiums."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require
from .loss_given_default import _known_flag, _reference
from .risk_mitigation import _finite_ids


def _finite(value, field):
    try:
        result = float(value)
    except OverflowError:
        require(False, field, "premium aggregate exceeds finite range", "REVIEW_REQUIRED")
    require(result != 0 or value == 0, field, "nonzero premium aggregate underflows", "REVIEW_REQUIRED")
    return result


@calculation("DR:article-116:5", "DR:article-147:5", "DR:article-208:2")
def premium_net_of_reinsurance(gross_premium: float, reinsurance_premiums: Mapping, *,
        qualification_reference: str, finite_reinsurance_ids: list[str] | tuple = (), context: Context):
    """Return signed net premiums, not recoverables, total volume or capital.

    All values refer to the same externally qualified earning/PV/currency basis.
    Unknown qualifications cannot silently become either deductions or exclusions.
    Excluded amounts are retained by row, not interpreted as zero contracts.
    finite_reinsurance_ids declares finite AND economically similar transfers;
    the default empty sequence explicitly qualifies all rows as non-finite.
    """
    _reference(qualification_reference, "qualification_reference")
    gross = number(gross_premium, "gross_premium")
    require(isinstance(reinsurance_premiums, Mapping), "reinsurance_premiums", "labelled premium mapping required")
    finite = _finite_ids(finite_reinsurance_ids, reinsurance_premiums)
    deductions = Fraction(0)
    audit = {}
    for label, row in reinsurance_premiums.items():
        require(isinstance(label, str) and bool(label.strip()), "premium_id", "nonempty ID required")
        exact_keys(row, ("amount", "article41_3_cashflows", "articles209_210_211_213_qualified"), label)
        amount = number(row["amount"], label + ".amount")
        flows = _known_flag(row["article41_3_cashflows"], label + ".article41_3_cashflows")
        qualified = _known_flag(row["articles209_210_211_213_qualified"], label + ".articles209_210_211_213_qualified")
        deductible = flows and qualified and label not in finite
        reasons = []
        if not flows:
            reasons.append("ARTICLE41_3_EXCLUDED_CASHFLOWS")
        if not qualified:
            reasons.append("ARTICLES209_210_211_213_NOT_QUALIFIED")
        if label in finite:
            reasons.append("ARTICLE208_FINITE_OR_SIMILAR_EXCLUDED")
        if deductible:
            deductions += Fraction(str(amount))
        audit[label] = {"amount": amount, "article41_3_cashflows": flows,
            "articles209_210_211_213_qualified": qualified, "deducted": deductible,
            "exclusion_reasons": reasons}
    net = _finite(Fraction(str(gross)) - deductions, "net_premium")
    deducted = _finite(deductions, "deducted_premiums")
    return net, {"gross_premium": gross, "deducted_premiums": deducted,
        "finite_reinsurance_ids": sorted(finite),
        "reinsurance_premiums": dict(sorted(audit.items())), "negative_premiums_floored": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "cashflow_or_contract_qualification_verified": False,
        "premium_projection_or_discounting_performed": False,
        "scope": "eligible_reinsurance_premium_subtraction_only_not_volume_or_SCR"}
