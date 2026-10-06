"""Article207 profit-assumption controls, not a tax/profit projection model."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-207:2a-2d", "DR:article-15", unit="indicator")
def lac_dt_profit_assumptions_check(projection: Mapping, conditions: Mapping, *,
        management_actions_assumed: bool | None, qualification_reference: str, context: Context):
    """Check one externally qualified projection/return-pair and declared evidence.

    Five years bounds new-business revenue assumptions, not all future profits.
    A longer profit forecast activates the haircut condition, without inventing
    its amount. Lower-than-forward returns require review of the literal source
    rather than treating conservative assumptions as automatically unlawful.
    """
    _reference(qualification_reference, "qualification_reference")
    keys = ("business_plan_years", "new_business_years", "forecast_years",
            "assumed_return", "post_stress_forward_return")
    exact_keys(projection, keys, "projection")
    values = {key: number(projection[key], key, 0 if key.endswith("_years") else None) for key in keys}
    management = _known_flag(management_actions_assumed, "management_actions_assumed")
    cap = number(scalar("lac_dt_new_business_max_years", context), "new_business_max_years", 0)
    higher = values["assumed_return"] > values["post_stress_forward_return"]
    require(values["assumed_return"] >= values["post_stress_forward_return"], "assumed_return",
            "below-forward assumption is outside literal equality/higher-evidenced route; assess separately",
            "REVIEW_REQUIRED")
    active = {"always": True, "higher_return": higher,
              "post_plan_forecast": values["forecast_years"] > values["business_plan_years"],
              "management_actions": management}
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["lac_dt_profit_assumption_controls"]["rows"]
    require(len({row[0] for row in rows}) == len(rows), "control_table",
            "unique control keys required", "REVIEW_REQUIRED")
    require(all(row[3] in active for row in rows), "control_table",
            "unknown control applicability rule", "REVIEW_REQUIRED")
    selected = [row for row in rows if active[row[3]]]
    exact_keys(conditions, [row[0] for row in selected], "conditions")
    declared = {row[0]: _known_flag(conditions[row[0]], row[0]) for row in selected}
    checks = {"new_business_within_business_plan": values["new_business_years"] <= values["business_plan_years"],
              "new_business_within_regulatory_horizon": values["new_business_years"] <= cap,
              **declared}
    return int(all(checks.values())), {
        "projection": values, "management_actions_assumed": management,
        "new_business_max_years": cap, "effective_new_business_limit": min(cap, values["business_plan_years"]),
        "return_route": "HIGHER_RETURN_REQUIRING_EVIDENCE" if higher else "POST_STRESS_FORWARD_RETURN",
        "active_controls": list(declared), "checks": checks,
        "failed_checks": [key for key, passed in checks.items() if not passed],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "taxable_profit_projected": False, "dta_recoverability_verified": False,
        "tax_amount_computed": False, "entire_return_curve_verified": False,
        "scope": "declared_profit_assumptions_and_one_corresponding_return_pair_only",
        "_sources": [row[1] for row in selected]}
