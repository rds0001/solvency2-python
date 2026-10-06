"""Article168 route selection from qualified scope inputs and existing screens."""
from collections.abc import Mapping

from .core import exact_keys, require
from .loss_given_default import _known_flag, _reference


def equity_classification(category, evidence, context):
    if evidence is None:
        return {"status": "NOT_ASSESSED"}, []
    exact_keys(evidence, ("route", "inputs", "qualification_reference"), "classification")
    _reference(evidence["qualification_reference"], "classification.qualification_reference")
    route, inputs = evidence["route"], evidence["inputs"]
    require(isinstance(route, str), "classification.route", "explicit route required")
    require(isinstance(inputs, Mapping) and "context" not in inputs,
            "classification.inputs", "scope inputs without a separate context required")
    nested = None
    sources = ["DR:article-168:2-3b:6"]
    if route == "strategic":
        # Article171 judges evidence, not a fitted volatility model. The
        # future exclusion must not be backported into the historical profile.
        future = context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1"
        fields = ("related_undertaking", "lower_volatility_next_twelve_months",
                  "nature_and_influence_considered", "clear_long_term_strategy",
                  "consistent_with_business_strategy", "ability_to_hold",
                  "stable_relationship", "all_relevant_factors_considered",
                  "group_member", "consistent_with_group_strategy")
        exact_keys(inputs, (*fields, *(("lookthrough_applies",) if future else ())),
                   "classification.inputs")
        flags = {key: _known_flag(inputs[key], key) for key in fields[:-2]}
        group = _known_flag(inputs["group_member"], "group_member")
        if group:
            flags["consistent_with_group_strategy"] = _known_flag(
                inputs["consistent_with_group_strategy"], "consistent_with_group_strategy")
        else:
            require(inputs["consistent_with_group_strategy"] is None,
                    "consistent_with_group_strategy", "not applicable outside a group; use None")
        if future:
            flags["no_lookthrough"] = not _known_flag(inputs["lookthrough_applies"], "lookthrough_applies")
        require(all(flags.values()), "classification", "declared Article171 conditions not met",
                "REVIEW_REQUIRED")
        selected = "strategic"
        sources = ["DR:article-171", "DR:article-169:1-4:a"]
    elif route == "long_term":
        if context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1":
            from .long_term_equity_future import future_long_term_qualification
            nested = future_long_term_qualification(inputs, context)
            sources = ["DIR:article-105a", "DR:article-171a", "DR:article-171b", "DR:article-171d"]
            if inputs["avoidance_method"] == "forced_selling":
                sources.remove("DR:article-171b")
                sources.extend(("DR:article-171c", "DR:annex-II", "DR:annex-XIV", "DIR:annex-IV"))
        else:
            from .long_term_equity import baseline_long_term_qualification
            nested = baseline_long_term_qualification(inputs, context)
            sources = ["DR:article-171a:1-3"]
        selected = "long_term"
    elif route == "market":
        exact_keys(inputs, ("regulated_market_eea_oecd", "eu_mtf"), "classification.inputs")
        flags = {key: _known_flag(value, key) for key, value in inputs.items()}
        selected = "type1" if any(flags.values()) else "type2"
    elif route == "alternative":
        exact_keys(inputs, ("commodity_or_alternative",), "classification.inputs")
        require(_known_flag(inputs["commodity_or_alternative"], "commodity_or_alternative"),
                "classification", "qualified commodity or alternative scope required", "REVIEW_REQUIRED")
        selected = "type2"
    elif route == "residual":
        fields = ("captured_interest_property_or_spread", "lookthrough_possible", "article84_3_used")
        exact_keys(inputs, fields, "classification.inputs")
        flags = {key: _known_flag(inputs[key], key) for key in fields}
        require(not any(flags.values()), "classification", "residual168(3) scope not established", "UNSUPPORTED_METHOD")
        selected = "type2"
    elif route == "fund":
        fields = ("fund_type", "fund_qualification_confirmed", "lookthrough_all", "exposure_kind",
                  "qualified_infrastructure")
        extra = ("closed_ended", "eu_domiciled_or_marketed_under_35_40", "unleveraged_commitment_method")
        closed = inputs.get("fund_type") == "closed_aif"
        exact_keys(inputs, (*fields, *(extra if closed else ())), "classification.inputs")
        require(inputs["fund_type"] in ("eusef", "euveca", "closed_aif", "eltif"),
                "fund_type", "qualified168(6)a-d fund route required", "UNSUPPORTED_METHOD")
        qualified = _known_flag(inputs["fund_qualification_confirmed"], "fund_qualification_confirmed")
        lookthrough = _known_flag(inputs["lookthrough_all"], "lookthrough_all")
        infra = _known_flag(inputs["qualified_infrastructure"], "qualified_infrastructure")
        flags = [_known_flag(inputs[key], key) for key in extra] if closed else []
        require(qualified and all(flags), "fund_qualification", "declared fund conditions not met", "UNSUPPORTED_METHOD")
        require(inputs["exposure_kind"] == ("underlying_equity" if lookthrough else "fund_unit"),
                "exposure_kind", "full look-through selects underlying equities, otherwise fund units", "REVIEW_REQUIRED")
        require(not infra, "qualified_infrastructure", "use the separate infrastructure route", "UNSUPPORTED_METHOD")
        selected = "type1"
    elif route in ("infrastructure", "infrastructure_corporate", "unlisted_portfolio"):
        if route == "infrastructure":
            from .infrastructure_project import infrastructure_project_eligibility_screen as screen
            require(inputs.get("investment_kind") == "equity", "investment_kind", "equity scope required")
        elif route == "infrastructure_corporate":
            from .infrastructure_corporate import infrastructure_corporate_eligibility_screen as screen
            require(inputs.get("instrument") == "equity", "instrument", "equity scope required")
        else:
            from .unlisted_equity import unlisted_equity_portfolio_screen as screen
        result = screen(**inputs, context=context)
        require(result.value == 1, "classification", "selected qualification screen failed", "UNSUPPORTED_METHOD")
        nested = {"value": result.value, "details": result.details}
        sources.extend(result.sources)
        selected = "type1" if route == "unlisted_portfolio" else route
    else:
        require(False, "classification.route", "unknown classification route", "UNSUPPORTED_METHOD")
    # Long-term and strategic recognition use separate source qualifications.
    require(category == selected, "category", "category differs from qualified168 route", "REVIEW_REQUIRED")
    return {"status": "DECLARED_SCOPE_CHECKED_NOT_LEGAL_APPROVAL", "selected_category": selected,
            "route": route, "inputs": dict(inputs), "screen": nested,
            "qualification_reference": evidence["qualification_reference"]}, sources
