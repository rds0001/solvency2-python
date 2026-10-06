"""Declared clearing prerequisites; historical and future legal evidence differ."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, require
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-192a", unit="indicator")
def default_clearing_conditions(route: str, conditions: Mapping, *,
        qualification_reference: str, context: Context):
    """Check one externally selected clearing route, not legal eligibility.

    A failed declaration screen never implies zero capital or a fallback LGD
    branch. The client joint-default exception relaxes only the named joint
    failure case. Historical legal opinions must not substitute for the changed
    2027 legal-review requirement. Direct own-account clearing is future-only.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(route, str) and route in (
        "client_full", "client_joint_default_exception", "member_own_account"),
        "route", "explicit supported clearing route required", "UNSUPPORTED_METHOD")
    table = effective_resource("profile.json", context)["tables"]["default_clearing_conditions"]
    rows = [row for row in table["rows"] if row[0] == route]
    require(bool(rows), "route", "route not available in selected profile", "UNSUPPORTED_RULESET")
    keys = [row[1] for row in rows]
    require(len(keys) == len(set(keys)), "default_clearing_conditions",
            "unique condition keys required", "RESOURCE_INTEGRITY")
    exact_keys(conditions, keys, "conditions")
    flags = {key: _known_flag(conditions[key], "conditions." + key) for key in keys}
    passed = all(flags.values())
    variant = "3a" if route == "client_joint_default_exception" else "3"
    sources = [row[3] for row in rows]
    if route == "client_joint_default_exception":
        sources.append("DR:article-192a:2")
    return int(passed), {
        "route": route, "conditions": flags,
        "unmet_conditions": [key for key, value in flags.items() if not value],
        "qualified_branch_candidate": variant if passed else None,
        "clearing_pd_category_candidate": "cleared_article192_" + variant if passed else None,
        "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "legal_review_certified": False, "final_branch_precedence_assessed": False,
        "scope": "declared_clearing_prerequisites_only_not_lgd_pd_or_capital",
        "_sources": sources}
