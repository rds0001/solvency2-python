"""Natural catastrophe scenario components, not reinsurance/BOF projection."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar

ARTICLES = {"windstorm": 121, "earthquake": 122, "flood": 123, "hail": 124, "subsidence": 125}
SEQUENCED = ("windstorm", "flood", "hail")


def _qualified(peril, reference, allowed=ARTICLES):
    require(isinstance(peril, str) and peril in allowed, "peril", "supported peril required")
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external contract/geography/valuation qualification required", "MISSING_INPUT")


@calculation()
def natural_cat_insured_sum(peril: str, components: Mapping, *, qualification_reference: str, context: Context):
    """Sum eligible zone exposures; flood/hail motor weights differ.

    Classify LOB7/19 property, LOB6/18 onshore property and LOB5/17 motor
    externally. Subsidence covers eligible residential property; its region
    scope is France historically, Annex VIIIA regions in the 2027 profile.
    """
    _qualified(peril, qualification_reference)
    keys = ["residential_property"] if peril == "subsidence" else ["property", "onshore_property"]
    if peril in ("flood", "hail"):
        keys.append("motor")
    exact_keys(components, keys, "components")
    values = {key: number(components[key], key, 0) for key in keys}
    weight = number(scalar("natural_" + peril + "_motor_weight", context), "motor_weight", 0) if "motor" in keys else None
    total = math.fsum(value * (weight if key == "motor" else 1) for key, value in values.items())
    paragraph = {"earthquake": 4, "subsidence": 2}.get(peril, 7)
    if peril == "subsidence":
        paragraph = effective_resource("profile.json", context).get("methods", {}).get("natural_subsidence_paragraph", 2)
    return total, {"peril": peril, "components": values, "motor_weight": weight,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "zone_insured_sum_before_Q_W_weighting",
                   "_sources": [f"DR:article-{ARTICLES[peril]}:{paragraph}"]}


@calculation()
def natural_cat_weighted_cap(weighted_sum: float, peril: str, use_alternative: bool | None,
                             potential_gross_loss: float | None = None, *, qualification_reference: str, context: Context):
    """Optional externally justified lower WSI, never a reinsurance-net amount."""
    _qualified(peril, qualification_reference)
    value = number(weighted_sum, "weighted_sum", 0)
    require(use_alternative is None or isinstance(use_alternative, bool), "use_alternative", "boolean required")
    require(use_alternative is not None, "use_alternative", "explicit alternative-method choice required", "REVIEW_REQUIRED")
    if use_alternative:
        limit = number(potential_gross_loss, "potential_gross_loss", 0)
    else:
        require(potential_gross_loss is None, "potential_gross_loss", "omit unused alternative bound")
        limit = None
    result = min(value, limit) if use_alternative else value
    paragraph = {"earthquake": 3, "subsidence": 2}.get(peril, 6)
    if peril == "subsidence":
        paragraph = effective_resource("profile.json", context).get("methods", {}).get("natural_subsidence_paragraph", 2)
    return result, {"peril": peril, "weighted_sum": value, "potential_gross_loss": limit,
                    "use_alternative": use_alternative, "reduced": result < value,
                    "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                    "scope": "qualified_alternative_weighted_sum_before_zone_aggregation",
                    "_sources": [f"DR:article-{ARTICLES[peril]}:{paragraph}"]}


@calculation()
def natural_cat_event_loss(prescribed_loss: float, peril: str, scenario: str, event: int,
                           *, qualification_reference: str, context: Context):
    """One ordered gross event; do not replace sequential recoveries with a sum.

    Article126 independence, no new mitigation between events, and realistic
    existing reinstatements must be reflected in external sequence valuation.
    """
    _qualified(peril, qualification_reference, SEQUENCED)
    require(isinstance(scenario, str) and scenario in ("A", "B"), "scenario", "A or B required")
    require(isinstance(event, int) and not isinstance(event, bool) and event in (1, 2), "event", "ordered event1 or2 required")
    amount = number(prescribed_loss, "prescribed_loss", 0)
    table = effective_resource("profile.json", context)["tables"]["natural_" + peril + "_events"]
    factor = number(dict(table["rows"])[f"{scenario}/{event}"], "event_factor", 0)
    paragraph = 3 if scenario == "A" else 4
    return amount * factor, {"peril": peril, "scenario": scenario, "event": event, "factor": factor,
                             "prescribed_loss": amount, "qualification_reference": qualification_reference,
                             "qualification_status": "EXTERNAL_UNVERIFIED",
                             "scope": "ordered_gross_event_only_not_sequence_bof_or_scr",
                             "_sources": [f"DR:article-{ARTICLES[peril]}:{paragraph}", "DR:article-126"]}


@calculation()
def natural_cat_scenario_risk(peril: str, scenario_charges: Mapping, *, qualification_reference: str, context: Context):
    """Maximum of externally valued A/B sequence capital, not sum of event losses."""
    _qualified(peril, qualification_reference, SEQUENCED)
    exact_keys(scenario_charges, ["A", "B"], "scenario_charges")
    charges = {key: number(scenario_charges[key], key, 0) for key in ("A", "B")}
    value = max(charges.values())
    return value, {"peril": peril, "scenario_charges": charges,
                   "selected_scenarios": [key for key in charges if charges[key] == value],
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "maximum_external_sequence_capital_only",
                   "_sources": [f"DR:article-{ARTICLES[peril]}:2", "DR:article-126"]}


@calculation()
def natural_cat_other_loss(peril: str, gross_premium: float, diversification: float,
                           *, qualification_reference: str, context: Context):
    """Outside AnnexXIII: eligible next12month gross premiums and external DIV.

    DIV uses the prescribed premium basis for AnnexIII regions5–18, not generic
    premium/reserve volumes. Geographic membership is not inferred here.
    """
    _qualified(peril, qualification_reference, ("windstorm", "earthquake", "flood", "hail"))
    premium = number(gross_premium, "gross_premium", 0)
    div = number(diversification, "diversification", 0, 1)
    require(div > 0, "diversification", "positive externally qualified DIV required")
    table = effective_resource("profile.json", context)["tables"]["natural_other_factors"]
    row = next(row for row in table["rows"] if row[0] == peril)
    multiplier, weight, base = [number(value, name, 0) for name, value in zip(table["columns"][1:], row[1:])]
    factor = multiplier * (weight * div + base)
    paragraph = 6 if peril == "earthquake" else 9
    return factor * premium, {"peril": peril, "gross_premium": premium, "diversification": div,
                              "effective_factor": factor, "qualification_reference": qualification_reference,
                              "qualification_status": "EXTERNAL_UNVERIFIED",
                              "scope": "gross_other_region_claim_before_reinsurance_not_bof_or_scr",
                              "_sources": [f"DR:article-{ARTICLES[peril]}:{paragraph}"]}
