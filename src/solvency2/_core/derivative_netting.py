"""Signed market-value sum for one qualified Article192 derivative netting set."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-192:1", "DR:article-192:3d:a")
def default_derivative_netting_value(positions: Mapping, *, netting_qualified: bool | None,
        liabilities_settled_before_clearing: bool | None, qualification_reference: str,
        context: Context):
    """Combine market values, never stand-alone RM, collateral stress or LGD.

    All values must already be in context currency and Article75-compatible.
    Netting eligibility and completeness of the set remain externally assessed.
    Fraction over decimal float representations prevents intermediate overflow
    and preserves signed cancellation. Only the final value becomes float.
    """
    _reference(qualification_reference, "qualification_reference")
    qualified = _known_flag(netting_qualified, "netting_qualified")
    early = _known_flag(liabilities_settled_before_clearing, "liabilities_settled_before_clearing")
    require(qualified and not early, "netting_qualification",
            "qualified209/210 netting without settlement-before-clearing exclusion required",
            "REVIEW_REQUIRED")
    require(isinstance(positions, Mapping), "positions", "labelled position mapping required")
    require(bool(positions), "positions", "explicit nonempty set required", "MISSING_INPUT")
    values, identity = {}, None
    for label, row in positions.items():
        require(isinstance(label, str) and bool(label.strip()), "position_id", "nonempty string ID required")
        exact_keys(row, ("counterparty_id", "netting_agreement_id", "market_value"), label)
        for field in ("counterparty_id", "netting_agreement_id"):
            require(isinstance(row[field], str) and bool(row[field].strip()), label + "." + field,
                    "nonempty string ID required")
        key = (row["counterparty_id"], row["netting_agreement_id"])
        if identity is None:
            identity = key
        require(identity == key, "netting_set",
                "same counterparty AND same agreement required, not merely same corporate group",
                "REVIEW_REQUIRED")
        values[label] = number(row["market_value"], label + ".market_value")
    total = sum((Fraction(str(v)) for v in values.values()), Fraction(0))
    try:
        result = float(total)
    except OverflowError:
        require(False, "netting_value", "combined value exceeds finite float range", "REVIEW_REQUIRED")
    require(result != 0 or total == 0, "netting_value",
            "nonzero combined value underflows float range", "REVIEW_REQUIRED")
    return result, {
        "position_values": dict(sorted(values.items())), "position_count": len(values),
        "counterparty_id": identity[0], "netting_agreement_id": identity[1],
        "netting_qualified": qualified, "liabilities_settled_before_clearing": early,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "netting_set_completeness_verified": False, "negative_values_floored": False,
        "summation_basis": "exact_decimal_representations_of_finite_input_floats",
        "risk_mitigation_basis_required": "ENTIRE_NETTING_SET",
        "collateral_basis_required": "ENTIRE_NETTING_SET_VARIANT_SPECIFIC",
        "scope": "signed_derivative_market_value_sum_only_not_lgd_or_capital"}
