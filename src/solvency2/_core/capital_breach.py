"""Declared capital-breach obligations, not recovery forecasts or supervisory action."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory, _reference


@calculation("DIR:article-138:1-3", "DIR:article-139:1-2", unit="indicator")
def capital_breach_requirements(capital_requirement: str, actual_breach: bool,
                               breach_risk_within_horizon: bool, *,
                               qualification_reference: str,
                               deterioration: Mapping | None = None,
                               consolidated_own_funds: float | None = None,
                               consolidated_scr: float | None = None,
                               transition_measures: list[str] | None = None,
                               transition_plan_active: bool | None = None, context: Context):
    """Select notification/plan duties using externally established breach facts.

    Future MCR plans also respond to prospective breach; historical MCR and
    SCR plans here respond to actual breach. No grace period for notification,
    calendar deadline, automatic extension, filing or approval is produced.
    Optional Article136 evidence adds its independent notification trigger;
    absence is not evidence that financial deterioration has been ruled out.
    Combined-group minimum breaches use233a(6) only in the2027 profile;
    SCR own funds never substitute for minimum-eligible basic own funds.
    """
    require(capital_requirement in ("scr", "mcr", "combined_group_minimum", "transition_without_measures"), "capital_requirement",
            "explicit supported capital requirement required", "UNSUPPORTED_PARAMETER")
    _reference(qualification_reference, "qualification_reference")
    actual = _declared_bool(actual_breach, "actual_breach")
    risk = _declared_bool(breach_risk_within_horizon, "breach_risk_within_horizon")
    profile = effective_resource("profile.json", context)
    if capital_requirement == "transition_without_measures":
        require(deterioration is None and consolidated_own_funds is None and consolidated_scr is None,
                "capital_requirement", "Article308e route is separate from136/group-minimum assessment")
        allowed = {"risk_free", "technical_provisions"}
        if context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1":
            allowed |= {"extrapolation", "interest_risk"}
        require(isinstance(transition_measures, (list, tuple)) and bool(transition_measures),
                "transition_measures", "explicit measures in use required", "MISSING_INPUT")
        require(all(isinstance(x, str) and x in allowed for x in transition_measures),
                "transition_measures", "unsupported transition in this profile", "UNSUPPORTED_METHOD")
        require(len(set(transition_measures)) == len(transition_measures), "transition_measures", "duplicate measure")
        require(not {"risk_free", "technical_provisions"}.issubset(transition_measures),
                "transition_measures", "308c and308d are mutually exclusive", "UNSUPPORTED_METHOD")
        active = _declared_bool(transition_plan_active, "transition_plan_active")
        notification = actual or risk
        return int(notification), {
            "capital_requirement": capital_requirement, "selected_duties_article": "308e",
            "transition_measures": list(transition_measures), "transition_plan_active": active,
            "actual_breach_without_measures": actual, "prospective_breach_without_measures": risk,
            "immediate_notification_required": notification, "notification_horizon_months": None,
            "plan_required": actual or active,
            "plan_submission_months": scalar("ltg_transition_plan_months", context) if actual else None,
            "progress_report_interval_months": scalar("ltg_transition_progress_months", context) if actual or active else None,
            "restoration_months_before_any_extension": None,
            "restoration_target": "end_of_applicable_transition_period",
            "unrealistic_restoration_requires_supervisory_withdrawal": True,
            "approval_withdrawn_by_engine": False, "qualification_reference": qualification_reference,
            "qualification_status": "EXTERNAL_UNVERIFIED",
            "scope": "declared_article308e_without_transition_duties_not_recovery_forecast",
            "_sources": ["DIR:article-308e"]}
    require(transition_measures is None and transition_plan_active is None, "transition_measures",
            "transition arguments unused outside Article308e route")
    group_minimum = capital_requirement == "combined_group_minimum"
    group_audit = None
    effective_requirement = capital_requirement
    if group_minimum:
        require(profile.get("methods", {}).get("group_rules") == "2027", "capital_requirement",
                "combined group minimum route requires2027 group rules", "UNSUPPORTED_METHOD")
        own_funds = number(consolidated_own_funds, "consolidated_own_funds")
        scr = number(consolidated_scr, "consolidated_scr", 0)
        special = actual and own_funds > scr
        effective_requirement = "scr" if special else "mcr"
        group_audit = {"consolidated_own_funds": own_funds, "consolidated_scr": scr,
            "article233a6_special_recovery_route": special,
            "minimum_basic_own_funds_coverage_externally_qualified": True,
            "minimum_coverage_inferred_from_scr_own_funds": False}
    else:
        require(consolidated_own_funds is None and consolidated_scr is None,
                "consolidated_own_funds", "group amounts unused for standalone scr/mcr route")
    table = profile["tables"]["capital_breach_periods"]
    trigger = table["mcr_plan_trigger"]
    require(trigger in ("actual", "actual_or_risk"), "mcr_plan_trigger",
            "unknown regulatory trigger", "REVIEW_REQUIRED")
    rows = {row[0]: row[1:] for row in table["rows"]}

    def months(key):
        value, unit, _source = rows[effective_requirement + "_" + key]
        require(unit == "months", key, "month parameter required", "REVIEW_REQUIRED")
        value = number(value, key, 0)
        require(value > 0, key, "positive duration required", "REVIEW_REQUIRED")
        return value

    horizon = months("notification_horizon")
    capital_notification = actual or risk
    deterioration_audit = None
    if deterioration is not None:
        exact_keys(deterioration, ("detected", "assessment_reference",
                                  "detection_procedure_reference"), "deterioration")
        detected = _declared_bool(deterioration["detected"], "deterioration.detected")
        for key in ("assessment_reference", "detection_procedure_reference"):
            _reference(deterioration[key], "deterioration." + key)
        deterioration_audit = {**deterioration, "detected": detected,
                               "procedure_effectiveness_verified": False}
    notification = capital_notification or (
        deterioration_audit is not None and deterioration_audit["detected"])
    plan = actual or (effective_requirement == "mcr" and trigger == "actual_or_risk" and risk)
    article = "138" if effective_requirement == "scr" else "139"
    return int(notification), {
        "capital_requirement": capital_requirement,
        "selected_duties_article": article,
        "combined_group_minimum": group_audit,
        "actual_breach": actual, "breach_risk_within_horizon": risk,
        "notification_horizon_months": horizon,
        "immediate_notification_required": notification,
        "capital_breach_notification_required": capital_notification,
        "deterioration": deterioration_audit,
        "article136_assessment_status": "EXTERNAL_UNVERIFIED" if deterioration_audit else "NOT_CHECKED",
        "plan_required": plan,
        "plan_submission_months": months("plan_submission") if plan else None,
        "restoration_months_before_any_extension": months("restoration") if plan else None,
        "period_origin": "qualified_detection" if plan else None,
        "supervisory_extension_applied": False, "calendar_deadline_calculated": False,
        "actual_submission_verified": False, "plan_approval_verified": False,
        "article136_deterioration_duty_waived": False,
        "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": ("declared_136_138_139_notification_and_base_plan_periods_only" if deterioration_audit
                  else "declared_138_139_notification_and_base_plan_periods_only"),
        "_sources": ["DIR:article-" + article + ":1", "DIR:article-" + article + ":2"]
                    + (["DIR:article-138:3"] if effective_requirement == "scr" and plan else [])
                    + (["DIR:article-233a:6"] if group_minimum else [])
                    + (["DIR:article-136"] if deterioration_audit else []),
    }


@calculation("DIR:article-142:1:a-e", unit="indicator")
def capital_recovery_plan_evidence_check(evidence: Mapping[str, dict], *, plan_kind: str,
                                         assessment_reference: str, scope_reference: str,
                                         context: Context):
    """Inventory the five common plan contents; do not project or approve them."""
    require(plan_kind in ("scr_recovery", "mcr_financing"), "plan_kind",
            "explicit scr_recovery or mcr_financing required", "UNSUPPORTED_PARAMETER")
    _reference(scope_reference, "scope_reference")
    table = effective_resource("profile.json", context)["tables"]["capital_recovery_plan_controls"]
    value, details = _evidence_inventory(evidence, table, assessment_reference)
    return value, {**details, "plan_kind": plan_kind, "scope_reference": scope_reference,
        "forecasts_verified": False, "plan_approval_verified": False,
        "actual_submission_verified": False, "all_article143_detail_rules_covered": False,
        "scope": "article142_common_plan_content_inventory_only"}
