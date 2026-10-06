"""SFCR paragraph-reference inventory, not content production or certification."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from ._report_structure import report_structure_check
from .group_reporting import group_reporting_check
from .evidence import _declared_bool, _evidence_inventory, _reference


def _de_materiality(assessment, context):
    """Optional archived BaFin57/58 arithmetic, never automatic national scope.

    The caller qualifies use of the November2025 text at the report date.
    Endpoints must be the change established FOR the period, not an invented
    maximum intraperiod swing. Lesser material changes remain reportable.
    """
    if assessment is None:
        return {"status": "NOT_ASSESSED"}, []
    fields = ("source_version", "applicability_reference", "scr_start", "scr_end",
              "mcr_start", "mcr_end", "scr_coverage_ratio", "smaller_scr_change_material",
              "smaller_mcr_change_material", "other_scr_breach_material")
    exact_keys(assessment, fields, "de_materiality")
    require(assessment["source_version"] == "2025-11", "de_materiality.source_version",
            "explicit archived November2025 BaFin source required", "UNSUPPORTED_RULESET")
    _reference(assessment["applicability_reference"], "de_materiality.applicability_reference")
    flags = {key: _declared_bool(assessment[key], "de_materiality." + key) for key in fields[-3:]}
    changes = {}
    for kind in ("scr", "mcr"):
        start = number(assessment[kind + "_start"], kind + "_start", 0)
        end = number(assessment[kind + "_end"], kind + "_end", 0)
        require(start > 0, kind + "_start", "zero initial requirement needs separate materiality assessment", "REVIEW_REQUIRED")
        limit = number(scalar("de_sfcr_" + kind + "_change_threshold", context), kind + "_change_threshold", 0, 1)
        relative = abs(Fraction(str(end)) - Fraction(str(start))) / Fraction(str(start))
        automatic = relative >= Fraction(str(limit))
        changes[kind] = {"start": start, "end": end, "absolute_relative_change": float(relative),
                         "threshold": limit, "numeric_threshold_reached": automatic,
                         "disclosure_indicated": automatic or flags["smaller_" + kind + "_change_material"]}
    ratio = number(assessment["scr_coverage_ratio"], "scr_coverage_ratio")
    breach_limit = number(scalar("de_sfcr_material_scr_breach_ratio", context), "material_scr_breach_ratio", 0, 1)
    require(not flags["other_scr_breach_material"] or ratio < 1, "other_scr_breach_material",
            "material actual SCR breach contradicts full coverage", "REVIEW_REQUIRED")
    material_breach = ratio < 1 and (ratio <= breach_limit or flags["other_scr_breach_material"])
    return {"status": "ARCHIVED_NUMERIC_COMPONENT_ONLY", "source_version": "2025-11",
            "applicability_reference": assessment["applicability_reference"], "changes": changes,
            "scr_coverage_ratio": ratio, "material_scr_breach_ratio": breach_limit,
            "material_scr_breach_disclosure_indicated": material_breach,
            "breach_period_ends_at": "full_scr_compliance_not_merely_above_materiality_threshold",
            "external_materiality_flags": flags, "national_applicability_verified": False,
            "report_contents_verified": False}, ["DE_BAFIN_REPORTING:2025-11:5.1.2.6:57-58"]


@calculation("DR:article-290", "DR:article-291", "DR:article-292-298a", unit="indicator")
def sfcr_content_evidence_check(evidence: Mapping[str, dict], *, report_part: str,
                                full_narrative_scope: bool, assessment_reference: str,
                                scope_reference: str, context: Context,
                                structure_sections: list[str] | None = None,
                                structure_reference: str | None = None,
                                de_materiality: Mapping | None = None,
                                reporting_scope: str = "solo",
                                group_evidence: Mapping | None = None):
    """Inventory references for an externally qualified full narrative part.

    A conditional paragraph needs either its content evidence or a qualified
    non-applicability assessment, never an unqualified silent omission.
    References are not retrieved or assessed. Quantitative-only relief reports
    require a different perimeter and are deliberately not certified here.
    """
    _reference(scope_reference, "scope_reference")
    full = _declared_bool(full_narrative_scope, "full_narrative_scope")
    require(full, "full_narrative_scope", "only qualified full narrative parts supported",
            "UNSUPPORTED_PARAMETER")
    national, national_sources = _de_materiality(de_materiality, context)
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["sfcr_content_controls"]["rows"]
    parts = {r[3] for r in rows}
    require(isinstance(report_part, str) and report_part in parts, "report_part",
            "explicit part supported by this profile required", "UNSUPPORTED_PARAMETER")
    require(reporting_scope == "solo" or report_part != "sfcr_policyholder", "report_part",
            "group part is professional-only; subsidiary policyholder parts require separate solo checks", "UNSUPPORTED_PARAMETER")
    selected = [r[:3] for r in rows if r[3] == report_part]
    value, details = _evidence_inventory(evidence, {"rows": selected}, assessment_reference)
    structure_ok, structure, structure_sources = report_structure_check(
        profile, report_part, structure_sections, structure_reference)
    group_ok, group_details, group_sources = group_reporting_check(
        profile, "sfcr", reporting_scope, group_evidence, assessment_reference)
    return int(value and structure_ok and group_ok), {**details, "report_part": report_part, "structure": structure,
        "reporting_scope": reporting_scope, "group_supplement": group_details,
        "de_materiality": national,
        "full_narrative_scope": full, "scope_reference": scope_reference,
        "conditional_applicability_verified": False, "numerical_content_verified": False,
        "page_count_verified": False, "prescribed_text_verified_in_report": False,
        "board_approval_verified": False, "actual_publication_verified": False,
        "quantitative_templates_verified": False, "all_reporting_requirements_covered": False,
        "scope": "declared_full_narrative_paragraph_references_only",
        "_sources": details["_sources"] + structure_sources + national_sources + group_sources + [context.profile_id + ":"
                    + profile["sources"]["DR"]["sha256"] + ":sfcr-content"],
    }
