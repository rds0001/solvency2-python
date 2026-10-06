"""Future105a/171b qualification with externally valued assets and liabilities.

No insurer-specific ALM model is supplied. Source-prescribed threshold and
haircut arithmetic is computed here, not replaced by an eligibility assertion.
"""
import math
from collections.abc import Mapping

from .core import effective_resource, exact_keys, number, require, scalar
from .loss_given_default import _known_flag, _reference


def _parameter(name, context):
    return number(scalar("long_term_equity_" + name, context), name, 0)


def _life(inputs, context):
    exact_keys(inputs, ("groups", "long_term_equity_value", "long_term_equity_share",
                        "total_life_best_estimate", "valuation_reference"), "avoidance_inputs")
    _reference(inputs["valuation_reference"], "valuation_reference")
    groups = inputs["groups"]
    require(isinstance(groups, Mapping) and bool(groups), "groups", "nonempty disjoint HRGs required")
    risk_keys = ("mortality", "lapse_up", "health_mortality", "health_lapse_up")
    duration_limit = _parameter("illiquid_duration", context)
    risk_limit = _parameter("illiquid_risk_ratio", context)
    audit = {}
    for identifier, group in groups.items():
        _reference(identifier, "group_id")
        exact_keys(group, ("macaulay_duration", "best_estimate", "article75_value", "risks"), "group")
        exact_keys(group["risks"], risk_keys, "group.risks")
        duration = number(group["macaulay_duration"], "macaulay_duration", 0)
        best_estimate = number(group["best_estimate"], "best_estimate")
        value = number(group["article75_value"], "article75_value")
        risks = {key: number(group["risks"][key], key, 0) for key in risk_keys}
        qualified = duration > duration_limit and all(v < risk_limit * best_estimate for v in risks.values())
        audit[identifier] = {"qualified": qualified, "article75_value": value,
                             "risk_threshold": risk_limit * best_estimate}
    illiquid = math.fsum(row["article75_value"] for row in audit.values() if row["qualified"])
    assets = number(inputs["long_term_equity_value"], "long_term_equity_value", 0)
    share = number(inputs["long_term_equity_share"], "long_term_equity_share", 0, 1)
    total_be = number(inputs["total_life_best_estimate"], "total_life_best_estimate")
    require(total_be != 0, "total_life_best_estimate", "zero ratio denominator requires review", "REVIEW_REQUIRED")
    limit = max(0, number(illiquid / total_be, "illiquid_share_limit"))
    return illiquid > assets and share <= limit, {"groups": audit, "illiquid_value": illiquid,
        "share_limit": limit, "long_term_equity_value": assets, "long_term_equity_share": share}


def _nonlife(inputs, context):
    exact_keys(inputs, ("direct_assets", "fund_assets", "gross_best_estimate", "qualified_recoveries",
                        "other_recoveries", "valuation_reference", "asset_qualification_reference"),
               "avoidance_inputs")
    for key in ("valuation_reference", "asset_qualification_reference"):
        _reference(inputs[key], key)
    table = effective_resource("profile.json", context)["tables"]["long_term_equity_liquidity_haircuts"]
    classes = [row[0] for row in table["rows"]]
    assets, weighted = {}, []
    for index, route in enumerate(("direct", "fund"), 1):
        exact_keys(inputs[route + "_assets"], classes, route + "_assets")
        assets[route] = {key: number(inputs[route + "_assets"][key], key, 0) for key in classes}
        for row in table["rows"]:
            haircut = number(row[index], "haircut", 0, 1)
            weighted.append(assets[route][row[0]] * (1 - haircut))
    total = math.fsum(v for values in assets.values() for v in values.values())
    level2 = math.fsum(v for values in assets.values() for key, v in values.items() if key.startswith("level2"))
    level2b = math.fsum(v for values in assets.values() for key, v in values.items() if key.startswith("level2b"))
    fund = math.fsum(assets["fund"].values())
    # The source limits solvency values before haircuts. No invented optimum
    # or silent pro-rata trimming: callers select the eligible portfolio.
    caps_ok = level2 <= _parameter("level2_cap", context) * total and level2b <= _parameter("level2b_cap", context) * total
    if fund:
        require(context.currency == "EUR", "currency", "fund cap requires externally converted EUR inputs",
                "UNSUPPORTED_CURRENCY")
        caps_ok = caps_ok and fund <= _parameter("fund_cap_eur", context)
    gross = number(inputs["gross_best_estimate"], "gross_best_estimate")
    qualified = number(inputs["qualified_recoveries"], "qualified_recoveries")
    other = number(inputs["other_recoveries"], "other_recoveries")
    # Signed discounted reinsurance cashflows: premiums are not mistaken for
    # positive recoveries. Each bucket has one uniform source haircut.
    adjusted = qualified * (1 - _parameter("qualified_reinsurance_haircut", context)) + other * (
        1 - _parameter("other_reinsurance_haircut", context))
    net = number(gross - adjusted, "adjusted_net_best_estimate")
    require(net > 0, "adjusted_net_best_estimate", "nonpositive buffer denominator requires review", "REVIEW_REQUIRED")
    liquid = number(math.fsum(weighted), "haircut_liquid_assets", 0)
    ratio = number(liquid / net, "liquidity_buffer", 0)
    return caps_ok and ratio > _parameter("liquidity_buffer", context), {
        "pre_haircut_total": total, "pre_haircut_level2": level2, "pre_haircut_level2b": level2b,
        "pre_haircut_fund": fund, "composition_caps_met": caps_ok, "haircut_liquid_assets": liquid,
        "adjusted_net_best_estimate": net, "liquidity_buffer": ratio, "automatic_asset_trimming": False}


