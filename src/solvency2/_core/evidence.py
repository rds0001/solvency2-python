"""Source-bound evidence inventories and accompanying arithmetic components."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _evidence_inventory(evidence, table, assessment_reference):
    """Preserve missing versus unknown declarations; never retrieve references."""
    require(isinstance(assessment_reference, str) and bool(assessment_reference.strip()),
            "assessment_reference", "versioned external assessment reference required", "MISSING_INPUT")
    require(isinstance(evidence, Mapping), "evidence", "control-labelled evidence mapping required")
    rows = table["rows"]
    ids = [row[0] for row in rows]
    require(bool(ids) and len(ids) == len(set(ids)), "control_table", "nonempty unique control IDs required", "REVIEW_REQUIRED")
    require(not set(evidence) - set(ids), "evidence", "unknown control for selected profile")
    counts = {"AVAILABLE": 0, "MISSING": 0, "UNKNOWN": 0}
    decisions = {}
    for control, source, description in rows:
        present = control in evidence
        record = evidence[control] if present else {"status": "MISSING", "reference": None}
        exact_keys(record, ("status", "reference"), f"evidence.{control}")
        status, reference = record["status"], record["reference"]
        require(isinstance(status, str) and status in counts, f"evidence.{control}.status",
                "AVAILABLE, MISSING or UNKNOWN declaration required")
        if status == "AVAILABLE":
            require(isinstance(reference, str) and bool(reference.strip()), f"evidence.{control}.reference",
                    "available evidence requires a nonempty reference", "MISSING_INPUT")
        else:
            require(reference is None or isinstance(reference, str) and bool(reference.strip()),
                    f"evidence.{control}.reference", "None or nonempty reference required")
        counts[status] += 1
        decisions[control] = {"status": status, "reference": reference, "input_present": present,
                              "source": source, "description": description}
    return int(counts["AVAILABLE"] == len(ids)), {
        "controls": decisions, "counts": counts, "required_control_count": len(ids),
        "assessment_reference": assessment_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "evidence_content_verified": False, "references_retrieved": False,
        "_sources": [row[1] for row in rows]}


@calculation("DIR:article-45", "DIR:article-45:7", "DR:article-262", unit="indicator")
def orsa_core_evidence_check(evidence: Mapping[str, dict], *, assessment_reference: str, context: Context):
    """Inventory explicitly declared core evidence, not adequacy or compliance.

    AVAILABLE means the caller supplies a reference; content is not inspected.
    A value of1 certifies neither ORSA completeness nor a capital requirement.
    Conditional comparisons, timing, recalibration and climate scenarios remain
    separate. The 2027 table adds mandatory macro/liquidity/materiality topics.
    """
    table = effective_resource("profile.json", context)["tables"]["orsa_core_controls"]
    value, details = _evidence_inventory(evidence, table, assessment_reference)
    return value, {**details, "scope": "core_evidence_inventory_not_ORSA_assessment_or_SCR",
                   "conditional_requirements_included": False}


@calculation("DR:article-19", "DR:article-20", unit="indicator")
def technical_provision_data_evidence_check(evidence: Mapping[str, dict], *, external_data_used: bool,
                                            data_deficiencies_present: bool,
                                            assessment_reference: str, context: Context):
    """Inventory TP data-quality evidence without certifying data or methods.

    External-data use and known deficiencies activate their own controls.
    The 2027 climate-history safeguard is unconditional, not a defect-only rule.
    AVAILABLE declares a reference, never verified content or legal compliance.
    """
    conditions = {
        "external_data_used": _declared_bool(external_data_used, "external_data_used"),
        "data_deficiencies_present": _declared_bool(data_deficiencies_present, "data_deficiencies_present")}
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["technical_provision_data_controls"]["rows"]
    active = [r[:3] for r in rows if r[3] == "always" or conditions[r[3]]]
    value, details = _evidence_inventory(evidence, {"rows": active}, assessment_reference)
    return value, {**details, "conditions": conditions,
        "inactive_controls": [r[0] for r in rows if r[3] != "always" and not conditions[r[3]]],
        "data_quality_certified": False, "approximation_permitted": False,
        "scope": "declared_TP_data_evidence_inventory_not_quality_or_method_approval",
        "_sources": details["_sources"] + [context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                                            + ":articles-19-20"]}


@calculation("DR:article-21", unit="indicator")
def best_estimate_approximation_conditions(conditions: Mapping[str, bool], *,
                                          qualification_reference: str, context: Context):
    """Check declared data-deficiency exception, not create an approximation.

    Inadequate internal processes cannot justify this exception. Neither an
    invented materiality percentage nor a preferred actuarial model is supplied.
    """
    _reference(qualification_reference, "qualification_reference")
    keys = ("data_insufficient_for_reliable_method", "internal_processes_appropriate",
            "external_data_cannot_remedy", "data_adjustment_impracticable", "approximation_appropriate")
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        _declared_bool(conditions[key], key)
    profile = effective_resource("profile.json", context)
    return int(all(conditions.values())), {
        "conditions": dict(conditions), "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "approximation_generated": False,
        "scope": "declared_article21_conditions_only_not_actuarial_method_approval",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-21"]}


def _technical_provision_method_evidence(evidence, conditions, assessment_reference,
                                         scope_reference, group, context):
    """Select source-bound evidence controls without performing their assessments."""
    _reference(scope_reference, "scope_reference")
    profile = effective_resource("profile.json", context)
    rows = profile["tables"][f"technical_provision_{group}_controls"]["rows"]
    keys = sorted({row[3] for row in rows if row[3] != "always"})
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        _declared_bool(conditions[key], key)
    if group == "assumptions":
        require(not conditions["financial_projection_model_used"] or conditions["financial_market_assumptions_used"],
                "conditions", "financial projection model requires financial-market assumptions")
        require(not conditions["behaviour_independence_assumed"] or conditions["policyholder_options_present"],
                "conditions", "behaviour independence requires policyholder options")
    selected = [row[:3] for row in rows if row[3] == "always" or conditions[row[3]]]
    value, details = _evidence_inventory(evidence, {"rows": selected}, assessment_reference)
    return value, {**details, "conditions": dict(conditions), "scope_reference": scope_reference,
        "inactive_controls": [row[0] for row in rows if row[3] != "always" and not conditions[row[3]]],
        "cashflows_generated": False, "insurer_model_implemented": False,
        "qualified_expert_review_performed": False,
        "scope": f"declared_TP_{group}_evidence_not_actuarial_valuation_or_approval",
        "_sources": details["_sources"] + [context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                                            + ":TP-" + group]}


@calculation("DR:articles-22-27", unit="indicator")
def technical_provision_assumptions_evidence_check(evidence: Mapping[str, dict],
                                                   conditions: Mapping[str, bool], *,
                                                   assessment_reference: str, scope_reference: str,
                                                   context: Context):
    """Inventory assumptions, management actions, FDB and behaviour evidence.

    Financial models and insurer-specific behaviour remain external. Conditional
    evidence is selected from explicit qualified scope decisions. A fully declared
    inventory proves neither method appropriateness nor supervisory compliance.
    """
    value, details = _technical_provision_method_evidence(
        evidence, conditions, assessment_reference, scope_reference, "assumptions", context)
    reports = None
    if conditions["management_actions_assumed"]:
        reports = number(scalar("tp_management_reports_per_year_minimum", context),
                         "tp_management_reports_per_year_minimum", 0)
        require(reports > 0, "tp_management_reports_per_year_minimum", "positive reporting frequency required")
    return value, {**details, "minimum_management_reports_per_year": reports,
                   "reporting_timing_verified": False}


@calculation("DR:articles-28-34", "DR:article-36", unit="indicator")
def technical_provision_projection_evidence_check(evidence: Mapping[str, dict],
                                                  conditions: Mapping[str, bool], *,
                                                  assessment_reference: str, scope_reference: str,
                                                  context: Context):
    """Inventory projection scope/uncertainty/expenses, not simulate cashflows.

    The 2027 expense basis reflects board decisions on new business; it does not
    silently inherit the baseline assumption of future new business. Category
    controls document relevance and appropriate inclusion, including reasoned
    absence. Currency separation and gross reinsurance expenses remain explicit.
    """
    value, details = _technical_provision_method_evidence(
        evidence, conditions, assessment_reference, scope_reference, "projection", context)
    return value, {**details, "expense_new_business_rule":
                   details["controls"]["expenses_new_business_basis"]["description"]}


def _declared_bool(value, field):
    """Unknown qualification is not equivalent to a negative finding."""
    require(value is not None, field, "external qualification unresolved", "REVIEW_REQUIRED")
    require(isinstance(value, bool), field, "explicit boolean required")
    return value


@calculation("DIR:article-45:2a:a-b", unit="indicator")
def orsa_phase_in_currency_exemption_2027(currency_cashflows: float,
                                         extrapolated_currency_cashflows: float,
                                         total_cashflows: float, *,
                                         qualification_reference: str, context: Context):
    """Screen only the Article77a phase-in comparison exemption per currency.

    Both denominators are ALL future cashflows. Do not substitute cashflows
    in this currency for the denominator of the extrapolated-share test.
    Signed raw cashflows need externally qualified aggregation, not abs/netting
    guessed by the engine. No exemption for MA, VA or other transition tests.
    """
    _reference(qualification_reference, "qualification_reference")
    amounts = [number(v, name) for v, name in (
        (currency_cashflows, "currency_cashflows"),
        (extrapolated_currency_cashflows, "extrapolated_currency_cashflows"),
        (total_cashflows, "total_cashflows"))]
    require(all(v >= 0 for v in amounts), "cashflows",
            "signed cashflows require externally qualified aggregation", "UNSUPPORTED_METHOD")
    currency, extrapolated, total = map(lambda v: Fraction(str(v)), amounts)
    require(total > 0, "total_cashflows", "positive total denominator required", "REVIEW_REQUIRED")
    require(extrapolated <= currency <= total, "cashflows", "extrapolated <= currency <= total required")
    currency_limit = number(scalar("orsa_phase_in_currency_share_limit", context), "currency_limit", 0, 1)
    extrapolated_limit = number(scalar("orsa_phase_in_extrapolated_share_limit", context), "extrapolated_limit", 0, 1)
    currency_ok = currency <= Fraction(str(currency_limit)) * total
    extrapolated_ok = extrapolated <= Fraction(str(extrapolated_limit)) * total
    return int(currency_ok or extrapolated_ok), {
        "currency_share": float(currency / total), "extrapolated_share_of_all_cashflows": float(extrapolated / total),
        "currency_condition": currency_ok, "extrapolated_condition": extrapolated_ok,
        "denominator_scope": "all_future_insurance_and_reinsurance_cashflows",
        "scope": "article77a_phase_in_currency_comparison_only",
        "other_adjustment_comparisons_exempted": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED"}


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external assessment reference required", "MISSING_INPUT")


@calculation("DR:article-37:2", unit="indicator")
def risk_margin_internal_model_required(uses_approved_internal_model: bool,
                                        suitable_all_runoff_times: bool | None, *,
                                        qualification_reference: str, context: Context):
    """Regulatory selection condition only; insurer supplies the approved model.

    A zero result does not approve another method. Suitability covers EVERY
    runoff time; no such finding is inferred from one successful valuation.
    """
    _reference(qualification_reference, "qualification_reference")
    use = _declared_bool(uses_approved_internal_model, "uses_approved_internal_model")
    if use or suitable_all_runoff_times is not None:
        _declared_bool(suitable_all_runoff_times, "suitable_all_runoff_times")
    profile = effective_resource("profile.json", context)
    return int(use and suitable_all_runoff_times is True), {
        "uses_approved_internal_model": use, "suitable_all_runoff_times": suitable_all_runoff_times,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "internal_model_support": "EXTERNAL_INPUT_ONLY", "alternative_method_approved": False,
        "scope": "article37_2_model_selection_condition_only",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-37-2"]}


@calculation("DR:article-38:1:g", unit="currency")
def risk_margin_reference_asset_balance(reference_scr: float, technical_provisions: float,
                                        recoverables: float, *, qualification_reference: str, context: Context):
    """SCR + TP - recoverables, not an asset portfolio or optimisation result.

    Preserve signs and disclose a negative implied balance. Qualification of
    values and a feasible market-risk-minimising portfolio remain external.
    """
    _reference(qualification_reference, "qualification_reference")
    scr = number(reference_scr, "reference_scr", 0)
    tp = number(technical_provisions, "technical_provisions")
    rec = number(recoverables, "recoverables")
    balance = Fraction(str(scr)) + Fraction(str(tp)) - Fraction(str(rec))
    try:
        result = float(balance)
    except OverflowError:
        require(False, "asset_balance", "balance outside representable range", "REVIEW_REQUIRED")
    return result, {"reference_scr": scr, "technical_provisions": tp, "recoverables": rec,
        "negative_implied_balance": balance < 0, "asset_portfolio_verified": False,
        "market_risk_minimisation_verified": False, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "reference_undertaking_balance_identity_only"}


@calculation("DR:article-38:1-3", unit="indicator")
def risk_margin_reference_evidence_check(evidence: Mapping[str, dict], composite_undertaking: bool,
                                         material_residual_market_risk: bool, *, qualification_reference: str,
                                         assessment_reference: str, context: Context):
    """Inventory reference-undertaking assumptions, never generate SCR runoff.

    Composite splitting and residual non-interest market risk have explicit
    externally assessed conditions. No quantitative materiality cutoff is
    invented; deferred-tax loss absorption must not be assumed.
    """
    _reference(qualification_reference, "qualification_reference")
    composite = _declared_bool(composite_undertaking, "composite_undertaking")
    market = _declared_bool(material_residual_market_risk, "material_residual_market_risk")
    active = {"always": True, "composite": composite, "market": market}
    table = effective_resource("profile.json", context)["tables"]["risk_margin_reference_controls"]
    rows = [row[:3] for row in table["rows"] if active[row[3]]]
    value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    return value, {**details, "composite_undertaking": composite,
        "material_residual_market_risk": market, "qualification_reference": qualification_reference,
        "scope": "reference_undertaking_evidence_inventory_only",
        "scr_runoff_generated": False, "projected_scr_verified": False,
        "internal_model_generated": False}


@calculation("DIR:article-246:4", unit="currency")
def group_orsa_method1_scr_difference(related_scrs: Mapping[str, float], consolidated_scr: float, *,
                                      qualification_reference: str, context: Context):
    """Signed related-SCR sum minus consolidated SCR, never floored.

    The externally qualified perimeter must match Article246(4), method1,
    valuation date and currency. This arithmetic is not the required substantive
    explanation of the difference, nor a release of diversification benefits.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(related_scrs, Mapping) and bool(related_scrs),
            "related_scrs", "nonempty entity-labelled SCR mapping required")
    values = {}
    for key, value in related_scrs.items():
        require(isinstance(key, str) and bool(key.strip()), "related_scrs", "nonempty entity IDs required")
        values[key] = number(value, f"related_scrs.{key}", 0)
    consolidated = number(consolidated_scr, "consolidated_scr", 0)
    total = sum((Fraction(str(v)) for v in values.values()), Fraction(0))
    difference = total - Fraction(str(consolidated))
    try:
        result = float(difference)
    except OverflowError:
        require(False, "difference", "difference outside representable range", "REVIEW_REQUIRED")
    return result, {"related_scrs": values, "consolidated_scr": consolidated,
        "difference_explanation_verified": False, "scope": "method1_SCR_difference_only",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DIR:article-246:4", unit="indicator")
def group_orsa_evidence_check(evidence: Mapping[str, dict], method1_applied: bool, single_document: bool, *,
                              qualification_reference: str, assessment_reference: str, context: Context):
    """Inventory group-ORSA scope, method1 and single-document evidence.

    No consent is inferred from availability of a group document. Subsidiary
    Article45 duties persist. The future profile separately includes material
    non-insurance activities and actual/potential risks/interdependencies.
    """
    _reference(qualification_reference, "qualification_reference")
    method1 = _declared_bool(method1_applied, "method1_applied")
    single = _declared_bool(single_document, "single_document")
    active = {"always": True, "method1": method1, "single_document": single}
    table = effective_resource("profile.json", context)["tables"]["group_orsa_controls"]
    rows = [row[:3] for row in table["rows"] if active[row[3]]]
    value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    return value, {**details, "method1_applied": method1, "single_document": single,
        "subsidiary_article45_duties_preserved": True, "supervisory_approval_verified": False,
        "group_governance_complete": False, "qualification_reference": qualification_reference,
        "scope": "group_ORSA_evidence_inventory_only"}


@calculation("DR:article-306", "DR:article-313", unit="indicator")
def orsa_report_evidence_check(evidence: Mapping[str, dict], significant_uncovered_risk_deviation: bool, *,
                               qualification_reference: str, assessment_reference: str, context: Context):
    """Inventory report content/transmission evidence, not the report itself.

    Quantification of non-reflected risks is conditional on externally assessed
    significance. Future electronic form also requires machine readability and
    searchable text/figures. No format inspection, filing or deadline approval.
    """
    _reference(qualification_reference, "qualification_reference")
    significant = _declared_bool(significant_uncovered_risk_deviation, "significant_uncovered_risk_deviation")
    table = effective_resource("profile.json", context)["tables"]["orsa_report_controls"]
    rows = [row[:3] for row in table["rows"] if row[3] == "always" or significant]
    value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    return value, {**details, "significant_uncovered_risk_deviation": significant,
        "qualification_reference": qualification_reference, "scope": "ORSA_report_evidence_inventory_only",
        "submission_verified": False, "file_format_verified": False, "deadline_verified": False}


@calculation("DIR:article-45:2a", "DIR:article-45:3", unit="indicator")
def orsa_conditional_evidence_check(adjustments: Mapping[str, bool], uses_internal_model: bool,
                                     evidence: Mapping[str, dict], *, qualification_reference: str,
                                     assessment_reference: str, context: Context):
    """Inventory conditional comparisons/recalibration, never calculate a model.

    The phase-in flag means a comparison remains required after externally
    qualified currency exemptions. Its false value is not inferred from
    missing data. Comparability evidence is technical traceability, not a
    prescribed projection method or an isolated-scenario requirement.
    """
    _reference(qualification_reference, "qualification_reference")
    _reference(assessment_reference, "assessment_reference")
    profile = effective_resource("profile.json", context)
    flags = [row[0] for row in profile["tables"]["orsa_adjustment_controls"]["rows"]]
    exact_keys(adjustments, flags, "adjustments")
    facts = {flag: _declared_bool(adjustments[flag], f"adjustments.{flag}") for flag in flags}
    internal = _declared_bool(uses_internal_model, "uses_internal_model")
    rows = []
    if any(facts.values()):
        rows.extend([
            ["capital_with_adjustments", "DIR:article-45:2a", "Capital compliance assessment with applicable measures"],
            ["capital_without_adjustments", "DIR:article-45:2a", "Capital compliance assessment without applicable measures"],
            ["comparison_basis", "DIR:article-45:2a", "Technical traceability of the comparison basis"],
        ])
    if internal:
        rows.append(["model_recalibration", "DIR:article-45:3", "External recalibration to SCR risk measure/calibration"])
    future_va = "phase_in_77a_comparison" in facts and facts["volatility_adjustment"]
    if future_va:
        rows.append(["va_risk_profile_deviation", "DIR:article-45:2b", "Risk-profile deviation from VA assumptions"])
    if rows:
        value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    else:
        require(isinstance(evidence, Mapping) and not evidence, "evidence",
                "no evidence controls applicable for supplied flags; empty mapping required")
        value, details = 1, {
            "controls": {}, "counts": {"AVAILABLE": 0, "MISSING": 0, "UNKNOWN": 0},
            "required_control_count": 0, "assessment_reference": assessment_reference,
            "qualification_status": "EXTERNAL_UNVERIFIED", "evidence_content_verified": False,
            "references_retrieved": False}
    return value, {**details, "adjustments": facts, "uses_internal_model": internal,
        "requirements_applicable": bool(rows), "qualification_reference": qualification_reference,
        "scope": "conditional_evidence_inventory_only", "core_ORSA_included": False}


@calculation("DIR:article-45:1:e", "DIR:article-45:1b", unit="indicator")
def orsa_additional_macro_analysis_required_2027(reasoned_supervisory_request: bool,
                                                small_non_complex: bool,
                                                prior_article29d_approval: bool, *,
                                                qualification_reference: str, context: Context):
    """Select only additional paragraph1(e) analysis; paragraph1(d) remains.

    Group-level analysis is not an automatic exemption: the supervisor must
    consider it under paragraph9. Approval/request/classification are external.
    """
    _reference(qualification_reference, "qualification_reference")
    request = _declared_bool(reasoned_supervisory_request, "reasoned_supervisory_request")
    snc = _declared_bool(small_non_complex, "small_non_complex")
    approved = _declared_bool(prior_article29d_approval, "prior_article29d_approval")
    return int(request and not (snc or approved)), {
        "reasoned_supervisory_request": request, "small_non_complex": snc,
        "prior_article29d_approval": approved, "core_macro_analysis_still_required": True,
        "group_analysis_automatic_exemption": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "additional_paragraph1e_analysis_only"}


@calculation("DIR:article-45:5:b", unit="indicator")
def orsa_biennial_captive_conditions_2027(is_captive: bool, permitted_policyholders: bool,
                                         natural_person_tp_share: float, no_compulsory_liability: bool, *,
                                         qualification_reference: str, context: Context):
    """Declared captive eligibility for ORSA frequency, not DR89 simplification.

    Permitted insureds/beneficiaries are group legal persons or natural persons
    eligible under group insurance contracts. Their TP share must be STRICTLY
    below5%. Qualification of persons/contracts and TP allocation is external.
    """
    _reference(qualification_reference, "qualification_reference")
    facts = {name: _declared_bool(value, name) for name, value in (
        ("is_captive", is_captive), ("permitted_policyholders", permitted_policyholders),
        ("no_compulsory_liability", no_compulsory_liability))}
    share = number(natural_person_tp_share, "natural_person_tp_share", 0, 1)
    limit = number(scalar("orsa_captive_natural_person_share_limit", context), "share_limit", 0, 1)
    below = Fraction(str(share)) < Fraction(str(limit))
    return int(all(facts.values()) and below), {
        "conditions": facts, "natural_person_tp_share": share, "strict_share_condition": below,
        "scope": "DIR45_5_captive_frequency_not_DR89_eligibility",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DIR:article-45:5", unit="years")
def orsa_max_assessment_interval_2027(small_non_complex: bool, qualifying_captive: bool, *,
                                     supervisory_interval_years: float | None = None,
                                     non_snc_approval_reference: str | None = None,
                                     qualification_reference: str, context: Context):
    """Maximum periodic interval; an event-triggered ORSA remains immediate.

    The reference must cover classifications AND supervisory directions.
    None declares no additional shorter supervisory interval, not ignorance.
    No calendar deadline, timely completion or supervisory approval is inferred.
    A separate29d/327e non-SNC approval can enable the reduced maximum;
    classification remains false and the approval is not inferred from size.
    """
    _reference(qualification_reference, "qualification_reference")
    snc = _declared_bool(small_non_complex, "small_non_complex")
    captive = _declared_bool(qualifying_captive, "qualifying_captive")
    approved_non_snc = non_snc_approval_reference is not None
    if approved_non_snc:
        _reference(non_snc_approval_reference, "non_snc_approval_reference")
        require(not snc and not captive, "non_snc_approval_reference", "separate Article29d/327e approved route, not duplicate SNC/captive route")
    key = "orsa_reduced_max_interval" if snc or captive or approved_non_snc else "orsa_default_max_interval"
    maximum = number(scalar(key, context), "maximum_interval", 0)
    require(maximum > 0, "maximum_interval", "positive maximum required", "REVIEW_REQUIRED")
    interval = maximum
    if supervisory_interval_years is not None:
        interval = number(supervisory_interval_years, "supervisory_interval_years", 0, maximum)
        require(interval > 0, "supervisory_interval_years", "strictly positive interval required")
    return interval, {
        "statutory_maximum_years": maximum, "supervisory_interval_years": supervisory_interval_years,
        "small_non_complex": snc, "qualifying_captive": captive,
        "non_snc_approval_reference": non_snc_approval_reference,
        "immediate_after_material_change": True, "ongoing_risk_management_required": True,
        "timely_completion_verified": False, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "_sources": ["DIR:article-29d", "DR:article-327e"] if approved_non_snc else []}


@calculation("DIR:article-45a:1-2", "DIR:article-45a:5", unit="count")
def orsa_climate_scenario_requirement_2027(material_climate_risk: bool, small_non_complex: bool, *,
                                          qualification_reference: str, context: Context):
    """Minimum scenario count from externally qualified materiality/SNC status.

    Zero exempts no undertaking from the paragraph1 materiality assessment.
    This is a requirement selector, not a finding that scenarios exist.
    """
    _reference(qualification_reference, "qualification_reference")
    material = _declared_bool(material_climate_risk, "material_climate_risk")
    snc = _declared_bool(small_non_complex, "small_non_complex")
    minimum = number(scalar("orsa_climate_minimum_scenarios", context), "minimum_scenarios", 1)
    require(minimum.is_integer(), "minimum_scenarios", "integer scenario count required", "REVIEW_REQUIRED")
    required = material and not snc
    return int(minimum) if required else 0, {
        "scenario_requirements_apply": required, "material_climate_risk": material,
        "small_non_complex": snc, "materiality_assessment_still_required": True,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scenarios_verified": False,
        "reason": "SNC_PARAGRAPHS_2_TO_4_EXEMPTION" if snc else
                  "MATERIAL_CLIMATE_RISK" if material else "NO_DECLARED_MATERIAL_CLIMATE_RISK"}


@calculation("DIR:article-45a:2-4", unit="indicator")
def orsa_climate_scenario_structure_2027(scenarios: Mapping[str, dict],
                                        impact_analysis_interval_years: float,
                                        scenario_review_interval_years: float, *,
                                        assessment_reference: str, context: Context):
    """Check required role metadata and maximum intervals, never model adequacy.

    'Significantly above' has no invented numeric cutoff: both >2 degrees and
    an explicit external qualification are required. Additional scenarios can
    remain in the external assessment; this input describes the two roles.
    Intervals are declared years, not dates or an automatic scheduling service.
    """
    _reference(assessment_reference, "assessment_reference")
    low, high = "below_two_degrees", "significantly_above_two_degrees"
    exact_keys(scenarios, (low, high), "scenarios")
    conditions = {}
    boundary = number(scalar("orsa_climate_temperature_boundary", context), "temperature_boundary")
    for role in (low, high):
        keys = ("reference", "temperature_increase_celsius", "long_term")
        if role == high:
            keys += ("significantly_above_qualified",)
        record = scenarios[role]
        exact_keys(record, keys, f"scenarios.{role}")
        _reference(record["reference"], f"scenarios.{role}.reference")
        temperature = number(record["temperature_increase_celsius"], f"scenarios.{role}.temperature")
        long_term = _declared_bool(record["long_term"], f"scenarios.{role}.long_term")
        qualified = True if role == low else _declared_bool(
            record["significantly_above_qualified"], f"scenarios.{role}.significantly_above_qualified")
        conditions[role] = long_term and qualified and (temperature < boundary if role == low else temperature > boundary)
    for label, value, parameter in (
        ("impact_analysis_interval", impact_analysis_interval_years, "orsa_climate_max_analysis_interval"),
        ("scenario_review_interval", scenario_review_interval_years, "orsa_climate_max_review_interval"),
    ):
        interval = number(value, label, 0)
        require(interval > 0, label, "strictly positive interval required")
        maximum = number(scalar(parameter, context), parameter, 0)
        conditions[label] = interval <= maximum
    return int(all(conditions.values())), {
        "conditions": conditions, "scenarios": {key: dict(record) for key, record in scenarios.items()},
        "impact_analysis_interval_years": impact_analysis_interval_years,
        "scenario_review_interval_years": scenario_review_interval_years,
        "assessment_reference": assessment_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "scenario_roles_and_maximum_intervals_only",
        "proportionate_shorter_intervals_assessed": False, "scenario_content_verified": False,
        "instrument_effectiveness_assessed": False, "necessary_updates_assessed": False}


@calculation("ORSA_GUIDANCE:guidelines-1-20", unit="indicator")
def orsa_guidance_evidence_check(evidence: Mapping[str, dict], conditions: Mapping[str, bool], *,
                                  qualification_reference: str, assessment_reference: str, context: Context):
    """Inventory archived guideline evidence, not content or legal applicability.

    Group/entity applicability and conditional needs are externally qualified.
    Incompatible scope flags are rejected. The future table explicitly excludes
    archived blanket annual frequency. Future frequency and expanded group scope
    are handled by separate APIs, not approved by this inventory.
    """
    _reference(qualification_reference, "qualification_reference")
    keys = ("group", "stress_analysis_needed", "different_valuation_basis", "single_document",
            "translation_requested", "application_translations_needed", "third_country_business")
    exact_keys(conditions, keys, "conditions")
    facts = {key: _declared_bool(conditions[key], f"conditions.{key}") for key in keys}
    for child, parent in (("single_document", "group"), ("third_country_business", "group"),
                          ("translation_requested", "single_document"),
                          ("application_translations_needed", "single_document")):
        require(not facts[child] or facts[parent], child, f"{parent} required by this conditional scope")
    table = effective_resource("profile.json", context)["tables"]["orsa_guidance_controls"]
    rows = [row[:3] for row in table["rows"] if row[3] == "always" or facts[row[3]]]
    value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    return value, {**details, "conditions": facts, "qualification_reference": qualification_reference,
        "scope": "archived_guideline_evidence_inventory_only",
        "guideline_legal_applicability": "PENDING", "substantive_ORSA_verified": False,
        "excluded_topics": table.get("excluded_topics", []),
        "additional_required_scope_api": table.get("additional_required_scope_api")}
