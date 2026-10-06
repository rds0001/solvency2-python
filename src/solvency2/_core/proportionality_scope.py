"""2027 numerical proportionality screens, never supervisory classification."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar
from .loss_given_default import _known_flag, _reference


def _qualified(undertaking_type, reference, context):
    _reference(reference, "qualification_reference")
    require(context.currency == "EUR", "currency", "EUR-qualified amounts required", "UNSUPPORTED_CURRENCY")
    require(isinstance(undertaking_type, str) and undertaking_type in {"life", "nonlife", "composite"},
            "undertaking_type", "qualified life/nonlife/composite business required", "UNSUPPORTED_METHOD")


def _f(value):
    return Fraction(str(value))


def _scope(undertaking_type, life_tp, total_tp, nonlife_gwp, total_gwp, life_fraction, nonlife_fraction):
    if undertaking_type != "composite":
        return undertaking_type == "life", undertaking_type == "nonlife"
    require(total_tp > 0 and total_gwp > 0, "mixed_basis", "positive mixed-business ratio bases required", "REVIEW_REQUIRED")
    return (_f(life_tp) >= _f(life_fraction) * _f(total_tp),
            _f(nonlife_gwp) >= _f(nonlife_fraction) * _f(total_gwp))


@calculation("DIR:article-213a:1-4", unit="indicator")
def small_non_complex_group_annual_conditions_2027(method: str, metrics: Mapping, conditions: Mapping, *,
                                                   qualification_reference: str, context: Context):
    """Group213a annual criteria: NOT the solo29a business-share branching.

    Group status/history and each method2 entity's SNC classification remain
    externally qualified. Group premium cap is TOTAL GWP; group surplus must
    be strictly positive. Two distinct foreign-premium criteria must both pass.
    Interest TP basis explicitly excludes method2 entities. Method2-only waives
    consolidated interest/investment tests, never the other group conditions.
    """
    _reference(qualification_reference, "qualification_reference")
    require(context.currency == "EUR", "currency", "EUR-qualified group amounts required", "UNSUPPORTED_CURRENCY")
    require(isinstance(method, str) and method in {"method1", "method2", "combined"}, "method", "qualified group method required")
    keys = ("life_gross_tp", "consolidated_gross_tp_excluding_method2", "total_gwp", "nonlife_gwp",
            "foreign_member_gwp", "foreign_business_gwp", "interest_scr", "market_scr", "investment_default_scr",
            "intangible_scr", "total_investments", "restricted_nonlife_gwp", "assumed_reinsurance_gwp",
            "combined_ratio_three_year_average", "group_surplus")
    exact_keys(metrics, keys, "metrics")
    vals = {k: number(metrics[k], k) for k in keys}
    for k in keys:
        if k not in {"combined_ratio_three_year_average", "group_surplus"}:
            require(vals[k] >= 0, k, "nonnegative qualified group screen basis required", "REVIEW_REQUIRED")
    require(vals["nonlife_gwp"] <= vals["total_gwp"], "nonlife_gwp", "part exceeds total")
    fact_keys = ("has_non_nonlife_member", "has_non_life_member", "all_method2_entities_snc",
                 "is_conglomerate", "has_article228_subsidiary", "approved_group_internal_model")
    exact_keys(conditions, fact_keys, "conditions")
    facts = {k: _known_flag(conditions[k], k) for k in fact_keys}
    require(facts["has_non_nonlife_member"] or facts["has_non_life_member"], "conditions", "qualified insurance group membership required")
    limits = {k: number(scalar("group_snc_" + k, context), k, 0) for k in (
        "interest_fraction", "life_tp_limit", "premium_limit", "combined_ratio_limit", "restricted_premium_fraction",
        "foreign_premium_limit", "foreign_fraction", "investment_risk_fraction", "assumed_reinsurance_fraction")}
    tests = {"positive_group_surplus": vals["group_surplus"] > 0,
             "method2_members": method == "method1" or facts["all_method2_entities_snc"],
             "assumed_reinsurance": _f(vals["assumed_reinsurance_gwp"]) <= _f(limits["assumed_reinsurance_fraction"]) * _f(vals["total_gwp"])}
    for k in ("foreign_member_gwp", "foreign_business_gwp"):
        tests[k] = vals[k] < limits["foreign_premium_limit"] or _f(vals[k]) < _f(limits["foreign_fraction"]) * _f(vals["total_gwp"])
    if facts["has_non_nonlife_member"]:
        tests["life_size"] = vals["life_gross_tp"] <= limits["life_tp_limit"]
        if method != "method2":
            tests["interest"] = _f(vals["interest_scr"]) <= _f(limits["interest_fraction"]) * _f(vals["consolidated_gross_tp_excluding_method2"])
    if facts["has_non_life_member"]:
        tests["combined_ratio"] = vals["combined_ratio_three_year_average"] < limits["combined_ratio_limit"]
        tests["total_group_premiums"] = vals["total_gwp"] <= limits["premium_limit"]
        tests["restricted_lines"] = _f(vals["restricted_nonlife_gwp"]) <= _f(limits["restricted_premium_fraction"]) * _f(vals["nonlife_gwp"])
    if method != "method2":
        tests["investments"] = sum(_f(vals[k]) for k in ("market_scr", "investment_default_scr", "intangible_scr")) <= _f(limits["investment_risk_fraction"]) * _f(vals["total_investments"])
    excluded = any(facts[k] for k in ("is_conglomerate", "has_article228_subsidiary", "approved_group_internal_model"))
    return int(all(tests.values()) and not excluded), {"method": method, "metrics": vals, "conditions": facts,
        "annual_criteria": tests, "absolute_exclusion": excluded, "limits": limits,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "classification_granted": False, "scope": "one_group_year_not_supervisory_classification_or_history"}


@calculation("DIR:article-29a:1-3", "DR:article-327a", unit="indicator")
def small_non_complex_annual_conditions_2027(undertaking_type: str, metrics: Mapping, conditions: Mapping, *,
                                             qualification_reference: str, context: Context):
    """One qualified year of Article29a criteria, not two-year status or approval.

    The three-year average NET combined ratio is externally qualified: the
    source does not prescribe a universal weighting method for its construction.
    investment_default_scr is only the listed investment exposures, not the
    whole default module. Intangible charge follows the existing Article203 API.
    Captive alternative never overrides the Article29a(3) absolute exclusions.
    """
    _qualified(undertaking_type, qualification_reference, context)
    keys = ("life_gross_tp", "total_gross_tp", "nonlife_gwp", "total_gwp", "other_member_states_gwp",
            "assumed_reinsurance_gwp", "interest_scr", "market_scr", "investment_default_scr",
            "intangible_scr", "total_investments", "restricted_nonlife_gwp", "net_combined_ratio_three_year_average",
            "eligible_own_funds", "scr", "natural_person_tp", "group_pension_fund_assets")
    exact_keys(metrics, keys, "metrics")
    fact_keys = ("is_captive", "captive_insureds_qualify", "compulsory_liability", "approved_internal_model",
                 "parent_conglomerate_or_group", "group_is_small_non_complex", "parent_article228_entity")
    exact_keys(conditions, fact_keys, "conditions")
    facts = {k: _known_flag(conditions[k], k) for k in fact_keys}
    values = {k: number(metrics[k], "metrics." + k) for k in keys}
    for key in ("total_gross_tp", "total_gwp", "nonlife_gwp", "life_gross_tp", "other_member_states_gwp",
                "assumed_reinsurance_gwp", "interest_scr", "market_scr", "investment_default_scr",
                "intangible_scr", "total_investments", "restricted_nonlife_gwp", "scr", "natural_person_tp",
                "group_pension_fund_assets"):
        require(values[key] >= 0, key, "nonnegative qualified screen basis required", "REVIEW_REQUIRED")
    require(values["life_gross_tp"] <= values["total_gross_tp"] and values["nonlife_gwp"] <= values["total_gwp"],
            "metrics", "component exceeds declared total")
    limits = {k: number(scalar("snc_" + k, context), k, 0) for k in (
        "life_fraction", "nonlife_fraction", "interest_fraction", "foreign_premium_limit", "foreign_fraction",
        "life_tp_limit", "nonlife_premium_limit", "restricted_premium_fraction", "investment_risk_fraction",
        "assumed_reinsurance_fraction", "combined_ratio_limit", "captive_natural_fraction", "pension_asset_limit")}
    if undertaking_type == "composite" and facts["is_captive"] and (
            values["total_gross_tp"] == 0 or values["total_gwp"] == 0):
        life, nonlife = False, False
    else:
        life, nonlife = _scope(undertaking_type, values["life_gross_tp"], values["total_gross_tp"],
                               values["nonlife_gwp"], values["total_gwp"], limits["life_fraction"], limits["nonlife_fraction"])
    require(life or nonlife or facts["is_captive"], "mixed_scope", "Article29a mixed business below both scope thresholds needs review",
            "REVIEW_REQUIRED")
    tests = {
        "investment_risk": sum(_f(values[k]) for k in ("market_scr", "investment_default_scr", "intangible_scr"))
                           <= _f(limits["investment_risk_fraction"]) * _f(values["total_investments"]),
        "scr_met": values["eligible_own_funds"] >= values["scr"],
    }
    if life:
        tests["interest_risk"] = _f(values["interest_scr"]) <= _f(limits["interest_fraction"]) * _f(values["total_gross_tp"])
        tests["life_size"] = values["life_gross_tp"] <= limits["life_tp_limit"]
    if nonlife:
        tests["combined_ratio"] = values["net_combined_ratio_three_year_average"] < limits["combined_ratio_limit"]
        tests["nonlife_size"] = values["nonlife_gwp"] <= limits["nonlife_premium_limit"]
        tests["restricted_lines"] = _f(values["restricted_nonlife_gwp"]) <= _f(limits["restricted_premium_fraction"]) * _f(values["nonlife_gwp"])
    if not facts["is_captive"]:
        tests["foreign_premiums"] = (values["other_member_states_gwp"] < limits["foreign_premium_limit"] or
            _f(values["other_member_states_gwp"]) < _f(limits["foreign_fraction"]) * _f(values["total_gwp"]))
        tests["assumed_reinsurance"] = _f(values["assumed_reinsurance_gwp"]) <= _f(limits["assumed_reinsurance_fraction"]) * _f(values["total_gwp"])
    natural_ok = (values["natural_person_tp"] == 0 or
                  _f(values["natural_person_tp"]) < _f(limits["captive_natural_fraction"]) * _f(values["total_gross_tp"]))
    captive_alternative = (facts["is_captive"] and facts["captive_insureds_qualify"] and natural_ok
                           and not facts["compulsory_liability"])
    exclusions = {
        "approved_internal_model": facts["approved_internal_model"],
        "parent_unqualified_group": facts["parent_conglomerate_or_group"] and not facts["group_is_small_non_complex"],
        "parent_article228_entity": facts["parent_article228_entity"],
        "pension_assets": values["group_pension_fund_assets"] > limits["pension_asset_limit"],
    }
    satisfied = ((bool(life or nonlife) and all(tests.values())) or captive_alternative) and not any(exclusions.values())
    return int(satisfied), {"annual_criteria": tests, "absolute_exclusions": exclusions, "metrics": values,
        "conditions": facts, "limits": limits, "life_branch": life, "nonlife_branch": nonlife,
        "captive_alternative": captive_alternative, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "classification_granted": False,
        "scope": "one_year_numerical_and_declared_conditions_not_article29b_classification"}


@calculation("DR:articles-327b-327e", "DR:article-327g", unit="indicator")
def non_snc_proportionality_size_screen_2027(measure: str, undertaking_type: str,
                                            life_gross_tp: float, total_gross_tp: float,
                                            nonlife_gwp: float, total_gwp: float, market_shares: Mapping, *,
                                            size_exception_confirmed: bool | None,
                                            exception_reference: str | None = None,
                                            qualification_reference: str, context: Context):
    """Shared327b/c/d/e/g size component; each measure's other conditions remain.

    A declared low-risk supervisory exception applies ONLY to size condition c,
    never to all governance/ORSA/liquidity or actual approval requirements.
    The existing327f prudent-deterministic screen is separate and unchanged.
    """
    _qualified(undertaking_type, qualification_reference, context)
    articles = {"rsr": "327b", "key_functions": "327c", "policies": "327d", "orsa": "327e", "liquidity": "327g"}
    require(isinstance(measure, str) and measure in articles, "measure", "explicit supported measure required",
            "UNSUPPORTED_METHOD")
    life_tp = number(life_gross_tp, "life_gross_tp", 0)
    total_tp = number(total_gross_tp, "total_gross_tp", 0)
    nl_gwp = number(nonlife_gwp, "nonlife_gwp", 0)
    total = number(total_gwp, "total_gwp", 0)
    require(life_tp <= total_tp and nl_gwp <= total, "basis", "component exceeds declared total")
    limits = {k: number(scalar("non_snc_" + k, context), k, 0) for k in (
        "life_tp_limit", "nonlife_premium_limit", "market_share_limit", "life_fraction", "nonlife_fraction")}
    life, nonlife = _scope(undertaking_type, life_tp, total_tp, nl_gwp, total,
                           limits["life_fraction"], limits["nonlife_fraction"])
    required = ("life", "nonlife") if undertaking_type == "composite" else (undertaking_type,)
    exact_keys(market_shares, required, "market_shares")
    shares = {k: number(v, "market_shares." + k, 0, 1) for k, v in market_shares.items()}
    tests = {"life_size": not life or life_tp <= limits["life_tp_limit"],
             "nonlife_size": not nonlife or nl_gwp <= limits["nonlife_premium_limit"],
             "market_shares": all(v <= limits["market_share_limit"] for v in shares.values())}
    exception = _known_flag(size_exception_confirmed, "size_exception_confirmed")
    if exception:
        _reference(exception_reference, "exception_reference")
    else:
        require(exception_reference is None, "exception_reference", "unused exception reference")
    return int(all(tests.values()) or exception), {"measure": measure, "article": articles[measure],
        "size_conditions": tests, "life_size_limit_applies": life, "nonlife_size_limit_applies": nonlife,
        "market_shares": shares, "limits": limits, "size_exception_confirmed": exception,
        "exception_reference": exception_reference, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "approval_granted": False,
        "scope": "condition_c_only_not_complete_measure_eligibility", "_sources": ["DR:article-" + articles[measure] + ":1:c-4"]}
