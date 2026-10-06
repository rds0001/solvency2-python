"""Article156 income-protection stresses; transition-model construction is external."""
from .core import Context, calculation, number, require, scalar


@calculation("DR:article-152:1-3", "DR:article-153:1-3", unit="rate")
def health_biometric_stress(rate: float, shock: str, *, rate_basis: str,
                            selected: bool | None, selection_reference: str, context: Context):
    """Stress only explicitly selected SLT health contracts, not their BOF valuation.

    Selection, permitted grouping and underlying reinsurance contracts remain
    external. Probability and intensity bases are never silently interconverted.
    """
    require(shock in ("mortality", "longevity"), "shock", "mortality or longevity required")
    require(rate_basis in ("probability", "intensity"), "rate_basis", "probability or intensity required")
    base = number(rate, "rate", 0, 1 if rate_basis == "probability" else None)
    require(selected is None or isinstance(selected, bool), "selected", "boolean or None required")
    require(selected is not None, "selected", "contract selection unresolved", "REVIEW_REQUIRED")
    require(isinstance(selection_reference, str) and bool(selection_reference.strip()),
            "selection_reference", "external selection reference required", "MISSING_INPUT")
    reduction = shock == "longevity"
    key = "health_" + shock
    change = number(scalar(key, context), key, 0, 1 if reduction else None)
    stressed = number(base * (1 + (-change if reduction else change)) if selected else base,
                      "stressed_rate", 0)
    require(rate_basis != "probability" or stressed <= 1, "stressed_rate",
            "stress exceeds probability range; no cap specified", "REVIEW_REQUIRED")
    return stressed, {"base_rate": base, "shock": shock, "rate_basis": rate_basis,
                      "relative_change": -change if reduction else change, "selected": selected,
                      "selection_reference": selection_reference, "selection_status": "EXTERNAL_UNVERIFIED",
                      "scope": "health_biometric_assumption_only_not_scr"}


@calculation("DR:article-156:a-b", unit="rate")
def health_income_incidence_stress(rate: float, period: str, *, rate_basis: str, context: Context):
    """Stress incidence for an explicitly assigned period; jointly project all156 changes."""
    keys = {"first_twelve_months": "health_income_first_year", "later_years": "health_income_later_years"}
    require(isinstance(period, str) and period in keys, "period", "explicit supported period required")
    require(rate_basis in ("probability", "intensity"), "rate_basis", "probability or intensity required")
    base = number(rate, "rate", 0, 1 if rate_basis == "probability" else None)
    change = number(scalar(keys[period], context), keys[period], 0)
    stressed = number(base * (1 + change), "stressed_rate", 0)
    require(rate_basis != "probability" or stressed <= 1, "stressed_rate",
            "stress exceeds probability range; no cap specified", "REVIEW_REQUIRED")
    return stressed, {"period": period, "rate_basis": rate_basis, "base_rate": base,
                      "relative_change": change, "parameter_id": "scalars/" + keys[period],
                      "joint_projection_status": "EXTERNAL_INPUT_ONLY", "scope": "income_incidence_assumption_only_not_scr"}


@calculation("DR:article-156:c-d", unit="probability")
def health_income_transition_stress(rate: float, transition: str, *, context: Context):
    """Apply strict recovery / inclusive continuation thresholds without normalisation.

    No complementary transition is inferred or reconstructed. The supplied
    valuation model must define coherent state transitions and joint projection.
    """
    require(transition in ("recovery", "continuation"), "transition", "recovery or continuation required")
    base = number(rate, "rate", 0, 1)
    threshold = number(scalar("health_income_transition_threshold", context), "health_income_transition_threshold", 0, 1)
    recovery = transition == "recovery"
    key = "health_income_recovery" if recovery else "health_income_continuation"
    change = number(scalar(key, context), key, 0, 1 if recovery else None)
    applies = base < threshold if recovery else base <= threshold
    stressed = base * (1 + (-change if recovery else change)) if applies else base
    require(stressed <= 1, "stressed_rate", "stress exceeds probability range; no cap specified", "REVIEW_REQUIRED")
    return stressed, {"transition": transition, "base_rate": base, "threshold": threshold,
                      "comparison": "<" if recovery else "<=", "stress_applied": applies,
                      "relative_change": -change if recovery else change,
                      "transition_model_status": "EXTERNAL_INPUT_ONLY", "scope": "income_transition_assumption_only_not_scr"}
