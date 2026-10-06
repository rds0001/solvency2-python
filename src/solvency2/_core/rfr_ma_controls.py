"""Declared MA application conditions, not supervisory approval or asset modelling."""
from .core import effective_resource, exact_keys, number, require


APPLICATION_FIELDS = (
    "prior_approval", "eligible_liability_scope", "assigned_assets_maintained",
    "separate_management_no_other_loss_cover", "same_currency_cashflow_replication",
    "no_material_mismatch", "no_future_premiums", "policyholder_options_qualified",
    "asset_cashflows_qualified", "contracts_not_split", "continuation_and_reentry_rules_met",
    "no_volatility_adjustment", "no_rate_transition")
RESTRUCTURED_FIELDS = (
    "underlying_returns_sufficiently_fixed", "loss_absorption_preserves_cashflows",
    "underlying_risks_managed", "evidence_demonstrable_to_supervisor")


def _flag(value, name):
    require(value is None or isinstance(value, bool), name, "boolean or None required")
    require(value is not None, name, "external condition unresolved", "REVIEW_REQUIRED")
    return value


def _conditions(values, fields):
    exact_keys(values, fields, "conditions")
    flags = {key: _flag(values[key], key) for key in fields}
    require(all(flags.values()), "conditions", "declared regulatory conditions not established", "REVIEW_REQUIRED")
    return flags


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field, "external reference required", "MISSING_INPUT")


def check_mortality_contract_selection(selection):
    """52(2/3) TP increase, not the SCR selector's TP-excluding-risk-margin basis."""
    if selection is None:
        return {"contract_selection_status": "NOT_ASSESSED", "contract_selection": None, "_sources": []}
    exact_keys(selection, ("valuation_basis", "grouping_mode", "grouping_qualified", "scenario_units"),
               "contract_selection")
    require(selection["valuation_basis"] in ("direct_insurance_contracts", "underlying_insurance_contracts"),
            "valuation_basis", "direct or underlying insurance contracts required", "UNSUPPORTED_METHOD")
    mode = selection["grouping_mode"]
    require(mode in ("individual", "same_insured", "article35"), "grouping_mode", "qualified grouping mode required")
    if mode == "individual":
        require(selection["grouping_qualified"] is None, "grouping_qualified", "omit unused grouping qualification")
    else:
        require(_flag(selection["grouping_qualified"], "grouping_qualified"), "grouping_qualified",
                "same-insured / Article35 equivalent selection not qualified", "REVIEW_REQUIRED")
    scenarios = selection["scenario_units"]
    exact_keys(scenarios, ("permanent", "next_twelve_months"), "scenario_units")
    from collections.abc import Mapping
    masks, units, base_values = {}, None, {}
    for scenario, rows in scenarios.items():
        require(isinstance(rows, Mapping) and bool(rows), scenario, "nonempty labelled valuation units required", "MISSING_INPUT")
        require(all(isinstance(key, str) and key.strip() for key in rows), scenario, "nonempty unit IDs required")
        if units is None:
            units = set(rows)
        require(set(rows) == units, "scenario_units", "same valuation units required in both scenarios")
        masks[scenario] = {}
        for label, row in rows.items():
            exact_keys(row, ("base_technical_provisions", "stressed_technical_provisions", "stress_applied"), label)
            base = number(row["base_technical_provisions"], label + ".base_technical_provisions")
            require(label not in base_values or base == base_values[label], label,
                    "same unstressed TP basis required across scenarios")
            base_values[label] = base
            stressed = number(row["stressed_technical_provisions"], label + ".stressed_technical_provisions")
            selected = stressed > base
            require(_flag(row["stress_applied"], label + ".stress_applied") == selected, label,
                    "stress must apply exactly to TP-increasing units", "REVIEW_REQUIRED")
            masks[scenario][label] = selected
    return {"contract_selection_status": "DECLARED_SELECTION_CHECKED_EXTERNAL_UNVERIFIED",
            "contract_selection": {"valuation_basis": selection["valuation_basis"], "grouping_mode": mode,
                "grouping_qualified": selection["grouping_qualified"], "selection_masks": masks,
                "aggregate_scenario_projection_verified": False}, "_sources": ["DR:article-52:2-3"]}