def future_long_term_qualification(inputs, context):
    """Qualified future subset using171b or the integrated171c projection check."""
    fields = ("conditions", "committed_average_holding_years", "avoidance_method", "avoidance_inputs",
              "assessment_level", "fund", "previous_breach")
    exact_keys(inputs, fields, "classification.inputs")
    conditions = ("subset_identified_and_separately_managed", "board_approved_strategy",
                  "strategy_frequently_reviewed_and_in_orsa", "eea_oecd_listing_or_domicile",
                  "policies_demonstrate_intention_and_capacity", "adequately_diversified",
                  "no_participations", "method_scope_appropriate",
                  "consistent_method_or_prior_supervisory_justification")
    exact_keys(inputs["conditions"], conditions, "conditions")
    require(all([_known_flag(inputs["conditions"][key], key) for key in conditions]),
            "conditions", "declared105a conditions not met", "REVIEW_REQUIRED")
    holding = number(inputs["committed_average_holding_years"], "committed_average_holding_years", 0)
    require(holding > _parameter("holding_years", context), "committed_average_holding_years",
            "future strategy must commit to more than the source threshold", "REVIEW_REQUIRED")
    level = inputs["assessment_level"]
    require(level in ("investment", "fund"), "assessment_level", "investment or fund required")
    if level == "fund":
        fund = inputs["fund"]
        exact_keys(fund, ("type", "qualified", "authorised_eu_aifm", "unleveraged_commitment_method",
                          "lookthrough_all", "exposure_kind"), "fund")
        require(fund["type"] in ("eltif", "eusef", "euveca", "closed_aif"), "fund.type",
                "Article171d fund required", "UNSUPPORTED_METHOD")
        require(_known_flag(fund["qualified"], "fund.qualified"), "fund", "fund qualification missing", "REVIEW_REQUIRED")
        for key in ("authorised_eu_aifm", "unleveraged_commitment_method"):
            if fund["type"] == "closed_aif":
                require(_known_flag(fund[key], key), key, "closed AIF condition not met", "REVIEW_REQUIRED")
            else:
                require(fund[key] is None, key, "not required for this fund type; use None")
        lookthrough = _known_flag(fund["lookthrough_all"], "lookthrough_all")
        require(fund["exposure_kind"] == ("underlying_equity" if lookthrough else "fund_unit"),
                "exposure_kind", "171d(3) scope does not match look-through", "REVIEW_REQUIRED")
    else:
        require(inputs["fund"] is None, "fund", "not needed for investment-level assessment; use None")
    breach = inputs["previous_breach"]
    if breach is not None:
        exact_keys(breach, ("months_to_restore", "months_since_exclusion_started"), "previous_breach")
        restoration = number(breach["months_to_restore"], "months_to_restore", 0)
        if restoration > _parameter("restoration_months", context):
            elapsed = number(breach["months_since_exclusion_started"], "months_since_exclusion_started", 0)
            require(elapsed >= _parameter("reentry_months", context), "months_since_exclusion_started",
                    "exclusion persists despite restored conditions", "REVIEW_REQUIRED")
        else:
            require(breach["months_since_exclusion_started"] is None, "months_since_exclusion_started",
                    "no exclusion inferred after timely restoration; use None")
    method = inputs["avoidance_method"]
    require(method in ("life_illiquid", "nonlife_buffer", "forced_selling"), "avoidance_method",
            "unknown forced-sale avoidance route", "UNSUPPORTED_METHOD")
    if method == "forced_selling":
        from .long_term_equity_forced_sale import forced_sale_qualification
        passed, audit = forced_sale_qualification(inputs["avoidance_inputs"], context)
    else:
        passed, audit = (_life if method == "life_illiquid" else _nonlife)(inputs["avoidance_inputs"], context)
    require(passed, "avoidance_inputs", "source-prescribed avoidance numerical conditions not met", "REVIEW_REQUIRED")
    return {"avoidance_method": method, "avoidance": audit, "assessment_level": level,
            "plan_deadline_months": _parameter("plan_months", context),
            "restoration_deadline_months": _parameter("restoration_months", context),
            "exclusion_months_after_failed_restoration": _parameter("reentry_months", context),
            "voluntary_return_permitted": False, "breach_requires_immediate_notification": True,
            "material_evidence_verified": False, "supervisory_notification_performed": False,
            "scope": "currently_compliant_declared_subset_not_breach_management_workflow"}
