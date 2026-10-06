"""Event-qualified sums and object maxima under Articles130–132.

Do not evaluate reinsurance contracts or substitute point distances for building
geometry. Inputs must already meet the documented external scope requirements.
"""
import math
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar

COMPONENTS = {
    "vessel": ("hull", "liability", "pollution"),
    "platform": ("property", "wreck_removal", "production_income", "well_control", "liability"),
    "aviation": ("hull", "liability"),
    "fire": ("insured_sum",),
}
SOURCES = {"vessel": "DR:article-130:2", "platform": "DR:article-130:3",
           "aviation": "DR:article-131", "fire": "DR:article-132:1-3"}


def _qualify(peril, reference):
    require(isinstance(peril, str) and peril in COMPONENTS, "peril", "supported concentration peril required")
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external scope, event-specific recovery and adequacy assessment required", "MISSING_INPUT")


@calculation()
def catastrophe_effective_sum(gross_sum: float, recoverable: float, use_gross: bool | None,
                              peril: str, *, qualification_reference: str, context: Context):
    """Qualified recovery subtraction or explicit gross fallback for inadequate risk capture.

    Recoveries conditional on unrelated claims must have been excluded externally.
    For vessel components apply separately; for other perils use the qualified
    combined object/group sum. The returned amount is not a BOF loss or SCR.
    """
    _qualify(peril, qualification_reference)
    require(use_gross is None or isinstance(use_gross, bool), "use_gross", "boolean assessment required")
    require(use_gross is not None, "use_gross", "unknown adequacy assessment", "REVIEW_REQUIRED")
    gross = number(gross_sum, "gross_sum", 0)
    recovery = number(recoverable, "recoverable", 0)
    require(recovery <= gross, "recoverable", "recovery above insured sum requires review", "REVIEW_REQUIRED")
    return gross if use_gross else gross - recovery, {
        "gross_sum": gross, "recoverable": recovery, "use_gross": use_gross, "peril": peril,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "effective_event_insured_sum_only_not_bof_or_scr", "_sources": [SOURCES[peril]]}


@calculation()
def manmade_concentration_loss(exposures: Mapping, peril: str, *, qualification_reference: str, context: Context):
    """Maximum combined effective insured sum of externally qualified objects.

    Fire inputs are complete, externally qualified building groups, not isolated
    points. Components are after qualified recovery/fallback; never deduct twice.
    Empty eligible populations return explicitly documented conventional zero.
    This is not the hypothetical Article196(a) capital calculation; its2027
    object-selection requirements need separate qualification.
    """
    _qualify(peril, qualification_reference)
    require(isinstance(exposures, Mapping), "exposures", "explicit object mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in exposures), "exposures", "nonempty string IDs required")
    threshold = None
    radius = None
    if peril == "vessel":
        require(context.currency == "EUR", "currency", "vessel threshold is printed in EUR", "UNSUPPORTED_CURRENCY")
        threshold = number(scalar("marine_vessel_minimum_value", context), "vessel_minimum_value", 0)
    if peril == "fire":
        radius = number(scalar("fire_concentration_radius", context), "fire_concentration_radius", 0)
    totals, excluded = {}, []
    for label, row in exposures.items():
        exact_keys(row, ["components", "insured_value"] if peril == "vessel" else ["components"], label)
        components = row["components"]
        exact_keys(components, COMPONENTS[peril], label + ".components")
        values = [number(components[key], label + "." + key, 0) for key in COMPONENTS[peril]]
        if peril == "vessel" and number(row["insured_value"], label + ".insured_value", 0) < threshold:
            excluded.append(label)
            continue
        totals[label] = math.fsum(values)
    value = max(totals.values(), default=0)
    return value, {"peril": peril, "effective_object_sums": totals,
                   "selected_ids": sorted(key for key in totals if totals[key] == value),
                   "below_threshold_ids": excluded, "minimum_vessel_value": threshold,
                   "externally_qualified_fire_radius_metres": radius,
                   "empty_population_convention": not bool(totals),
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "effective_scenario_claim_not_bof_or_scr", "_sources": [SOURCES[peril]]}
