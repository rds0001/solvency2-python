"""Document-profile scope screens, never automatic legal non-applicability."""
from fractions import Fraction
from collections.abc import Sequence

from .core import Context, calculation, effective_resource, number, require, scalar


def _history_reference(value):
    require(isinstance(value, str) and bool(value.strip()), "qualification_reference",
            "external consecutive periods and historically applicable thresholds required", "MISSING_INPUT")


def _annual_flags(values, field, parameter, context):
    count = number(scalar(parameter, context), parameter, 1)
    require(count.is_integer(), parameter, "positive whole-year window required")
    require(isinstance(values, Sequence) and not isinstance(values, (str, bytes)), field, "explicit annual boolean sequence required")
    require(len(values) == int(count), field, "exact annual period count required")
    for index, value in enumerate(values):
        require(value is not None, f"{field}[{index}]", "annual exceedance unresolved", "REVIEW_REQUIRED")
        require(isinstance(value, bool), f"{field}[{index}]", "explicit boolean required")
    return list(values)


@calculation("DIR:article-4:2", unit="indicator")
def scope_volume_entry_trigger(annual_exceedance: Sequence, *, qualification_reference: str, context: Context):
    """Three-year breach of one identified amount, for the following-year trigger.

    Period consecutiveness and historically applicable thresholds are externally
    qualified. Different monetary criteria must not be mixed within a series.
    This component does not select an effective legal regime for the entity.
    """
    _history_reference(qualification_reference)
    flags = _annual_flags(annual_exceedance, "annual_exceedance", "scope_volume_history_years", context)
    return int(all(flags)), {"annual_exceedance": flags, "history_years": len(flags),
                             "qualification_reference": qualification_reference,
                             "qualification_status": "EXTERNAL_UNVERIFIED",
                             "scope": "same_amount_consecutive_breach_trigger_for_following_year_not_legal_scope_decision"}


@calculation("DIR:article-4:4:a-b", unit="indicator")
def scope_volume_release_history(past_any_exceedance: Sequence, forecast_any_exceedance: Sequence, *,
                                  qualification_reference: str, context: Context):
    """Only historical/prospective volume conditions, not supervisory release.

    Forecasts are external. Cross-border activity, voluntary authorisation and
    supervisory satisfaction remain separate, even when this indicator is1.
    """
    _history_reference(qualification_reference)
    past = _annual_flags(past_any_exceedance, "past_any_exceedance", "scope_volume_history_years", context)
    forecast = _annual_flags(forecast_any_exceedance, "forecast_any_exceedance", "scope_volume_forecast_years", context)
    historical_clear, forecast_clear = not any(past), not any(forecast)
    return int(historical_clear and forecast_clear), {
        "past_any_exceedance": past, "forecast_any_exceedance": forecast,
        "historical_clear": historical_clear, "forecast_clear": forecast_clear,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "release_volume_history_only_not_forecast_model_or_supervisory_release"}


@calculation("DIR:article-4:1", "DIR:article-16:1-2", unit="indicator")
def scope_volume_conditions(gross_written_premiums: float, gross_technical_provisions: float,
                             reinsurance_written_premiums: float, reinsurance_technical_provisions: float, *,
                             part_of_group: bool | None, group_gross_technical_provisions: float | None = None,
                             has_disallowed_business: bool | None, qualification_reference: str, context: Context):
    """Screen one year's literal Article4(1) conditions in the selected profile.

    Inputs are externally qualified gross EUR amounts. No netting or zero floor
    is inferred. Article4(2-5) time rules, authorisation and cross-border business
    must be assessed separately; a result of1 is not a scope exemption.
    """
    require(context.currency == "EUR", "currency", "qualified EUR inputs required; no automatic Article299 conversion",
            "UNSUPPORTED_PARAMETER")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external gross-volume and business qualification required", "MISSING_INPUT")
    for name, value in (("part_of_group", part_of_group), ("has_disallowed_business", has_disallowed_business)):
        require(value is not None, name, "external classification unresolved", "REVIEW_REQUIRED")
        require(isinstance(value, bool), name, "explicit boolean required")
    inputs = {
        "gross_written_premiums": number(gross_written_premiums, "gross_written_premiums"),
        "gross_technical_provisions": number(gross_technical_provisions, "gross_technical_provisions"),
        "reinsurance_written_premiums": number(reinsurance_written_premiums, "reinsurance_written_premiums"),
        "reinsurance_technical_provisions": number(reinsurance_technical_provisions, "reinsurance_technical_provisions"),
    }
    if part_of_group:
        group_tp = number(group_gross_technical_provisions, "group_gross_technical_provisions")
    else:
        require(group_gross_technical_provisions is None, "group_gross_technical_provisions", "omit unused group amount")
        group_tp = None
    suffixes = ("premium_limit", "tp_limit", "group_tp_limit", "reinsurance_premium_limit",
                "reinsurance_tp_limit", "reinsurance_premium_share", "reinsurance_tp_share")
    limits = {key: number(scalar("scope_volume_" + key, context), key, 0, 1 if key.endswith("_share") else None)
              for key in suffixes}
    # Exact decimal comparisons preserve inclusive thresholds without tolerance.
    amounts = {key: Fraction(str(value)) for key, value in inputs.items()}
    thresholds = {key: Fraction(str(value)) for key, value in limits.items()}
    checks = {
        "premium_limit": amounts["gross_written_premiums"] <= thresholds["premium_limit"],
        "tp_limit": amounts["gross_technical_provisions"] <= thresholds["tp_limit"],
        "group_tp_limit": group_tp is None or Fraction(str(group_tp)) <= thresholds["group_tp_limit"],
        "business_condition": not has_disallowed_business,
        "reinsurance_premium_absolute": amounts["reinsurance_written_premiums"] <= thresholds["reinsurance_premium_limit"],
        "reinsurance_tp_absolute": amounts["reinsurance_technical_provisions"] <= thresholds["reinsurance_tp_limit"],
        "reinsurance_premium_relative": amounts["reinsurance_written_premiums"] <=
            thresholds["reinsurance_premium_share"] * amounts["gross_written_premiums"],
        "reinsurance_tp_relative": amounts["reinsurance_technical_provisions"] <=
            thresholds["reinsurance_tp_share"] * amounts["gross_technical_provisions"],
    }
    return int(all(checks.values())), {
        "amounts": inputs, "group_gross_technical_provisions": group_tp, "part_of_group": part_of_group,
        "has_disallowed_business": has_disallowed_business, "thresholds": limits, "conditions": checks,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "one_year_article4_conditions_not_legal_exemption_or_authorisation_decision"}


