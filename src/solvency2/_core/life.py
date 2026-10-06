"""Life shock assumptions only: contract selection and BOF revaluation stay separate."""
from .core import Context, calculation, number, require, scalar


@calculation("DR:article-143:1-3", unit="probability")
def life_catastrophe_rate_stress(rate: float, *, selected: bool | None,
                                 selection_reference: str, context: Context):
    """Add the twelve-month mortality shock only to externally selected contracts.

    The input is a mortality probability for the next twelve months, not an
    intensity. No lifetime extrapolation, contract selection or BOF valuation
    is inferred; article 143 specifies no probability cap.
    """
    base = number(rate, "rate", 0, 1)
    require(selected is None or isinstance(selected, bool), "selected", "boolean or None required")
    require(selected is not None, "selected", "contract selection unresolved", "REVIEW_REQUIRED")
    require(isinstance(selection_reference, str) and bool(selection_reference.strip()),
            "selection_reference", "external contract selection reference required", "MISSING_INPUT")
    change = number(scalar("life_cat", context), "life_cat", 0)
    stressed = base + change if selected else base
    require(stressed <= 1, "stressed_rate", "stress exceeds probability range; no cap specified",
            "REVIEW_REQUIRED")
    return stressed, {"base_rate": base, "absolute_change": change, "selected": selected,
                      "selection_reference": selection_reference, "selection_status": "EXTERNAL_UNVERIFIED",
                      "period": "NEXT_TWELVE_MONTHS_ONLY", "scope": "mortality_assumption_only_not_scr"}


@calculation("DR:article-137:1", "DR:article-138:1", "DR:article-139", unit="rate")
def life_biometric_stress(rate: float, shock: str, *, rate_basis: str, context: Context):
    """Apply a selected biometric stress without inventing a probability/intensity conversion.

    Disability incidence/recovery stresses must be projected jointly. Contract
    selection and time-period assignment are external, not inferred from rate.
    """
    parameters = {"mortality": ("mortality", 1), "longevity": ("longevity", -1),
                  "disability_first_year": ("disability_first_year", 1),
                  "disability_later_years": ("disability_later_years", 1),
                  "disability_recovery": ("disability_recovery", -1)}
    require(isinstance(shock, str) and shock in parameters, "shock", "supported life shock required",
            "UNSUPPORTED_METHOD")
    require(rate_basis in ("probability", "intensity"), "rate_basis", "explicit rate basis required")
    base = number(rate, "rate", 0, 1 if rate_basis == "probability" else None)
    key, direction = parameters[shock]
    change = number(scalar(key, context), key, 0, 1 if direction < 0 else None)
    stressed = number(base * (1 + direction * change), "stressed_rate", 0)
    require(rate_basis != "probability" or stressed <= 1, "stressed_rate",
            "stress exceeds probability range; no probability cap specified here", "REVIEW_REQUIRED")
    return stressed, {"base_rate": base, "shock": shock, "rate_basis": rate_basis,
                       "relative_change": direction * change, "parameter_id": f"scalars/{key}",
                       "selection_and_period_status": "EXTERNAL_INPUT_ONLY",
                       "scope": "life_rate_assumption_only_not_scr"}


@calculation("DR:article-140:a")
def life_expense_level_stress(expense: float, *, context: Context):
    """Stress eligible costs; combine with inflation stress in the external projection."""
    base = number(expense, "expense", 0)
    change = number(scalar("life_expense", context), "life_expense", 0)
    return base * (1 + change), {"base_expense": base, "relative_change": change,
                                "required_joint_stress": "life_expense_inflation_stress",
                                "scope": "expense_level_only_not_projection_or_scr"}


@calculation("DR:article-140:b", unit="rate")
def life_expense_inflation_stress(inflation_rate: float, *, context: Context):
    """Add the prescribed percentage-point shock without choosing a compounding model."""
    base = number(inflation_rate, "inflation_rate")
    change = number(scalar("expense_inflation", context), "expense_inflation", 0)
    return base + change, {"base_inflation_rate": base, "absolute_change": change,
                           "required_joint_stress": "life_expense_level_stress",
                           "scope": "expense_inflation_only_not_projection_or_scr"}


@calculation("DR:article-141")
def life_revision_stress(annuity_benefit: float, *, revision_exposed: bool | None, context: Context):
    """Increase only externally qualified revision-exposed annuity benefits."""
    base = number(annuity_benefit, "annuity_benefit", 0)
    require(revision_exposed is None or isinstance(revision_exposed, bool), "revision_exposed",
            "boolean or None required")
    require(revision_exposed is not None, "revision_exposed", "revision exposure unresolved", "REVIEW_REQUIRED")
    change = number(scalar("life_revision", context), "life_revision", 0)
    return base * (1 + change) if revision_exposed else base, {
        "base_annuity_benefit": base, "revision_exposed": revision_exposed, "relative_change": change,
        "selection_status": "EXTERNAL_UNVERIFIED", "scope": "annuity_benefit_stress_only_not_scr"}
