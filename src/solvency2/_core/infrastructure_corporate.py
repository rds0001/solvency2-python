"""Declared Article164b corporate-infrastructure prerequisites, not approval."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DR:article-164b", "DR:article-164a:2", unit="indicator")
def infrastructure_corporate_eligibility_screen(conditions: Mapping, *, instrument: str,
        revenue_route: str, many_users: bool, rating_available: bool,
        qualification_reference: str, credit_quality_step: str | None = None,
        operating_years: float | None = None, history_basis: str | None = None, context: Context):
    """Screen declared corporate criteria with conditional controls and numbers.

    The caller qualifies the infrastructure majority, EEA/OECD location,
    revenue pattern and (where needed) offtaker. No percentage for a 'clear
    majority' or numeric interpretation of Article164a(2)biii is invented.
    Corporate CQS0..3 in Article164b(7) is distinct and explicit.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external scope and substantive qualification required", "MISSING_INPUT")
    require(isinstance(instrument, str) and instrument in {"equity", "debt"}, "instrument",
            "equity or debt required")
    require(isinstance(revenue_route, str) and revenue_route in {
        "availability", "return_regulated", "take_or_pay", "volume_price"}, "revenue_route",
        "explicit Article164a(2)a route required")
    for name, flag in (("many_users", many_users), ("rating_available", rating_available)):
        require(flag is not None, name, "classification unknown", "REVIEW_REQUIRED")
        require(isinstance(flag, bool), name, "explicit boolean required")
    profile = effective_resource("profile.json", context)
    predicates = {"always": True, "few_users": not many_users, "volume_price": revenue_route == "volume_price",
                  "debt": instrument == "debt", "unrated": not rating_available}
    rows = profile["tables"]["infrastructure_corporate_conditions"]["rows"]
    require(all(row[3] in predicates for row in rows), "condition_table",
            "unknown control applicability", "REVIEW_REQUIRED")
    selected = [row for row in rows if predicates[row[3]]]
    keys = [row[0] for row in selected]
    require(len(keys) == len(set(keys)) and bool(keys), "condition_table", "unique controls required", "REVIEW_REQUIRED")
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        require(conditions[key] is not None, key, "active prerequisite unknown", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")
    if rating_available:
        require(operating_years is None and history_basis is None, "history",
                "unrated history inputs must be omitted for a rated corporate")
        require(credit_quality_step is not None, "credit_quality_step", "designated-ECAI rating required", "MISSING_INPUT")
        require(isinstance(credit_quality_step, str) and credit_quality_step in {str(i) for i in range(7)},
                "credit_quality_step", "explicit string CQS0 through6 required")
        maximum = number(scalar("infrastructure_corporate_maximum_cqs", context), "maximum_cqs", 0, 6)
        require(maximum == int(maximum), "maximum_cqs", "whole credit-quality step required", "REVIEW_REQUIRED")
        numeric_met = int(credit_quality_step) <= maximum
        numeric = {"credit_quality_step": credit_quality_step, "maximum_credit_quality_step": maximum}
    else:
        require(credit_quality_step is None, "credit_quality_step", "rating must be omitted for an unrated corporate")
        years = number(operating_years, "operating_years", 0)
        require(isinstance(history_basis, str) and history_basis in {
            "company_business", "acquired_company_operations"}, "history_basis",
            "company business or acquired-company operation history required")
        minimum = number(scalar("infrastructure_corporate_minimum_years", context), "minimum_years", 0)
        numeric_met = years >= minimum
        numeric = {"operating_years": years, "history_basis": history_basis, "minimum_years": minimum}
    met = all(conditions.values()) and numeric_met
    return int(met), {
        "instrument": instrument, "revenue_route": revenue_route, "many_users": many_users,
        "rating_available": rating_available, "conditions": dict(conditions), "active_controls": keys,
        "numeric_criterion_met": numeric_met, **numeric,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "decision": "DECLARED_PREREQUISITES_MET" if met else "DECLARED_PREREQUISITES_NOT_MET",
        "substantive_conditions_verified": False, "supervisory_approval_granted_by_engine": False,
        "risk_factor_selected": False,
        "scope": "corporate_164b_declared_screen_not_project_164a_or_legal_approval",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":" + ref
                     for ref in ("article-164b", "article-164a-2")]}
