"""Final recovery/default PV reconciliation; no default model or deposit allocation."""
from fractions import Fraction

from .core import Context, calculation, number, require
from .reinsurance import _reference


@calculation("DIR:article-81", "DR:article-42:1-3")
def reinsurance_adjusted_recoverable(recoverables_before_default: float,
                                     expected_default_adjustment: float, *,
                                     reconciliation_reference: str, context: Context):
    """Subtract the separately calculated EXPECTED default adjustment exactly once.

    Values must already share counterparty/LoB/contract/provision scope, date,
    currency and qualified valuation basis. This does not compute PD, reapply
    an LGD floor, net gross TP, or choose a deposit/SPV-cap ordering.
    A signed negative result is not automatically a recognised asset.
    """
    _reference(reconciliation_reference, "reconciliation_reference")
    before = number(recoverables_before_default, "recoverables_before_default")
    adjustment = number(expected_default_adjustment, "expected_default_adjustment", 0)
    exact = Fraction(str(before)) - Fraction(str(adjustment))
    try:
        result = float(exact)
    except OverflowError:
        require(False, "adjusted_recoverable", "reconciled amount exceeds finite range", "REVIEW_REQUIRED")
    require(result != 0 or exact == 0, "adjusted_recoverable", "nonzero reconciled amount underflows",
            "REVIEW_REQUIRED")
    return result, {"recoverables_before_default": before, "expected_default_adjustment": adjustment,
        "adjustment_sign": "positive_deduction", "reconciliation_reference": reconciliation_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "same_partition_and_basis_verified": False,
        "probability_or_lgd_applied": False, "floor_applied": False,
        "deposit_adjustment_or_spv_cap_performed": False, "gross_technical_provisions_reduced": False,
        "negative_balance_requires_external_classification": result < 0,
        "scope": "qualified_recovery_minus_expected_default_adjustment_not_full_valuation"}
