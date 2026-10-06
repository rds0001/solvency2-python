"""Article163 gross pandemic scenario loss, explicitly not BOF loss or capital."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _mapping(values, field):
    require(isinstance(values, Mapping), field, "explicit mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in values), field, "nonempty string IDs required")


def _reference(reference, field):
    require(isinstance(reference, str) and bool(reference.strip()), field,
            "external selection/valuation reference required", "MISSING_INPUT")


@calculation("DR:article-163:2")
def health_pandemic_income_exposure(benefits: Mapping, *, valuation_reference: str, context: Context):
    """Sum externally valued permanent-disability benefits with no recovery assumed.

    Occupational accident obligations are excluded by external classification;
    recurring benefits require externally supplied best estimates, not face sums.
    """
    _mapping(benefits, "benefits")
    _reference(valuation_reference, "valuation_reference")
    values = {key: number(value, key, 0) for key, value in benefits.items()}
    return math.fsum(values.values()), {"benefits": values, "valuation_reference": valuation_reference,
                                       "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "income_exposure_only_not_scr"}


@calculation("DR:article-163:3", "DR:annex-XVI")
def health_pandemic_medical_cost(costs: Mapping, *, valuation_reference: str, context: Context):
    """Weight all three externally valued care types; never silently normalise overrides."""
    table = effective_resource("profile.json", context)["tables"]["health_pandemic_care_weights"]
    weights = {key: number(value, key, 0, 1) for key, value in table["rows"]}
    exact_keys(costs, list(weights), "costs")
    _reference(valuation_reference, "valuation_reference")
    values = {key: number(costs[key], key, 0) for key in weights}
    return math.fsum(weights[key] * values[key] for key in weights), {
        "costs": values, "weights": weights, "weight_sum": math.fsum(weights.values()),
        "valuation_reference": valuation_reference, "valuation_status": "EXTERNAL_UNVERIFIED",
        "scope": "average_medical_cost_per_person_only_not_scr"}


@calculation("DR:article-163:1")
def health_pandemic_loss(income_exposure: float, countries: Mapping, *, exposure_reference: str, context: Context):
    """Gross sudden scenario claim before reinsurance; country residence/scope external."""
    income = number(income_exposure, "income_exposure", 0)
    _mapping(countries, "countries")
    _reference(exposure_reference, "exposure_reference")
    totals = {}
    for country, row in countries.items():
        exact_keys(row, ["persons", "medical_cost"], country)
        persons = number(row["persons"], country + ".persons", 0)
        require(persons.is_integer(), country + ".persons", "whole person count required")
        cost = number(row["medical_cost"], country + ".medical_cost", 0)
        totals[country] = number(persons * cost, country + ".total", 0)
    income_factor = number(scalar("health_pandemic_income_factor", context), "health_pandemic_income_factor", 0, 1)
    share = number(scalar("health_pandemic_symptomatic_share", context), "health_pandemic_symptomatic_share", 0, 1)
    income_loss = income_factor * income
    medical_loss = share * math.fsum(totals.values())
    return math.fsum((income_loss, medical_loss)), {
        "income_loss": income_loss, "medical_loss": medical_loss, "country_medical_totals": totals,
        "income_factor": income_factor, "symptomatic_share": share,
        "exposure_reference": exposure_reference, "exposure_status": "EXTERNAL_UNVERIFIED",
        "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}
