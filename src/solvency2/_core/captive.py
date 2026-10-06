"""DR89/90 captive components; qualifications remain external evidence."""
import math
from typing import Mapping

from .core import Context, calculation, number, require, scalar


def _reference(value, name):
    require(isinstance(value, str) and bool(value.strip()), name,
            "external qualification reference required", "MISSING_INPUT")


@calculation("DR:article-89", unit="indicator")
def captive_simplification_conditions(conditions: Mapping[str, bool], *,
                                      qualification_reference: str, context: Context):
    """Check externally assessed DR89 facts, not substantive eligibility itself.

    Absent insurance/reinsurance business must be explicitly qualified by the
    caller; missing evidence never means that a condition is met.
    """
    _reference(qualification_reference, "qualification_reference")
    keys = {"captive_under_article13", "article88_satisfied", "insurance_group_only",
            "underlying_reinsurance_group_only", "no_compulsory_liability"}
    require(isinstance(conditions, Mapping), "conditions", "condition mapping required")
    require(not set(conditions) - keys, "conditions", "unknown condition")
    require(keys <= set(conditions), "conditions", "all conditions required", "MISSING_INPUT")
    for key in sorted(keys):
        require(conditions[key] is not None, key, "qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")
    return int(all(conditions.values())), {"conditions": dict(conditions),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "DR89_condition_screen_not_general_simplification_approval"}


@calculation("DR:article-90:2", "DR:article-116:3", "DR:article-116:6")
def captive_nonlife_segment(premium_volume: float, reserve_volume: float, *,
                            eligibility_reference: str, volume_reference: str, context: Context):
    """Calculate a segment charge from already qualified Article116 volumes.

    Normalising before squaring avoids overflow for representable charges;
    neither reinsurance adjustments nor geographic diversification are repeated.
    """
    _reference(eligibility_reference, "eligibility_reference")
    _reference(volume_reference, "volume_reference")
    premium = number(premium_volume, "premium_volume", 0)
    reserve = number(reserve_volume, "reserve_volume", 0)
    factor = number(scalar("captive_nonlife_factor", context), "captive_nonlife_factor", 0)
    scale = max(premium, reserve)
    p, r = (premium / scale, reserve / scale) if scale else (0, 0)
    value = (factor * math.sqrt(p * p + p * r + r * r)) * scale
    require(math.isfinite(value), "segment_charge", "charge not representable", "REVIEW_REQUIRED")
    return value, {"premium_volume": premium, "reserve_volume": reserve, "factor": factor,
        "eligibility_reference": eligibility_reference, "volume_reference": volume_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "DR90_segment_only"}


@calculation("DR:article-90:1", "DR:annex-II")
def captive_nonlife_aggregation(segment_charges: Mapping[str, float], *,
                                eligibility_reference: str, context: Context):
    """Aggregate all twelve DR90 segment charges, with explicit inactive zeros.

    Weights are separate profile parameters, not ordinary nonlife correlations.
    A full set prevents omitted exposures from silently becoming zero.
    """
    _reference(eligibility_reference, "eligibility_reference")
    keys = {str(i) for i in range(1, 13)}
    require(isinstance(segment_charges, Mapping), "segment_charges", "segment mapping required")
    require(not set(segment_charges) - keys, "segment_charges", "unknown AnnexII segment")
    require(keys <= set(segment_charges), "segment_charges", "all twelve segments required", "MISSING_INPUT")
    charges = {str(i): number(segment_charges[str(i)], f"segment_charges.{i}", 0) for i in range(1, 13)}
    diagonal = number(scalar("captive_nonlife_diagonal_weight", context), "captive_nonlife_diagonal_weight", 0)
    summed = number(scalar("captive_nonlife_sum_weight", context), "captive_nonlife_sum_weight", 0)
    scale = max(charges.values())
    normal = [v / scale for v in charges.values()] if scale else [0.0] * 12
    value = math.sqrt(diagonal * math.fsum(v * v for v in normal)
                      + summed * math.fsum(normal) ** 2) * scale
    require(math.isfinite(value), "aggregate_charge", "charge not representable", "REVIEW_REQUIRED")
    return value, {"segment_charges": charges, "diagonal_weight": diagonal, "sum_weight": summed,
        "eligibility_reference": eligibility_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "DR90_nonlife_premium_reserve_only"}
