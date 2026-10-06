"""Prescribed LTG transition arithmetic; approvals and base valuations external."""
from datetime import date
from fractions import Fraction

from .core import Context, calculation, number, require, scalar
from .loss_given_default import _known_flag, _reference


def _fraction(approval_reference, qualification_reference, context):
    _reference(approval_reference, "approval_reference")
    _reference(qualification_reference, "qualification_reference")
    start = number(scalar("ltg_transition_start_year", context), "start_year")
    end = number(scalar("ltg_transition_end_year", context), "end_year")
    require(start == int(start) and end == int(end) and end > start,
            "transition_years", "increasing whole years required")
    day = date.fromisoformat(context.as_of)
    # A valuation dated31December is end-of-day and includes that year-end
    # reduction. This avoids daily interpolation of the prescribed annual steps.
    effective_year = day.year + int((day.month, day.day) == (12, 31))
    share = Fraction(max(0, min(int(end - start), int(end) - effective_year)), int(end - start))
    return share, {"approval_reference": approval_reference, "qualification_reference": qualification_reference,
                   "qualification_status": "EXTERNAL_UNVERIFIED", "transition_fraction": float(share),
                   "effective_year": effective_year, "valuation_convention": "END_OF_DAY_YEAR_END_STEP",
                   "approval_granted_by_engine": False}


def _excluded(flag, field):
    require(not _known_flag(flag, field), field, "incompatible transition/MA declared", "UNSUPPORTED_METHOD")


def _finite(value, field):
    try:
        return float(value)
    except OverflowError:
        require(False, field, "transition result not representable", "REVIEW_REQUIRED")


@calculation("DIR:article-308c:1-4", unit="rate")
def rfr_transitional_spot_rate(spot_rate: float, legacy_rate: float, equivalent_annual_rate: float, *,
                                matching_adjustment_used: bool | None,
                                technical_provisions_transition_used: bool | None,
                                approval_reference: str, qualification_reference: str, context: Context):
    """Add the approved currency-specific annual transition to one curve point.

    The equivalent annual rate must value the eligible portfolio on the matching
    basis including applicable VA. Existing rfr_equivalent_annual_rate can solve
    nonnegative cashflows; mixed-sign portfolios need qualified external roots.
    Do not include eligible obligations in VA calculation or combine with MA/308d.
    """
    share, details = _fraction(approval_reference, qualification_reference, context)
    _excluded(matching_adjustment_used, "matching_adjustment_used")
    _excluded(technical_provisions_transition_used, "technical_provisions_transition_used")
    spot, legacy, equivalent = (number(v, k) for v, k in (
        (spot_rate, "spot_rate"), (legacy_rate, "legacy_rate"), (equivalent_annual_rate, "equivalent_annual_rate")))
    require(all(rate > -1 for rate in (spot, legacy, equivalent)), "rates", "annual rates must exceed -1")
    adjustment = share * (Fraction(str(legacy)) - Fraction(str(equivalent)))
    value = _finite(Fraction(str(spot)) + adjustment, "adjusted_spot_rate")
    require(value > -1, "adjusted_spot_rate", "transition gives invalid annual discount basis", "REVIEW_REQUIRED")
    return value, {**details, "unadjusted_spot_rate": spot, "legacy_rate": legacy,
                   "equivalent_annual_rate": equivalent, "transition_adjustment": _finite(adjustment, "adjustment"),
                   "scope": "eligible_currency_curve_point_not_new_approval_or_valuation"}


@calculation("DIR:article-308d:1-5")
def technical_provisions_transitional_value(current_gross_provisions: float,
                                             base_solvency2_net_provisions: float, base_legacy_net_provisions: float, *,
                                             supervisory_deduction_limit: float | None,
                                             risk_free_transition_used: bool | None,
                                             approval_reference: str, qualification_reference: str, context: Context):
    """Deduct the phased, optionally capped approved difference from current TP.

    Base amounts are NET on the Article308d(2) date or approved recalibration;
    the current provision is gross, with current recoverables remaining separate.
    None limit explicitly means no supervisory cap was imposed, not unknown.
    A negative deduction is not silently floored or turned into relief.
    """
    share, details = _fraction(approval_reference, qualification_reference, context)
    _excluded(risk_free_transition_used, "risk_free_transition_used")
    current = number(current_gross_provisions, "current_gross_provisions")
    s2 = number(base_solvency2_net_provisions, "base_solvency2_net_provisions")
    legacy = number(base_legacy_net_provisions, "base_legacy_net_provisions")
    difference = Fraction(str(s2)) - Fraction(str(legacy))
    raw = share * difference
    require(raw >= 0, "base_provisions", "negative deduction requires external review, not a zero floor",
            "REVIEW_REQUIRED")
    limit = None if supervisory_deduction_limit is None else number(
        supervisory_deduction_limit, "supervisory_deduction_limit", 0)
    deduction = raw if limit is None else min(raw, Fraction(str(limit)))
    return _finite(Fraction(str(current)) - deduction, "adjusted_provisions"), {
        **details, "current_gross_provisions": current, "base_solvency2_net_provisions": s2,
        "base_legacy_net_provisions": legacy, "base_difference": _finite(difference, "base_difference"),
        "uncapped_deduction": _finite(raw, "uncapped_deduction"),
        "deduction": _finite(deduction, "deduction"), "supervisory_deduction_limit": limit,
        "ordinary_recalculation_interval_months": scalar("ltg_transition_recalculation_months", context),
        "recalibration_authorized_by_engine": False, "recoverables_deducted_again": False,
        "scope": "current_gross_tp_after_approved_transition_not_base_revaluation"}
