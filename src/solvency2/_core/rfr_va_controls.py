"""2027 VA reuse/firm-factor controls on explicitly qualified external records."""
from datetime import date
from fractions import Fraction

from .core import exact_keys, number, require, scalar
from .rfr_ma_controls import _conditions, _reference


def _count(key, context):
    value = number(scalar(key, context), key, 1)
    require(value.is_integer(), key, "positive integer period count required")
    return int(value)


def reuse_cssr(reuse, context):
    exact_keys(reuse, ("cssr", "calculated_on", "currency", "not_materially_changed", "evidence_reference"), "reuse")
    _reference(reuse["evidence_reference"], "reuse.evidence_reference")
    _conditions({"not_materially_changed": reuse["not_materially_changed"]}, ("not_materially_changed",))
    require(reuse["currency"] == context.currency, "reuse.currency", "same currency required")
    try:
        calculated = date.fromisoformat(reuse["calculated_on"])
    except (TypeError, ValueError):
        require(False, "reuse.calculated_on", "canonical ISO date required")
    require(calculated.isoformat() == reuse["calculated_on"], "reuse.calculated_on", "canonical ISO date required")
    as_of = date.fromisoformat(context.as_of)
    require(calculated <= as_of, "reuse.calculated_on", "future calculation cannot be reused")
    years = _count("rfr_cssr_reuse_years", context)
    try:
        anniversary = calculated.replace(year=calculated.year + years)
    except ValueError:
        require(False, "reuse.calculated_on", "calendar anniversary needs explicit date assessment", "REVIEW_REQUIRED")
    require(as_of < anniversary, "reuse.calculated_on", "CSSR reuse period expired; recalculate", "REVIEW_REQUIRED")
    value = number(reuse["cssr"], "reuse.cssr", 0, 1)
    return value, {"reuse": dict(reuse), "branch": "QUALIFIED_REUSE",
        "reuse_expiry_exclusive": anniversary.isoformat(), "reuse_years": years,
        "supervisory_evidence_verified": False, "revaluation_performed": False,
        "_sources": ["DR:article-51a:4"]}


def firm_adjusted_spread(reference_spread, specification, context):
    if specification is None:
        return reference_spread, {"firm_adjustment_status": "NOT_APPLIED", "firm_adjustment": None}
    exact_keys(specification, ("undertaking_spread", "mode", "approval_reference", "conditions", "history"),
               "firm_adjustment")
    _reference(specification["approval_reference"], "firm_adjustment.approval_reference")
    conditions = _conditions(specification["conditions"], ("data_quality_sufficient", "same_calculation_method",
        "application_currently_permitted", "history_periods_qualified", "macro_adjustment_not_applied"))
    mode = specification["mode"]
    require(isinstance(mode, str) and mode in ("initial", "continuing"), "mode", "initial or continuing required")
    initial = _count("rfr_firm_initial_periods", context)
    cessation = _count("rfr_firm_cessation_periods", context)
    required = initial if mode == "initial" else cessation - 1
    history = specification["history"]
    require(isinstance(history, (list, tuple)) and len(history) == required, "history",
            "explicit consecutive qualified reporting-period history required", "MISSING_INPUT")
    ids, audited, past_increases = set(), [], []
    for row in history:
        comparison_key = "undertaking_spread" if mode == "initial" else "adjusted_spread"
        exact_keys(row, ("period_id", "reference_spread", comparison_key), "history")
        _reference(row["period_id"], "history.period_id")
        require(row["period_id"] not in ids, "history.period_id", "duplicate reporting period")
        ids.add(row["period_id"])
        reference = number(row["reference_spread"], "history.reference_spread")
        compared = number(row[comparison_key], "history." + comparison_key)
        if mode == "initial":
            require(reference > compared, "history", "all prior reference spreads must strictly exceed own spreads",
                    "REVIEW_REQUIRED")
        else:
            past_increases.append(compared > reference)
        audited.append(dict(row))
    own = number(specification["undertaking_spread"], "undertaking_spread")
    require(reference_spread != 0, "reference_spread", "zero reference spread leaves ratio undefined", "REVIEW_REQUIRED")
    cap = number(scalar("rfr_firm_adjustment_cap", context), "firm_adjustment_cap", 0)
    # Cap before float conversion: a huge positive ratio can still give a
    # perfectly representable capped result. No invented lower bound.
    factor = number(float(min(Fraction(cap), Fraction(own) / Fraction(reference_spread))), "firm_adjustment_ratio")
    adjusted = number(factor * reference_spread, "firm_adjusted_spread")
    if mode == "continuing":
        require(not (all(past_increases) and adjusted > reference_spread), "firm_adjustment",
                "consecutive spread increases require immediate cessation", "REVIEW_REQUIRED")
    return adjusted, {"firm_adjustment_status": "DECLARED_QUALIFICATION_CHECKED_EXTERNAL_UNVERIFIED",
        "firm_adjustment": {"mode": mode, "reference_spread": reference_spread, "undertaking_spread": own,
            "factor": factor, "cap": cap, "adjusted_spread": adjusted, "history": audited,
            "initial_periods": initial, "cessation_periods": cessation, "conditions": conditions,
            "approval_reference": specification["approval_reference"], "supervisory_approval_verified": False,
            "period_sequence_verified": False}, "_sources": ["DIR:article-77d:1c"]}
