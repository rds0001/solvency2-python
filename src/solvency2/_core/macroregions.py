"""Literal AnnexIII territory catalogue, not an automatic legal risk-location model."""
from .core import Context, calculation, effective_resource, require
from .loss_given_default import _reference


@calculation("DR:annex-III:8", unit="region_ordinal")
def premium_reserve_geographic_region(territory: str, *, risk_location_reference: str, context: Context):
    """Return the macroregion for an explicitly qualified original territory name.

    No translations/current-name aliases or sovereign-to-overseas shortcuts are
    inferred. For a parent country, its printed exclusions must already have
    been excluded from the caller's risk-location input; they remain in audit.
    This lookup neither identifies a NatCat zone nor calculates regional volumes.
    """
    _reference(risk_location_reference, "risk_location_reference")
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["premium_reserve_territories"]["rows"]
    require(isinstance(territory, str), "territory", "exact original territory name required",
            "UNSUPPORTED_PARAMETER")
    found = [row for row in rows if row[0] == territory]
    require(bool(found), "territory", "territory not explicitly listed; no inferred alias or aggregate mapping",
            "UNSUPPORTED_PARAMETER")
    require(len(found) == 1, "territory", "ambiguous catalogue assignment", "REVIEW_REQUIRED")
    _, region, exclusions = found[0]
    require(region in {str(i) for i in range(1, 19)}, "region", "invalid AnnexIII region", "REVIEW_REQUIRED")
    regions = [row for row in profile["tables"]["premium_reserve_macroregions"]["rows"] if row[0] == region]
    require(len(regions) == 1, "region", "unique region definition required", "REVIEW_REQUIRED")
    _, name, text, page = regions[0]
    return int(region), {
        "territory": territory, "region_key": region, "region_name": name,
        "excluded_territories": list(exclusions), "original_region_territories": text,
        "evidence_pdf_page": page, "risk_location_reference": risk_location_reference,
        "risk_location_status": "EXTERNAL_UNVERIFIED", "aliases_inferred": False,
        "current_political_status_verified": False, "natcat_zone_identified": False,
        "regional_volume_calculated": False,
        "scope": "literal_AnnexIII_lookup_after_external_risk_location_qualification",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-III:8"]}
