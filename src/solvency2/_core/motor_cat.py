"""Article129 EUR motor catastrophe components; qualification remains external."""
import math
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar


def _qualified(reference, context):
    require(context.currency == "EUR", "currency", "printed EUR thresholds require explicit conversion",
            "UNSUPPORTED_CURRENCY")
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external Article129 scope/basis reference required", "MISSING_INPUT")


@calculation("DR:article-129:2", unit="EUR")
def motor_assumed_limit(amounts: Mapping, basis: str, *, qualification_reference: str, context: Context):
    """Externally choose total, absent-total property/personal, or per-victim basis."""
    _qualified(qualification_reference, context)
    require(isinstance(basis, str) and basis in ("total", "property_personal", "per_victim"),
            "basis", "explicit supported coverage-limit basis required")
    keys = {"total": ["total"], "property_personal": ["property", "personal"],
            "per_victim": ["per_victim"]}[basis]
    exact_keys(amounts, keys, "amounts")
    values = {key: number(amounts[key], key, 0) for key in keys}
    multiplier = number(scalar("motor_cat_victims", context), "victims", 0) if basis == "per_victim" else 1
    return math.fsum(values.values()) * multiplier, {
        "basis": basis, "amounts": values, "multiplier": multiplier,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "assumed_coverage_limit_only_not_claim_or_scr"}


@calculation("DR:article-129:1:a-b", unit="count")
def motor_vehicle_count(vehicles: Mapping, category: str, *, qualification_reference: str, context: Context):
    """Aggregate qualified LOB4/16 vehicle groups, proportional shares applied once.

    Vehicle counts are whole numbers before weighting; the resulting count can
    be fractional. Each group must have a single assumed coverage limit/share.
    """
    _qualified(qualification_reference, context)
    require(isinstance(category, str) and category in ("high", "low"), "category", "high or low required")
    require(isinstance(vehicles, Mapping), "vehicles", "explicit mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in vehicles), "vehicles", "nonempty string IDs required")
    threshold = number(scalar("motor_cat_limit_threshold", context), "limit_threshold", 0)
    selected = {}
    for key, row in vehicles.items():
        exact_keys(row, ["assumed_limit", "count", "share"], key)
        limit = number(row["assumed_limit"], key + ".assumed_limit", 0)
        count = number(row["count"], key + ".count", 0)
        require(count.is_integer(), key + ".count", "whole unweighted vehicle count required")
        share = number(row["share"], key + ".share", 0, 1)
        if (limit > threshold) == (category == "high"):
            selected[key] = count * share
    return math.fsum(selected.values()), {
        "category": category, "limit_threshold": threshold, "weighted_counts": selected,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "weighted_eligible_vehicle_count_only"}


@calculation("DR:article-129:1", unit="EUR")
def motor_cat_loss(high_count: float, low_count: float, *, qualification_reference: str, context: Context):
    """Gross sudden claim, with literal floor even at zero supplied counts.

    Counts are already proportionally weighted. Whether this submodule applies
    to the undertaking is external; this API does not invent a zero-book waiver.
    """
    _qualified(qualification_reference, context)
    high = number(high_count, "high_count", 0)
    low = number(low_count, "low_count", 0)
    params = {key: number(scalar("motor_cat_" + key, context), key, 0)
              for key in ("floor", "multiplier", "low_weight", "capped_weight", "count_cap")}
    radicand = math.fsum((high, params["low_weight"] * low,
                         params["capped_weight"] * min(low, params["count_cap"])))
    unfloored = params["multiplier"] * math.sqrt(radicand)
    return max(params["floor"], unfloored), {
        "high_count": high, "low_count": low, "parameters": params,
        "radicand": radicand, "unfloored_loss": unfloored,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}
