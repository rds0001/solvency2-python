"""SFCR publication evidence and event consequences, never publication or approval."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .evidence import _declared_bool, _evidence_inventory


def _capital_events(events, periods):
    if events is None:
        return {"status": "NOT_ASSESSED"}, False
    require(isinstance(events, Mapping) and bool(events) and set(events) <= {"mcr", "scr"},
            "capital_events", "explicit mcr/scr event records required")
    limits = {r[0]: number(r[1], r[0], 0) for r in periods}
    require(all(r[2] == "months" for r in periods), "periods", "disclosure thresholds require months", "RESOURCE_INTEGRITY")
    results, update = {}, False
    fields = ("actual_breach_detected", "material_breach", "months_since_detection",
              "realistic_plan_received_in_time", "initially_realistic_plan",
              "unresolved_at_restoration_deadline", "supervisor_deems_plan_impossible")
    for kind, event in events.items():
        exact_keys(event, fields, "capital_events." + kind)
        actual = _declared_bool(event["actual_breach_detected"], kind + ".actual_breach_detected")
        relevant = actual and (kind == "mcr" or _declared_bool(event["material_breach"], kind + ".material_breach"))
        demand, period_end = False, False
        if relevant:
            elapsed = number(event["months_since_detection"], kind + ".months_since_detection", 0)
            missing_plan_limit = limits[kind + "_missing_realistic_plan"]
            restoration_limit = limits[kind + "_unresolved_after_realistic_plan"]
            impossible = kind == "mcr" and _declared_bool(event["supervisor_deems_plan_impossible"], kind + ".supervisor_deems_plan_impossible")
            demand = impossible or (elapsed >= missing_plan_limit and not _declared_bool(
                event["realistic_plan_received_in_time"], kind + ".realistic_plan_received_in_time"))
            if elapsed >= restoration_limit:
                period_end = _declared_bool(event["initially_realistic_plan"], kind + ".initially_realistic_plan") and _declared_bool(
                    event["unresolved_at_restoration_deadline"], kind + ".unresolved_at_restoration_deadline")
        results[kind] = {"input": dict(event), "relevant_actual_breach": relevant,
            "supervisory_demand_for_immediate_disclosure_required": demand,
            "disclosure_at_restoration_period_end_required": period_end,
            "supervisory_demand_actually_issued_verified": False,
            "historical_disclosure_performed_verified": False}
        update = update or demand or period_end
    return {"events": results, "unassessed_event_types": sorted({"mcr", "scr"} - set(events)),
            "periods": periods, "calendar_dates_computed": False,
            "private_recovery_period_extensions_imported": False}, update


def _publication_facts(facts, profile):
    if facts is None:
        return {"status": "NOT_ASSESSED"}, True, False
    names = ("own_website_maintained", "association_website_qualified", "withholding_used",
             "withholding_permission", "withholding_ground_persists", "protected_information_withheld",
             "withholding_ground_ceased", "equivalent_publication_used", "equivalent_publication_permission",
             "material_development")
    exact_keys(facts, names, "publication_facts")
    flags = {key: _declared_bool(value, key) for key, value in facts.items()}
    require(not flags["protected_information_withheld"] or flags["withholding_used"],
            "publication_facts", "withheld protected information contradicts no withholding", "REVIEW_REQUIRED")
    require(not (flags["withholding_ground_ceased"] and flags["withholding_ground_persists"]),
            "publication_facts", "same permission ground cannot both persist and have ceased", "REVIEW_REQUIRED")
    channel = ("own_website" if flags["own_website_maintained"] else
               "association_website" if flags["association_website_qualified"] else "electronic_on_request")
    permitted = flags["withholding_permission"] and flags["withholding_ground_persists"] and not flags["protected_information_withheld"]
    violations = []
    if flags["withholding_used"] and not permitted:
        violations.append("WITHHOLDING_NOT_PERMITTED")
    if flags["equivalent_publication_used"] and not flags["equivalent_publication_permission"]:
        violations.append("EQUIVALENT_PUBLICATION_NOT_PERMITTED")
    rows = profile["tables"]["sfcr_publication_controls"]["rows"]
    return {"input": flags, "required_channel": channel, "withholding_permitted": permitted,
            "notify_supervisor_of_ceased_ground": flags["withholding_ground_ceased"],
            "withholding_reasons_disclosure_required": flags["withholding_used"],
            "protected_information_scope": next(r[2] for r in rows if r[0] == "protected_information"),
            "known_policy_violations": violations,
            "website_retention_required": channel != "electronic_on_request",
            "paper_request_duty_in_profile": any(r[0] == "paper_request" for r in rows),
            "simultaneous_supervisory_submission_required": True,
            "actual_publication_verified": False}, not violations, flags["material_development"]


@calculation("DIR:articles-53-55", "DR:articles-299-303", unit="indicator")
def sfcr_publication_evidence_check(evidence: Mapping, *, assessment_reference: str,
                                    context: Context, publication_facts: Mapping | None = None,
                                    capital_events: Mapping | None = None):
    """Join versioned duty references and qualified event facts, not legal sign-off.

    Every control needs evidence, including reasoned non-applicability when
    conditional. AVAILABLE merely records a reference. Elapsed months and
    historical deadline facts are externally qualified; no calendar guess.
    Missing optional screenings remain NOT_ASSESSED, never implicitly passed.
    """
    profile = effective_resource("profile.json", context)
    table = profile["tables"]["sfcr_publication_controls"]
    value, details = _evidence_inventory(evidence, table, assessment_reference)
    publication, permitted, material = _publication_facts(publication_facts, profile)
    periods = profile["tables"]["sfcr_publication_breach_periods"]["rows"]
    capital, capital_update = _capital_events(capital_events, periods)
    return int(value and permitted), {**details, "publication": publication, "capital_events": capital,
        "public_report_update_indicated": material or capital_update,
        "update_trigger_assessment_complete": publication_facts is not None and capital_events is not None and set(capital_events) == {"mcr", "scr"},
        "publication_periods": profile["tables"]["sfcr_periods"]["rows"],
        "source_issue_controls": [r[0] for r in table["rows"] if r[0] == "update_supplement_unresolved"],
        "all_publication_duties_fulfilled": False, "publication_performed": False,
        "supervisory_notification_sent": False, "report_content_or_board_approval_verified": False,
        "scope": "evidence_inventory_and_declared_event_screening_not_publication_certification",
        "_sources": [*details["_sources"], *(r[3] for r in periods)]}