def apply_subinvestment_comparison(value, residual, comparison):
    """Increase residual FS only against an explicitly same-scope IG benchmark."""
    if comparison is None:
        return value, {"subinvestment_comparison_status": "NOT_ASSESSED",
                       "subinvestment_comparison": None, "additional_fundamental_spread": 0,
                       "effective_residual_fundamental_spread": residual}
    flags = ("same_duration", "same_asset_category", "comparison_applies_to_entire_input_scope")
    exact_keys(comparison, (*flags, "investment_grade_matching_adjustment", "qualification_reference"),
               "subinvestment_grade_comparison")
    _conditions({key: comparison[key] for key in flags}, flags)
    _reference(comparison["qualification_reference"], "comparison.qualification_reference")
    maximum = number(comparison["investment_grade_matching_adjustment"], "investment_grade_matching_adjustment")
    selected = min(value, maximum)
    increase = number(value - selected, "additional_fundamental_spread", 0)
    effective = number(residual + increase, "effective_residual_fundamental_spread")
    return selected, {"subinvestment_comparison_status": "DECLARED_COMPARISON_APPLIED_EXTERNAL_UNVERIFIED",
        "subinvestment_comparison": dict(comparison), "additional_fundamental_spread": increase,
        "effective_residual_fundamental_spread": effective}


def check_matching_application(application, restructured_assets, value, qualification_reference, context):
    """Reject failed declared gates; do not silently repair rates or valuations."""
    audit, restructuring, sources = None, None, []
    if application is not None:
        exact_keys(application, ("approval_reference", "conditions", "underwriting_risks", "mortality"), "application")
        _reference(application["approval_reference"], "approval_reference")
        flags = _conditions(application["conditions"], APPLICATION_FIELDS)
        risks = application["underwriting_risks"]
        require(isinstance(risks, (list, tuple)) and all(isinstance(risk, str) for risk in risks),
                "underwriting_risks", "explicit risk list required")
        require(len(set(risks)) == len(risks), "underwriting_risks", "duplicate risks")
        require(set(risks) <= {"longevity", "expense", "revision", "mortality"},
                "underwriting_risks", "risk outside Article77b(1)(e)", "REVIEW_REQUIRED")
        mortality = application["mortality"]
        mortality_audit = None
        if "mortality" in risks:
            exact_keys(mortality, ("base_best_estimate", "stressed_best_estimate"), "mortality")
            # Reuse the profile-bound regulatory threshold and its override audit.
            from .rfr import rfr_matching_mortality_headroom
            headroom = rfr_matching_mortality_headroom(**mortality,
                qualification_reference=qualification_reference, context=context)
            require(headroom.value >= 0, "mortality", "mortality BE increase exceeds limit", "REVIEW_REQUIRED")
            mortality_audit = headroom.to_dict()
        else:
            require(mortality is None, "mortality", "omit unused mortality scenario")
        audit = {"approval_reference": application["approval_reference"], "conditions": flags,
                 "underwriting_risks": list(risks), "mortality": mortality_audit,
                 "qualification_status": "EXTERNAL_UNVERIFIED", "supervisory_approval_verified": False}
        sources.extend(["DIR:article-77b:1", "DIR:article-77b:3"])
    if restructured_assets is not None:
        require(audit is not None, "application", "restructured route requires declared MA application", "MISSING_INPUT")
        future = effective_resource("profile.json", context).get("methods", {}).get("volatility_adjustment") == "VA_2027"
        require(future, "restructured_assets", "Article54a route only qualified in future profile", "UNSUPPORTED_RULESET")
        exact_keys(restructured_assets, ("conditions", "financial_guarantees_present",
            "without_guarantees_matching_adjustment", "comparison_reference"), "restructured_assets")
        flags = _conditions(restructured_assets["conditions"], RESTRUCTURED_FIELDS)
        present = _flag(restructured_assets["financial_guarantees_present"], "financial_guarantees_present")
        _reference(restructured_assets["comparison_reference"], "comparison_reference")
        comparator = restructured_assets["without_guarantees_matching_adjustment"]
        if present:
            comparator = number(comparator, "without_guarantees_matching_adjustment")
            require(value <= comparator, "restructured_assets",
                    "financial guarantees may not increase matching adjustment", "REVIEW_REQUIRED")
        else:
            require(comparator is None, "without_guarantees_matching_adjustment", "omit unused guarantee comparison")
        restructuring = {"conditions": flags, "financial_guarantees_present": present,
            "without_guarantees_matching_adjustment": comparator,
            "comparison_reference": restructured_assets["comparison_reference"],
            "qualification_status": "EXTERNAL_UNVERIFIED", "comparison_scope_verified": False}
        sources.append("DR:article-54a:2")
    return {"application": audit, "restructured_assets": restructuring,
            "application_status": "DECLARED_CONDITIONS_CHECKED_EXTERNAL_UNVERIFIED" if audit else "NOT_ASSESSED",
            "_sources": sources}
