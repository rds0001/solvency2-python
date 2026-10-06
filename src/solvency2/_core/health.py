"""Health-specific parameter arithmetic; external HRES determinations stay external."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _reference


def _hres_qualification(evidence, supplied, lower, upper):
    """Check declared Article149 prerequisites, never authenticate an official act.

    This route concerns the implementing-act parameter, not an approved USP
    substitution. The latter uses the separately qualified effective-sigma path.
    """
    exact_keys(evidence, ("conditions", "assessment_reference", "implementing_act_reference",
                          "methodology_publication_reference"), "qualification")
    for key in ("assessment_reference", "implementing_act_reference", "methodology_publication_reference"):
        _reference(evidence[key], "qualification." + key)
    required = ("segregated_without_transfer", "separate_segment_and_risk_parameters",
                "appropriate_methods", "complete_accurate_appropriate_data",
                "current_credible_information", "residual_and_common_risks_considered",
                "methodology_and_calculation_public", "implementing_act_applicable",
                "parameter_matches_act", "article147_separate_volumes")
    exact_keys(evidence["conditions"], required, "qualification.conditions")
    conditions = {key: _declared_bool(evidence["conditions"][key], "qualification." + key)
                  for key in required}
    require(all(conditions.values()), "qualification.conditions",
            "declared Article149 prerequisites not met", "REVIEW_REQUIRED")
    require(lower <= supplied <= upper, "hres_sigma",
            "declared implementing-act parameter contradicts Article149 arithmetic bounds", "REVIEW_REQUIRED")
    return {**evidence, "conditions": conditions, "official_act_authenticated": False,
            "evidence_content_verified": False, "supervisory_approval_granted": False,
            "usp_substitution_included": False}


def _standard_sigma(segment, risk, context):
    require(segment in ("1", "2", "3"), "segment", "Article 149 standard HRES scope is segments 1–3")
    require(risk in ("premium", "reserve"), "risk", "premium or reserve required")
    rows = effective_resource("profile.json", context)["tables"]["health_segments"]["rows"]
    row = next(row for row in rows if row[0] == segment)
    sigma = number(row[1 if risk == "premium" else 2], "standard_sigma", 0)
    if risk == "premium":
        sigma *= number(scalar("health_nonprop_adjustment", context), "health_nonprop_adjustment", 0)
    return number(sigma, "standard_sigma", 0)


def _bounds(segment, risk, context):
    sigma = _standard_sigma(segment, risk, context)
    fraction = number(scalar("health_hres_floor_fraction", context), "health_hres_floor_fraction", 0, 1)
    return sigma * fraction, sigma


@calculation("DR:article-149:2:b-c", "DR:annex-XIV", unit="ratio")
def health_hres_sigma_bound(segment: str, risk: str, representative_sigma: float, *, context: Context):
    """Bound an external representative estimate; this does not determine an official HRES sigma."""
    estimate = number(representative_sigma, "representative_sigma", 0)
    lower, upper = _bounds(segment, risk, context)
    return min(upper, max(lower, estimate)), {
        "lower_bound": lower, "standard_sigma": upper, "representative_sigma": estimate,
        "parameter_determination": "NOT_ESTABLISHED",
        "scope": "arithmetic_only_not_an_official_hres_parameter"}


@calculation("DR:article-149:3-4", "DR:annex-XIV", unit="ratio")
def health_hres_mixed_sigma(segment: str, risk: str, non_hres_volume: float,
                            hres_volume: float, hres_sigma: float, *,
                            parameter_reference: str, qualification: Mapping | None = None,
                            context: Context):
    """Mix separately calculated volumes; a source reference is not a legal applicability decision.

    Bounds are reported independently instead of silently changing a supplied
    external parameter. Optional qualification additionally rejects declared
    ineligibility or bound contradictions; omission stays explicitly unchecked.
    This component is not the complete HRES risk module.
    """
    lower, standard = _bounds(segment, risk, context)
    outside = number(non_hres_volume, "non_hres_volume", 0)
    inside = number(hres_volume, "hres_volume", 0)
    supplied = number(hres_sigma, "hres_sigma", 0)
    require(isinstance(parameter_reference, str) and bool(parameter_reference.strip()),
            "parameter_reference", "nonempty external parameter reference required", "MISSING_INPUT")
    qualified = (_hres_qualification(qualification, supplied, lower, standard)
                 if qualification is not None else None)
    scale = max(outside, inside)
    require(scale > 0, "volumes", "zero denominator has no defined mixed sigma", "REVIEW_REQUIRED")
    # Common scaling keeps the weighting valid for both tiny and huge monetary units.
    non_hres_share = (outside / scale) / (outside / scale + inside / scale)
    hres_share = (inside / scale) / (outside / scale + inside / scale)
    return standard * non_hres_share + supplied * hres_share, {
        "standard_sigma": standard, "hres_sigma": supplied, "hres_share": hres_share,
        "non_hres_share": non_hres_share, "parameter_reference": parameter_reference,
        "parameter_reference_status": "EXTERNAL_UNVERIFIED",
        "qualification": qualified,
        "qualification_status": "DECLARED_PREREQUISITES_CHECKED" if qualified else "NOT_CHECKED",
        "parameter_bounds_status": "WITHIN_ARITHMETIC_BOUNDS" if lower <= supplied <= standard
        else "REVIEW_REQUIRED", "lower_bound": lower,
        "scope": "arithmetic_only_not_hres_applicability_or_complete_scr",
        "_sources": (["DR:article-149:1", "DR:article-149:2:a-h",
                      "DR:article-149:3" if risk == "premium" else "DR:article-149:4"]
                     if qualified else [])}
