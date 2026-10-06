"""DR191 declared mortgage conditions and explicit EUR/history thresholds."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .evidence import _declared_bool


@calculation("DR:article-191:1-13", unit="indicator")
def mortgage_type2_eligibility_screen(conditions: Mapping[str, bool], total_debt_eur: float,
                                      years_since_value_monitoring: float, *, repayment_route: str,
                                      qualification_reference: str, context: Context):
    """Screen declarations and numerical limits, not the truth of legal conditions.

Debt is explicitly EUR and includes overdue/connected-party/group creditor
amounts. Context.currency causes no implicit FX conversion. A <=3-year age
does not waive more frequent monitoring under material market changes.
The future CRR alternative is an external qualification, not a CRR calculator.
"""
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "nonempty external qualification reference required", "MISSING_INPUT")
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["mortgage_type2_conditions"]["rows"]
    routes = {row[3] for row in rows} - {"always"}
    require(isinstance(repayment_route, str) and repayment_route in routes, "repayment_route",
            "explicit repayment route supported by selected profile required", "UNSUPPORTED_METHOD")
    selected = [row for row in rows if row[3] in {"always", repayment_route}]
    exact_keys(conditions, [row[0] for row in selected], "conditions")
    # Validate all declarations, even when another condition or a numeric
    # limit would already fail. Unknown is never a silent False.
    declarations = {row[0]: _declared_bool(conditions[row[0]], "conditions." + row[0]) for row in selected}
    debt = number(total_debt_eur, "total_debt_eur", 0)
    age = number(years_since_value_monitoring, "years_since_value_monitoring", 0)
    debt_limit = number(profile["scalars"]["mortgage_type2_total_debt_limit_eur"]["value"], "debt_limit_eur", 0)
    max_age = number(profile["scalars"]["mortgage_value_monitoring_max_years"]["value"], "max_age_years", 0)
    debt_pass, age_pass = debt <= debt_limit, age <= max_age
    failed = [key for key, value in declarations.items() if not value]
    return int(not failed and debt_pass and age_pass), {
        "conditions": declarations, "failed_conditions": failed, "repayment_route": repayment_route,
        "required_condition_count": len(selected), "inactive_conditions": [r[0] for r in rows if r not in selected],
        "total_debt_eur": debt, "debt_limit_eur": debt_limit, "debt_limit_passed": debt_pass,
        "years_since_value_monitoring": age, "maximum_monitoring_age_years": max_age,
        "monitoring_age_passed": age_pass, "thresholds_inclusive": True, "debt_currency": "EUR",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "fx_conversion_performed": False, "conditions_verified": False, "crr_requirements_computed": False,
        "credit_risk_classification_applied": False, "lgd_qualification_granted": False,
        "conditional_control_note": "True declares compliance where the regulatory trigger applies.",
        "scope": "declared_DR191_conditions_and_numeric_limits_not_legal_or_valuation_certification",
        "_sources": [r[1] for r in selected] + [
            context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-191"]}
