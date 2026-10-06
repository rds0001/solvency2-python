"""Reporting evidence and a narrow captive screen, not blanket reporting waivers."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory, _reference
from ._report_structure import report_structure_check
from .group_reporting import group_reporting_check


@calculation("DIR:article-35:1", "DIR:article-35:3-5", unit="indicator")
def supervisory_reporting_evidence_check(evidence: Mapping[str, dict], *,
                                          assessment_reference: str, scope_reference: str,
                                          report_kind: str = "core",
                                          context: Context,
                                          structure_sections: list[str] | None = None,
                                          structure_reference: str | None = None,
                                          reporting_scope: str = "solo",
                                          group_evidence: Mapping | None = None):
    """Inventory core or full RSR references for a qualified request/period.

    Qualitative/quantitative, temporal and data-source alternatives remain
    alternatives: one reference documents the externally justified selection.
    No file inspection, content certification, board approval or filing occurs.
    """
    _reference(scope_reference, "scope_reference")
    require(isinstance(report_kind, str) and report_kind in ("core", "rsr"),
            "report_kind", "core or rsr required", "UNSUPPORTED_PARAMETER")
    table_name = "rsr_content_controls" if report_kind == "rsr" else "supervisory_reporting_core_controls"
    profile = effective_resource("profile.json", context)
    table = profile["tables"][table_name]
    value, details = _evidence_inventory(evidence, table, assessment_reference)
    structure_ok, structure, structure_sources = report_structure_check(
        profile, report_kind, structure_sections, structure_reference)
    group_ok, group_details, group_sources = group_reporting_check(
        profile, report_kind, reporting_scope, group_evidence, assessment_reference)
    return int(value and structure_ok and group_ok), {**details, "scope_reference": scope_reference, "report_kind": report_kind,
        "reporting_scope": reporting_scope, "group_supplement": group_details,
        "structure": structure, "_sources": details["_sources"] + structure_sources + group_sources,
        "conditional_applicability_verified": False,
        "information_quality_verified": False, "board_approval_verified": False,
        "file_format_or_XBRL_verified": False, "actual_submission_verified": False,
        "all_reporting_requirements_covered": False,
        "scope": ("declared_full_RSR_paragraph_references_only" if report_kind == "rsr"
                  else "declared_core_supervisory_information_inventory_only")}


@calculation("DIR:article-35a:3", unit="indicator")
def reporting_captive_itemised_exemption_2027(is_captive: bool, permitted_policyholders: bool,
                                              natural_person_tp_share: float, no_compulsory_liability: bool,
                                              reporting_interval_years: float, *,
                                              qualification_reference: str, context: Context):
    """Declared Article35a(3) eligibility only for subannual itemised reporting.

    Policyholder/beneficiary scope and underlying reinsurance contracts must
    already be qualified. Neither ORSA eligibility nor a general waiver is inferred.
    """
    _reference(qualification_reference, "qualification_reference")
    facts = {key: _declared_bool(value, key) for key, value in (
        ("is_captive", is_captive), ("permitted_policyholders", permitted_policyholders),
        ("no_compulsory_liability", no_compulsory_liability))}
    share = number(natural_person_tp_share, "natural_person_tp_share", 0, 1)
    interval = number(reporting_interval_years, "reporting_interval_years", 0)
    require(interval > 0, "reporting_interval_years", "strictly positive interval required")
    share_limit = number(scalar("reporting_captive_natural_person_share_limit", context), "share_limit", 0, 1)
    interval_limit = number(scalar("reporting_captive_interval_limit_years", context), "interval_limit", 0)
    require(interval_limit > 0, "interval_limit", "positive interval boundary required", "REVIEW_REQUIRED")
    share_ok = Fraction(str(share)) < Fraction(str(share_limit))
    interval_ok = Fraction(str(interval)) < Fraction(str(interval_limit))
    return int(all(facts.values()) and share_ok and interval_ok), {
        "conditions": facts, "natural_person_tp_share": share, "reporting_interval_years": interval,
        "strict_share_condition": share_ok, "strict_interval_condition": interval_ok,
        "share_limit": share_limit, "interval_limit_years": interval_limit,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "blanket_reporting_waiver": False, "other_reporting_duties_waived": False,
        "scope": "declared_subannual_itemised_reporting_eligibility_only_not_ORSA_or_general_exemption"}
