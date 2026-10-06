"""SLT medical payment assumptions and aggregation of external scenario capital."""
import math

from .core import Context, calculation, number, require, scalar


def _direction(direction):
    require(direction in ("up", "down"), "direction", "up or down required")
    return 1 if direction == "up" else -1


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external reference required", "MISSING_INPUT")


@calculation("DR:article-157:a")
def health_expense_level_stress(expense: float, *, context: Context):
    """Stress eligible own/cedent costs jointly with inflation in external projection."""
    base = number(expense, "expense", 0)
    change = number(scalar("health_expense", context), "health_expense", 0)
    return base * (1 + change), {"base_expense": base, "relative_change": change,
                                "required_joint_stress": "health_expense_inflation_stress",
                                "scope": "health_expense_assumption_only_not_scr"}


@calculation("DR:article-157:b", unit="rate")
def health_expense_inflation_stress(inflation_rate: float, *, context: Context):
    """Add the expense inflation shock without choosing a projection convention."""
    base = number(inflation_rate, "inflation_rate")
    change = number(scalar("health_expense_inflation", context), "health_expense_inflation", 0)
    return base + change, {"base_inflation": base, "absolute_change": change,
                           "required_joint_stress": "health_expense_level_stress",
                           "scope": "health_expense_inflation_assumption_only_not_scr"}


@calculation("DR:article-158")
def health_revision_stress(annuity_benefit: float, *, revision_exposed: bool | None,
                           qualification_reference: str, context: Context):
    """Stress externally selected inflation/legal/health revision-exposed annuities."""
    base = number(annuity_benefit, "annuity_benefit", 0)
    require(revision_exposed is None or isinstance(revision_exposed, bool), "revision_exposed",
            "boolean or None required")
    require(revision_exposed is not None, "revision_exposed", "exposure unresolved", "REVIEW_REQUIRED")
    _reference(qualification_reference, "qualification_reference")
    change = number(scalar("health_revision", context), "health_revision", 0)
    return base * (1 + change) if revision_exposed else base, {
        "base_annuity_benefit": base, "revision_exposed": revision_exposed, "relative_change": change,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "health_revision_assumption_only_not_scr"}


@calculation("DR:article-155:2:a", "DR:article-155:3:a")
def health_medical_payment_stress(payment: float, direction: str, *, context: Context):
    """Stress payments jointly with inflation in the external permanent projection."""
    sign = _direction(direction)
    base = number(payment, "payment", 0)
    change = number(scalar("health_medical_payment_change", context), "health_medical_payment_change", 0, 1)
    return base * (1 + sign * change), {
        "base_payment": base, "relative_change": sign * change,
        "required_joint_stress": "health_medical_inflation_stress", "direction": direction,
        "scope": "slt_medical_payment_assumption_only_not_scr"}


@calculation("DR:article-155:2:b", "DR:article-155:3:b", unit="rate")
def health_medical_inflation_stress(inflation_rate: float, direction: str, *, context: Context):
    """Add/subtract percentage points without inventing a compounding model."""
    sign = _direction(direction)
    base = number(inflation_rate, "inflation_rate")
    change = number(scalar("health_medical_inflation_change", context), "health_medical_inflation_change", 0)
    return base + sign * change, {
        "base_inflation": base, "absolute_change": sign * change,
        "required_joint_stress": "health_medical_payment_stress", "direction": direction,
        "scope": "slt_medical_inflation_assumption_only_not_scr"}


@calculation("DR:article-155:1")
def health_medical_risk(up_charge: float, down_charge: float, *, valuation_reference: str, context: Context):
    """Maximum of two joint-scenario charges; no extra net-selection rule is inferred."""
    up = number(up_charge, "up_charge", 0)
    down = number(down_charge, "down_charge", 0)
    _reference(valuation_reference, "valuation_reference")
    return max(up, down), {"up_charge": up, "down_charge": down,
                           "valuation_reference": valuation_reference, "valuation_status": "EXTERNAL_UNVERIFIED",
                           "scope": "supplied_slt_medical_scenarios_only"}


@calculation("DR:article-154:1-2")
def health_disability_risk(medical_charge: float, income_protection_charge: float, *,
                           classification_reference: str, context: Context):
    """Sum disjoint SLT medical/income charges; no diversification or classification inference."""
    medical = number(medical_charge, "medical_charge", 0)
    income = number(income_protection_charge, "income_protection_charge", 0)
    _reference(classification_reference, "classification_reference")
    return math.fsum((medical, income)), {
        "medical_charge": medical, "income_protection_charge": income,
        "classification_reference": classification_reference, "classification_status": "EXTERNAL_UNVERIFIED",
        "scope": "supplied_slt_disability_components_only"}
