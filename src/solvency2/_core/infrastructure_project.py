"""Declared Article164a project criteria; no insurer modelling or legal approval."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, require


@calculation("DR:article-164a:1:2", unit="indicator")
def infrastructure_project_eligibility_screen(conditions: Mapping, *, investment_kind: str,
        revenue_route: str, many_users: bool, qualification_reference: str,
        security_route: str | None = None, alternative_security_mechanisms: list[str] | None = None,
        in_construction: bool | None = None, construction_risk: bool | None = None,
        material_operational_risk: bool | None = None, context: Context):
    """Apply only the declared, branch-specific project prerequisites.

    Equity and unrated debt carry the additional paragraph1(f) criteria.
    Instrument rating availability is externally qualified, not inferred from
    a corporate rating. Revenue/offtaker/stress/financial assessments remain
    external; a successful screen does not select a reduced capital factor.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external project/scope and substantive evidence required", "MISSING_INPUT")
    require(isinstance(investment_kind, str) and investment_kind in {"equity", "rated_debt", "unrated_debt"},
            "investment_kind", "explicit qualified equity/rated-debt/unrated-debt scope required")
    require(isinstance(revenue_route, str) and revenue_route in {
        "availability", "return_regulated", "take_or_pay", "volume_price"}, "revenue_route",
        "explicit Article164a(2)a revenue route required")
    require(many_users is not None, "many_users", "user concentration qualification unresolved", "REVIEW_REQUIRED")
    require(isinstance(many_users, bool), "many_users", "explicit boolean required")
    debt = investment_kind != "equity"
    enhanced = investment_kind != "rated_debt"
    risk_flags = {"in_construction": in_construction, "construction_risk": construction_risk,
                  "material_operational_risk": material_operational_risk}
    for name, value in risk_flags.items():
        if enhanced:
            require(value is not None, name, "additional-criteria risk scope unknown", "REVIEW_REQUIRED")
            require(isinstance(value, bool), name, "explicit boolean required")
        else:
            require(value is None, name, "paragraph1(f) inputs unused for rated debt; omit")
    if debt:
        require(security_route is not None, "security_route", "explicit debt security route required", "MISSING_INPUT")
        require(isinstance(security_route, str) and security_route in {"all_assets_contracts", "alternative"},
                "security_route", "prescribed debt security route required")
    else:
        require(security_route is None, "security_route", "debt security route unused for equity")
    alternative = security_route == "alternative"
    profile = effective_resource("profile.json", context)
    chosen_mechanisms = []
    if alternative:
        require(alternative_security_mechanisms is not None, "alternative_security_mechanisms",
                "explicit mechanism list required", "MISSING_INPUT")
        require(isinstance(alternative_security_mechanisms, list)
                and all(isinstance(m, str) for m in alternative_security_mechanisms),
                "alternative_security_mechanisms", "list of prescribed mechanism identifiers required")
        allowed = {row[0] for row in profile["tables"]["infrastructure_security_mechanisms"]["rows"]}
        require(len(set(alternative_security_mechanisms)) == len(alternative_security_mechanisms)
                and set(alternative_security_mechanisms) <= allowed, "alternative_security_mechanisms",
                "mechanisms must be unique and from the prescribed catalogue")
        chosen_mechanisms = sorted(alternative_security_mechanisms)
    else:
        require(alternative_security_mechanisms is None, "alternative_security_mechanisms",
                "unused outside the alternative security route; omit")
    predicates = {
        "always": True, "termination": not many_users and revenue_route != "return_regulated",
        "all_security": debt and not alternative, "debt": debt, "alternative_security": alternative,
        "unrated_debt": investment_kind == "unrated_debt", "enhanced": enhanced,
        "construction": enhanced and in_construction is True,
        "construction_risk": enhanced and construction_risk is True,
        "operational_risk": enhanced and material_operational_risk is True,
        "few_users": not many_users}
    rows = profile["tables"]["infrastructure_project_conditions"]["rows"]
    require(all(row[3] in predicates for row in rows), "condition_table",
            "unknown control applicability", "REVIEW_REQUIRED")
    selected = [row for row in rows if predicates[row[3]]]
    keys = [row[0] for row in selected]
    require(len(keys) == len(set(keys)) and bool(keys), "condition_table", "unique controls required", "REVIEW_REQUIRED")
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        require(conditions[key] is not None, key, "active project prerequisite unknown", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")
    mechanism_met = not alternative or bool(chosen_mechanisms)
    met = all(conditions.values()) and mechanism_met
    return int(met), {
        "investment_kind": investment_kind, "revenue_route": revenue_route, "many_users": many_users,
        "security_route": security_route, "alternative_security_mechanisms": chosen_mechanisms,
        "alternative_mechanism_requirement_met": mechanism_met,
        "additional_1f_criteria_applied": enhanced, **risk_flags,
        "active_controls": keys, "conditions": dict(conditions),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "decision": "DECLARED_PREREQUISITES_MET" if met else "DECLARED_PREREQUISITES_NOT_MET",
        "substantive_conditions_verified": False, "instrument_rating_verified": False,
        "supervisory_approval_granted_by_engine": False, "risk_factor_selected": False,
        "scope": "project_164a_declared_screen_not_corporate_164b_or_legal_approval",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-164a"]}
