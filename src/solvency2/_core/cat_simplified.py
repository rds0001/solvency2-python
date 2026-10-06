"""Prescribed catastrophe simplifications, not geographic or contract models."""
from typing import Mapping

from .aggregation import catastrophe_weighted_sum
from .core import Context, calculation, exact_keys, number, require, scalar
from .evidence import _reference


@calculation("DR:article-90b", "DR:article-88")
def catastrophe_group_weighted_sum(peril: str, region: str, zone_ordinals: list[int],
                                   insured_sum: float, *, qualification_reference: str,
                                   exposure_basis_reference: str | None = None, context: Context):
    """Q*max(group zone weights)*qualified group SI; never invent a group matrix.

    The named region fixes the common regional scope. Source-blocked weights
    remain blocked through the ordinary selector. A group amount cannot be
    repeated into every original matrix zone: downstream group treatment must
    be qualified separately. Future90b(6) requires120(1a) evidence for wind/soil.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(zone_ordinals, (list, tuple)) and bool(zone_ordinals),
            "zone_ordinals", "explicit nonempty group membership required", "MISSING_INPUT")
    require(all(isinstance(z, int) and not isinstance(z, bool) and z > 0 for z in zone_ordinals),
            "zone_ordinals", "positive integer ordinals required")
    require(len(set(zone_ordinals)) == len(zone_ordinals), "zone_ordinals", "duplicate zone")
    future_basis = context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1" and peril in ("windstorm", "subsidence")
    if future_basis:
        _reference(exposure_basis_reference, "exposure_basis_reference")
    else:
        require(exposure_basis_reference is None, "exposure_basis_reference", "unused future exposure-basis reference")
    results = [catastrophe_weighted_sum(peril, region, z, insured_sum, context=context) for z in zone_ordinals]
    selected = max(results, key=lambda r: r.details["zone_weight"])
    return selected.value, {"peril": peril, "region": region, "zone_ordinals": list(zone_ordinals),
        "maximum_zone_weight": selected.details["zone_weight"], "regional_factor": selected.details["regional_factor"],
        "qualification_reference": qualification_reference, "exposure_basis_reference": exposure_basis_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "group_correlation_or_geography_inferred": False,
        "scope": "one_group_weighted_sum_not_complete_catastrophe_aggregation",
        "_sources": list(selected.sources) + (["DR:article-120:1a"] if future_basis else [])}


@calculation("DR:article-90c", "DR:article-88")
def simplified_fire_risk(exposures: Mapping, average_residential_sum: float,
                         residential_market_shares: Mapping, *,
                         qualification_reference: str, context: Context):
    """Maximum of qualified top-five building-neighbourhood exposures and theta.

    Each category explicitly supplies five ranked centre-neighbourhood sums;
    nonexistent centres are qualified zero entries. Actual building geometry,
    full/partial200m intersection, LoBs7/19, ranking by building-specific net
    insured sum and recoveries not contingent on unrelated claims are external.
    No point-distance proxy and no second deduction of reinsurance are used.
    """
    _reference(qualification_reference, "qualification_reference")
    exact_keys(exposures, ("industrial", "commercial", "residential"), "exposures")
    count = number(scalar("simplified_fire_centres", context), "centre_count", 1)
    require(count.is_integer(), "centre_count", "integer count required")
    maxima = {}
    for category, amounts in exposures.items():
        require(isinstance(amounts, (list, tuple)) and len(amounts) == count,
                category, "one value per prescribed ranked centre; qualified zeros for absent centres")
        maxima[category] = max(number(v, category, 0) for v in amounts)
    average = number(average_residential_sum, "average_residential_sum", 0)
    require(isinstance(residential_market_shares, Mapping), "residential_market_shares", "explicit country shares required")
    require(all(isinstance(k, str) and k.strip() for k in residential_market_shares), "residential_market_shares", "country IDs required")
    require(bool(residential_market_shares) or (average == 0 and maxima["residential"] == 0),
            "residential_market_shares", "all residential business countries required", "MISSING_INPUT")
    shares = [number(v, "market_share", 0, 1) for v in residential_market_shares.values()]
    floor = number(scalar("simplified_fire_market_share_floor", context), "share_floor", 0, 1)
    multiplier = number(scalar("simplified_fire_residential_multiplier", context), "multiplier", 0)
    theta = average * multiplier * max(floor, max(shares, default=0))
    return max(*maxima.values(), theta), {"category_neighbourhood_maxima": maxima,
        "residential_market_share_amount": theta, "ranked_centres_per_category": int(count),
        "qualified_radius_metres": scalar("fire_concentration_radius", context),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "geography_or_reinsurance_valued": False, "scope": "article90c_simplified_fire_capital_only"}
