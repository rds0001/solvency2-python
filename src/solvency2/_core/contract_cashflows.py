"""Obligation-level contract scope connected to existing best-estimate arithmetic."""

import math
from collections.abc import Mapping

from .contracts import (
    contract_boundary_exclusion,
    contract_recognition_due,
    obligation_derecognition_condition,
)
from .core import Context, calculation, effective_resource, exact_keys, require
from .provisions import best_estimate_cashflows


def _reassessment(data, context):
    """Guideline6C decision gates; no materiality threshold or actual reporting."""
    if data is None:
        return {"status": "NOT_ASSESSED"}
    keys = ("scenario_calculation", "trigger", "indication_of_different_conclusion",
            "less_extreme_than_sf_interest_stress", "reassessment_performed",
            "clearly_different_conclusion", "boundary_changed", "material_tp_and_solvency_impact")
    exact_keys(data, keys, "reassessment")
    trigger = data["trigger"]
    require(isinstance(trigger, str) and trigger in {"none", "economic_environment", "contract_terms", "other_environment"},
            "reassessment.trigger", "explicit supported change trigger required")
    for key in ("scenario_calculation", "indication_of_different_conclusion", "reassessment_performed", "boundary_changed"):
        require(isinstance(data[key], bool), key, "explicit externally qualified boolean required", "REVIEW_REQUIRED")
    economic = trigger == "economic_environment"
    less_extreme = data["less_extreme_than_sf_interest_stress"]
    if economic:
        require(isinstance(less_extreme, bool), "less_extreme_than_sf_interest_stress",
                "qualified economic-change comparison required", "REVIEW_REQUIRED")
    else:
        require(less_extreme is None, "less_extreme_than_sf_interest_stress", "omit unused economic comparison")
    performed, changed = data["reassessment_performed"], data["boundary_changed"]
    clear, material = data["clearly_different_conclusion"], data["material_tp_and_solvency_impact"]
    require(isinstance(clear, bool) if performed else clear is None, "clearly_different_conclusion",
            "explicit conclusion only when reassessment performed", "REVIEW_REQUIRED")
    require(isinstance(material, bool) if changed else material is None, "material_tp_and_solvency_impact",
            "explicit materiality only for changed boundaries", "REVIEW_REQUIRED")
    indicated = data["indication_of_different_conclusion"]
    require(trigger != "none" or not indicated, "reassessment.trigger", "indication requires an identified change trigger")
    eligible = indicated and trigger != "none" and not (economic and less_extreme)
    scenario = data["scenario_calculation"]
    if scenario:
        require(not performed and not changed, "scenario_calculation",
                "contract boundaries must not be reassessed for BE/SCR scenarios", "REVIEW_REQUIRED")
    else:
        require(not eligible or performed, "reassessment_performed", "qualified indication requires reassessment", "REVIEW_REQUIRED")
        require(not (economic and less_extreme and performed), "reassessment_performed",
                "economic changes below standard-formula interest stress are not an extreme trigger", "REVIEW_REQUIRED")
        require(not changed or (eligible and performed and clear), "boundary_changed",
                "boundary change requires a qualifying trigger and clearly different conclusion", "REVIEW_REQUIRED")
    notification = changed and material is True
    future = effective_resource("profile.json", context).get("methods", {}).get("risk_margin") == "TIME_ADJUSTED_2027"
    return {"status": "DECLARED_DECISIONS_CHECKED", "inputs": dict(data),
            "base_reassessment_indicated": eligible,
            "immediate_notification_required": notification,
            "annual_reporting_cross_reference_status": (
                "SOURCE_REVIEW_REQUIRED_OLD_DR312_REFERENCE" if notification and future else
                "GUIDELINE6C_DR312_REPORT_INDICATED" if notification else "NOT_TRIGGERED"),
            "notification_sent": False, "qualification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DR:article-17", "DR:article-18:1-6", "CB_GUIDANCE:guideline-0",
             "CB_GUIDANCE:guideline-3", "CB_GUIDANCE:guideline-8")
