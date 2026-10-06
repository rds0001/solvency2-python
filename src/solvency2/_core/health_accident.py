"""Health accident scenarios and aggregation; claims remain distinct from BOF capital."""
import math
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .health_pandemic import _mapping, _reference


def _weights(context):
    return {key: number(value, key, 0, 1) for key, value in
            effective_resource("profile.json", context)["tables"]["health_accident_event_weights"]["rows"]}


def _regions(context):
    return {key: number(value, key, 0, 1) for key, value in
            effective_resource("profile.json", context)["tables"]["health_mass_accident_regions"]["rows"]}


def _event_sum(values, context):
    weights = _weights(context)
    exact_keys(values, list(weights), "events")
    exposures = {key: number(values[key], key, 0) for key in weights}
    return math.fsum(weights[key] * exposures[key] for key in weights), weights, exposures


def _benefits(benefits, reference):
    _mapping(benefits, "benefits")
    _reference(reference, "valuation_reference")
    return {key: number(value, key, 0) for key, value in benefits.items()}


def _grouped_benefits(values, counts, reference, mean):
    """Weight per-person HRG benefits; do not count each group as one person."""
    _reference(reference, "grouping_reference")
    exact_keys(counts, tuple(values), "group_counts")
    numbers = {}
    for key, raw in counts.items():
        count = number(raw, f"group_counts.{key}", 0)
        require(count.is_integer(), f"group_counts.{key}", "whole event-insured person count required")
        numbers[key] = int(count)
    persons = sum(numbers.values())
    require(not mean or persons > 0, "group_counts", "empty event population has undefined average",
            "REVIEW_REQUIRED")
    # Exact integer counts avoid intermediate overflow before division in a mean.
    weighted = sum((Fraction(str(values[key])) * count for key, count in numbers.items()), Fraction(0))
    try:
        result = float(weighted / persons if mean else weighted)
    except OverflowError:
        require(False, "benefits", "grouped result outside representable range", "REVIEW_REQUIRED")
    return result, {"group_counts": numbers, "event_insured_persons": persons,
        "grouping_reference": reference, "grouping_status": "EXTERNAL_UNVERIFIED",
        "benefit_basis": "per_person_within_each_externally_qualified_HRG"}


@calculation("DR:article-161:3-4")
def health_accident_benefit_sum(benefits: Mapping, *, valuation_reference: str, context: Context,
                               group_counts: Mapping | None = None, grouping_reference: str | None = None):
    """Sum externally qualified event benefits of resident insured persons."""
    values = _benefits(benefits, valuation_reference)
    if group_counts is not None:
        value, grouping = _grouped_benefits(values, group_counts, grouping_reference, False)
        return value, {**grouping, "benefits": values, "valuation_reference": valuation_reference,
                       "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "grouped_event_exposure_sum_only"}
    require(grouping_reference is None, "grouping_reference", "grouping reference unused without group counts")
    return math.fsum(values.values()), {"benefits": values, "valuation_reference": valuation_reference,
                                       "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "event_exposure_sum_only"}


@calculation("DR:article-162:4-5")
def health_accident_benefit_mean(benefits: Mapping, *, valuation_reference: str, context: Context,
                                group_counts: Mapping | None = None, grouping_reference: str | None = None):
    """Average only event-insured persons in the externally selected concentration.

    The denominator is event-specific Ne, not the whole building count Cc.
    Empty event populations require review, never an invented zero mean.
    """
    values = _benefits(benefits, valuation_reference)
    if group_counts is not None:
        value, grouping = _grouped_benefits(values, group_counts, grouping_reference, True)
        return value, {**grouping, "valuation_reference": valuation_reference,
                       "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "grouped_event_mean_benefit_only"}
    require(grouping_reference is None, "grouping_reference", "grouping reference unused without group counts")
    require(bool(values), "benefits", "empty event population has undefined average", "REVIEW_REQUIRED")
    count = len(values)
    return math.fsum(value / count for value in values.values()), {
        "event_insured_persons": count, "valuation_reference": valuation_reference,
        "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "event_mean_benefit_only"}


@calculation("DR:article-161:2", "DR:annex-XVI")
def health_mass_accident_loss(segment: str, event_exposures: Mapping, *, exposure_reference: str, context: Context):
    """Gross claim for one printed AnnexXVI segment, before reinsurance and BOF revaluation."""
    regions = _regions(context)
    require(isinstance(segment, str) and segment in regions, "segment", "explicit AnnexXVI segment required",
            "UNSUPPORTED_PARAMETER")
    _reference(exposure_reference, "exposure_reference")
    weighted, weights, values = _event_sum(event_exposures, context)
    return regions[segment] * weighted, {
        "segment": segment, "affected_share": regions[segment], "event_weights": weights,
        "event_exposures": values, "weighted_exposure": weighted, "exposure_reference": exposure_reference,
        "exposure_status": "EXTERNAL_UNVERIFIED", "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}


@calculation("DR:article-162:2-3", "DR:annex-XVI")
def health_accident_concentration_loss(persons: float, mean_benefits: Mapping, *,
                                      concentration_reference: str, context: Context):
    """Use the externally identified largest qualified building population, not largest loss."""
    count = number(persons, "persons", 0)
    require(count.is_integer(), "persons", "whole person count required")
    _reference(concentration_reference, "concentration_reference")
    weighted, weights, values = _event_sum(mean_benefits, context)
    return count * weighted, {"persons": count, "mean_benefits": values, "event_weights": weights,
                              "concentration_reference": concentration_reference,
                              "concentration_status": "EXTERNAL_UNVERIFIED",
                              "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}


@calculation("DR:article-161:1", "DR:article-162:1")
def health_accident_country_aggregation(country_charges: Mapping, peril: str, *, scope_reference: str, context: Context):
    """Root-sum-square of already valued country BOF charges, never of gross claims."""
    require(peril in ("mass_accident", "concentration"), "peril", "supported health accident peril required")
    _mapping(country_charges, "country_charges")
    _reference(scope_reference, "scope_reference")
    if peril == "mass_accident":
        exact_keys(country_charges, list(_regions(context)), "country_charges")
    values = {key: number(value, key, 0) for key, value in country_charges.items()}
    return math.hypot(*values.values()), {"country_charges": values, "peril": peril,
                                         "scope_reference": scope_reference, "scope_status": "EXTERNAL_UNVERIFIED",
                                         "scope": "supplied_country_capital_aggregation_only"}
