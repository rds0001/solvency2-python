"""Article189 routing of qualified risks, not contract or credit classification."""
from .core import Context, calculation, effective_resource, number, require, scalar


@calculation("DR:article-189:2-7", unit="exposure_type")
def default_exposure_type(category: str, *, qualification_reference: str,
        single_name_count: int | None = None, elect_type1: bool | None = None, context: Context):
    """Return1/2 for default types or0 for exclusion FROM THIS MODULE ONLY.

    The category must already describe the precise qualified contractual risk,
    including any spread/mortgage/CCP/guarantee conditions. An excluded risk
    may attract capital elsewhere; zero is a routing code, not a capital value.
    Only cedant deposits and called-unpaid commitments use the declared count
    and optional legal election. Article190 grouping and Article189(5) provider
    substitution, and the all-relevant-exposures scope of the election, remain
    external prerequisites; no count is inferred from arbitrary asset IDs.
    """
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["default_exposure_categories"]["rows"]
    require(isinstance(category, str) and category in {r[0] for r in rows}, "category",
            "explicit supported qualified risk category required", "UNSUPPORTED_PARAMETER")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "material scope and classification qualification required", "MISSING_INPUT")
    selected = [row for row in rows if row[0] == category]
    require(len(selected) == 1, "category_table", "unique category row required", "REVIEW_REQUIRED")
    _, route, source = selected[0]
    require(route in {"TYPE1", "TYPE2", "COUNT_DEPENDENT", "EXCLUDED"}, "category_table",
            "unknown category route", "REVIEW_REQUIRED")
    details = {"category": category, "route": route, "qualification_reference": qualification_reference,
               "qualification_status": "EXTERNAL_UNVERIFIED", "substantive_classification_verified": False,
               "single_name_grouping_verified": False, "mitigation_provider_substitution_performed": False,
               "capital_charge_computed": False, "other_module_capital_assumed_zero": False,
               "scope": "qualified_risk_routing_not_credit_risk_measurement"}
    if route == "COUNT_DEPENDENT":
        count = number(single_name_count, "single_name_count", 1)
        require(count.is_integer(), "single_name_count", "whole count of qualified single names required")
        require(elect_type1 is not None, "elect_type1", "type1 election unknown", "REVIEW_REQUIRED")
        require(isinstance(elect_type1, bool), "elect_type1", "explicit boolean election required")
        limit = number(scalar("default_type1_single_name_limit", context), "single_name_limit", 0)
        require(limit.is_integer(), "single_name_limit", "whole count threshold required", "REVIEW_REQUIRED")
        value = 1 if count <= limit or elect_type1 else 2
        details.update(single_name_count=count, single_name_limit=limit, elect_type1=elect_type1,
                       election_scope_verified=False,
                       decision_basis="COUNT_WITHIN_LIMIT" if count <= limit else
                       "EXPLICIT_TYPE1_ELECTION" if elect_type1 else "COUNT_ABOVE_LIMIT")
    else:
        require(single_name_count is None and elect_type1 is None, "count/election",
                "count and election inputs only apply to count-dependent categories")
        value = {"TYPE1": 1, "TYPE2": 2, "EXCLUDED": 0}[route]
        details["decision_basis"] = route
    return value, {**details, "classification": {0: "EXCLUDED_FROM_DEFAULT_MODULE", 1: "TYPE1", 2: "TYPE2"}[value],
                   "_sources": [source, context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-189"]}