def best_estimate_contract_cashflows(obligations: Mapping, *, runoff_complete: bool,
                                     cashflow_reference: str, curve_reference: str,
                                     context: Context):
    """Select entire qualified obligations, never truncate by a payment date.

    Every row identifies a disjoint obligation or contract part. Its evidence
    qualifies legal enforceability, unilateral rights, full-risk reflection,
    profile-specific life rules, discernibility and any unbundling. Accepted
    reinsurance is assessed independently of underlying contract boundaries.
    These substantive qualifications remain external, not certified here.

    Article18(5)(c) is cross-checked against the same-version English text;
    the incomplete German source is preserved. Paid premiums, discernible
    cover/guarantee or enforceable future premiums disapply this exception.
    Unbundled parts are independently qualified, not inferred from cash flows.
    """
    require(isinstance(obligations, Mapping) and bool(obligations), "obligations",
            "nonempty, disjoint obligation mapping required", "MISSING_INPUT")
    fields = ("contract_party_date", "coverage_start_date", "obligation_status",
              "related_to_contract", "boundary", "cashflows", "assessment_reference")
    boundary_fields = ("coverage_after_qualifying_right", "premium_payment_enforceable",
                       "related_to_paid_premiums", "discernible_uncertain_event_cover",
                       "discernible_financial_guarantee")
    audit, selected, assessment_sources = {}, [], []
    for label, row in obligations.items():
        require(isinstance(label, str) and bool(label.strip()), "obligation_id", "nonempty obligation identifier required")
        exact_keys(row, (*fields, *(key for key in ("reassessment", "discernibility") if key in row)), label)
        reassessment = _reassessment(row.get("reassessment"), context)
        boundary = row["boundary"]
        exact_keys(boundary, boundary_fields, label + ".boundary")
        for key, flag in {"related_to_contract": row["related_to_contract"], **boundary}.items():
            require(flag is None or isinstance(flag, bool), key, "explicit boolean or None required")
        from .contract_discernibility import assess_discernibility
        boundary, discernibility, sources = assess_discernibility(row.get("discernibility"), boundary)
        assessment_sources.extend(sources)
        evidence = row["assessment_reference"]
        recognition = contract_recognition_due(row["contract_party_date"], row["coverage_start_date"],
                                               evidence_reference=evidence, context=context)
        # The state concerns this obligation, not an expired policy whose
        # incurred claims can still be active. Existing function enforces that
        # distinction and rejects unknown states.
        derecognition = obligation_derecognition_condition(row["obligation_status"],
                                                          evidence_reference=evidence, context=context)
        projected = best_estimate_cashflows(row["cashflows"], runoff_complete=runoff_complete,
                                            cashflow_reference=cashflow_reference,
                                            curve_reference=curve_reference, context=context)
        exclusion = None
        if not recognition.value:
            reason = "INITIAL_RECOGNITION_NOT_DUE"
        elif derecognition.value:
            reason = "SPECIFIC_OBLIGATION_DERECOGNISED"
        else:
            require(row["related_to_contract"] is not None, label + ".related_to_contract",
                    "contract/part relationship unresolved", "REVIEW_REQUIRED")
            if not row["related_to_contract"]:
                reason = "NOT_RELATED_TO_CONTRACT"
            else:
                exclusion = contract_boundary_exclusion(
                    coverage_after_qualifying_right=boundary["coverage_after_qualifying_right"],
                    premium_payment_enforceable=boundary["premium_payment_enforceable"],
                    assessment_reference=evidence, context=context)
                if exclusion.value:
                    reason = "EXCLUDED_BY_ARTICLE_18_3"
                else:
                    # Article18(5) is conjunctive. One known contrary fact
                    # suffices; otherwise every exclusion fact must be known.
                    protected = any(boundary[key] is True for key in (
                        "related_to_paid_premiums", "discernible_uncertain_event_cover",
                        "discernible_financial_guarantee"))
                    if protected:
                        reason = "INCLUDED_18_3_NOT_EXCLUDED_18_5_6_INAPPLICABLE"
                    elif boundary["premium_payment_enforceable"] is True:
                        reason = "INCLUDED_18_5_INAPPLICABLE_ENFORCEABLE_PREMIUM"
                    else:
                        require(all(boundary[key] is False for key in (
                            "related_to_paid_premiums", "discernible_uncertain_event_cover",
                            "discernible_financial_guarantee", "premium_payment_enforceable")),
                            label + ".article18_5_6", "unresolved exception facts", "REVIEW_REQUIRED")
                        reason = "EXCLUDED_BY_ARTICLE_18_5_6"
        included = reason.startswith("INCLUDED_")
        if included:
            selected.append(projected.value)
        audit[label] = {
            "included": included, "selection_reason": reason,
            "recognition": recognition.to_dict(), "derecognition": derecognition.to_dict(),
            "article18_3": None if exclusion is None else exclusion.to_dict(),
            "boundary_assessment": dict(boundary), "unselected_projection": projected.to_dict(),
            "selected_best_estimate": projected.value if included else 0.0,
            "assessment_reference": evidence, "qualification_status": "EXTERNAL_UNVERIFIED",
            "reassessment": reassessment,
            "discernibility": discernibility,
        }
    return math.fsum(selected), {
        "obligations": audit, "selected_obligation_ids": [k for k, v in audit.items() if v["included"]],
        "excluded_obligation_ids": [k for k, v in audit.items() if not v["included"]],
        "payment_date_truncation_applied": False,
        "cashflow_reference": cashflow_reference, "curve_reference": curve_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "qualified_obligation_scope_to_gross_best_estimate_not_complete_legal_boundary_assessment",
        "_sources": ["DR_EN:article-18:5:c", *assessment_sources, *(["CB_GUIDANCE:guideline-6C"]
            if any("reassessment" in row for row in obligations.values()) else [])],
    }