@calculation("DIR:article-16:1-2", "DIR:annex-I:A", unit="indicator")
def scope_ancillary_risk_conditions(ancillary_branch: int, main_branch: int, *,
                                    main_risk_authorised: bool | None, linked_to_main: bool | None,
                                    same_object: bool | None, same_contract: bool | None,
                                    legal_expenses_exception: str | None = None,
                                    qualification_reference: str, context: Context):
    """Apply Article16's cross-branch conditions to external factual declarations.

    Credit/surety remain prohibited. Legal expenses require the assistance main
    branch and the explicitly declared travel or sea-vessel exception; all base
    conditions still apply. This function does not grant or verify a licence.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external contract and authorisation qualification required", "MISSING_INPUT")
    flags = {"main_risk_authorised": main_risk_authorised, "linked_to_main": linked_to_main,
             "same_object": same_object, "same_contract": same_contract}
    for name, value in flags.items():
        require(value is not None, name, "external factual condition unresolved", "REVIEW_REQUIRED")
        require(isinstance(value, bool), name, "explicit boolean required")
    data = effective_resource("profile.json", context)["tables"]["scope_nonlife_branches"]
    require(data["columns"] == ["branch", "label_de", "ancillary_rule", "exception_main_branch"],
            "scope_nonlife_branches", "unexpected branch table schema")
    rows = {}
    for row in data["rows"]:
        code = number(row[0], "branch_code", 1)
        require(code.is_integer() and code not in rows, "branch_code", "distinct positive integer branch codes required")
        require(row[2] in ("ordinary", "prohibited", "legal_expenses"), "ancillary_rule", "unknown table rule")
        rows[int(code)] = row
    for row in rows.values():
        if row[2] == "legal_expenses":
            special_main = number(row[3], "exception_main_branch", 1)
            require(special_main.is_integer() and special_main in rows, "exception_main_branch", "known integer branch required")
        else:
            require(row[3] is None, "exception_main_branch", "omit unused table exception")
    ancillary = number(ancillary_branch, "ancillary_branch", 1)
    main = number(main_branch, "main_branch", 1)
    require(ancillary.is_integer() and ancillary in rows, "ancillary_branch", "known AnnexI branch required", "UNSUPPORTED_PARAMETER")
    require(main.is_integer() and main in rows, "main_branch", "known AnnexI branch required", "UNSUPPORTED_PARAMETER")
    require(ancillary != main, "ancillary_branch", "Article16 screen is for a different branch")
    row = rows[int(ancillary)]
    if row[2] == "legal_expenses":
        require(legal_expenses_exception is not None, "legal_expenses_exception", "explicit exception decision required", "REVIEW_REQUIRED")
        require(legal_expenses_exception in ("none", "travel_assistance", "sea_vessel"),
                "legal_expenses_exception", "unsupported declared exception", "UNSUPPORTED_PARAMETER")
        branch_allowed = main == row[3] and legal_expenses_exception != "none"
    else:
        require(legal_expenses_exception is None, "legal_expenses_exception", "omit unused exception")
        branch_allowed = row[2] == "ordinary"
    return int(all(flags.values()) and branch_allowed), {
        "ancillary_branch": int(ancillary), "main_branch": int(main), "ancillary_label": row[1],
        "ancillary_rule": row[2], "declared_conditions": flags, "branch_condition": branch_allowed,
        "legal_expenses_exception": legal_expenses_exception,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "declared_ancillary_risk_conditions_not_licence_or_factual_qualification"}
