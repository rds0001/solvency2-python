"""Exact Annex IX geographic-code lookup; no inferred address normalization."""
from .core import Context, calculation, effective_resource, require


@calculation("DR:annex-IX", unit="zone_ordinal")
def catastrophe_zone_ordinal(region: str, geographic_code: str, *, context: Context):
    """Resolve an explicitly supplied published code to its zone ordinal.

    Callers must first apply the region's documented postcode/province rule.
    This function never guesses a prefix from a full address or repairs source
    conflicts; the latter produce REVIEW_REQUIRED for the affected code only.
    """
    require(isinstance(region, str) and bool(region), "region", "nonempty region code required")
    require(isinstance(geographic_code, str) and bool(geographic_code)
            and geographic_code == geographic_code.strip(), "geographic_code",
            "exact published code required as a string")

    compact = effective_resource("catastrophe_zone_map.json", context)["mapping"]
    if region in compact:
        matches = [(ordinal, row) for ordinal, row in compact[region].items()
                   if row["zone"] == geographic_code]
        require(bool(matches), "geographic_code", "no published code for region", "UNSUPPORTED_PARAMETER")
        require(len(matches) == 1, "geographic_code", "ambiguous printed code", "REVIEW_REQUIRED")
        ordinal, row = matches[0]
        return int(ordinal), {"region": region, "geographic_code": geographic_code,
                              "zone_ordinal": int(ordinal), "evidence": {"line": row["line"],
                                                                         "pdf_page": row["pdf_page"]},
                              "scope": "exact_published_code_only"}

    grouped = effective_resource("catastrophe_postcode_groups.json", context)["regions"]
    if region in grouped:
        matches = [(ordinal, zone) for ordinal, zone in grouped[region]["zones"].items()
                   if geographic_code in zone["postcodes"]]
        require(bool(matches), "geographic_code", "no published postcode prefix", "UNSUPPORTED_PARAMETER")
        require(len(matches) == 1, "geographic_code", "ambiguous postcode prefix", "REVIEW_REQUIRED")
        ordinal, zone = matches[0]
        return int(ordinal), {"region": region, "geographic_code": geographic_code,
                              "zone_ordinal": int(ordinal),
                              "prefix_length": grouped[region]["prefix_length"],
                              "evidence": zone["evidence"][geographic_code],
                              "scope": "exact_published_code_only"}

    districts = effective_resource("catastrophe_administrative.json", context)["mapping"]
    if region in districts:
        matches = [(ordinal, row) for ordinal, row in districts[region].items()
                   if row["name"] == geographic_code]
        require(bool(matches), "geographic_code", "no published district name for region",
                "UNSUPPORTED_PARAMETER")
        require(len(matches) == 1, "geographic_code", "ambiguous printed district name",
                "REVIEW_REQUIRED")
        ordinal, row = matches[0]
        return int(ordinal), {"region": region, "geographic_code": geographic_code,
                              "zone_ordinal": int(ordinal), "evidence": row["evidence"],
                              "scope": "exact_published_district_name_only"}

    raw = effective_resource("catastrophe_geography_raw.json", context)["regions"]
    if region == "FR":
        # The printed FR row for 05 repeats ordinal 4 and leaves 5 absent in both
        # archived editions. Keep the raw row, but never select a presumed fix.
        require(geographic_code != "05", "geographic_code", "conflicting FR zone row",
                "REVIEW_REQUIRED")
        matches = [row for row in raw["FR"]["entries"] if row["postcode"] == geographic_code]
        require(bool(matches), "geographic_code", "no published FR postcode prefix", "UNSUPPORTED_PARAMETER")
        require(len(matches) == 1, "geographic_code", "ambiguous FR postcode prefix", "REVIEW_REQUIRED")
        row = matches[0]
        ordinal = int(row["zone_ordinal"])
        return ordinal, {"region": region, "geographic_code": geographic_code,
                         "zone_ordinal": ordinal, "prefix_length": 2,
                         "evidence": {"line": row["line"], "pdf_page": row["pdf_page"]},
                         "scope": "exact_published_code_only"}

    if region == "SI":
        matches = [(ordinal, zone["evidence"][geographic_code])
                   for ordinal, zone in raw["SI"]["zones"].items()
                   if geographic_code in zone["evidence"]]
        require(bool(matches), "geographic_code", "no published SI postcode", "UNSUPPORTED_PARAMETER")
        require(len(matches) == 1, "geographic_code", "postcode assigned to multiple SI zones",
                "REVIEW_REQUIRED")
        ordinal, evidence = matches[0]
        return int(ordinal), {"region": region, "geographic_code": geographic_code,
                              "zone_ordinal": int(ordinal), "prefix_length": 4,
                              "evidence": evidence, "scope": "exact_published_code_only"}

    require(False, "region", "no verified geographic-code table in this profile", "UNSUPPORTED_PARAMETER")
