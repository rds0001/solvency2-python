"""Labelled quadratic aggregation; all components must be explicitly supplied."""
from __future__ import annotations

import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .scenario_assumptions import _check_gross_assumptions


def quadratic(components: Mapping[str, float], matrix: dict) -> tuple[float, dict]:
    labels, values = matrix["labels"], matrix["values"]
    exact_keys(components, labels, "components")
    x = [number(components[key], key, 0) for key in labels]
    products = [math.fsum(values[i][j] * x[j] for j in range(len(x))) for i in range(len(x))]
    squared = math.fsum(x[i] * products[i] for i in range(len(x)))
    require(squared >= 0, "matrix", "negative quadratic form", "NUMERICAL_ERROR")
    value = math.sqrt(squared)
    return value, {"quadratic_form": squared, "labels": list(labels),
                   "euler_contributions": dict(zip(labels, (x[i] * products[i] / value if value else 0
                                                            for i in range(len(x))))),
                   "_sources": [matrix["source"]]}


@calculation()
def aggregate_risk(components: Mapping[str, float], matrix_id: str, *, context: Context):
    """Aggregate already determined module charges using an explicit regulatory matrix."""
    matrices = effective_resource("profile.json", context)["matrices"]
    require(matrix_id in matrices, "matrix_id", "unknown matrix", "UNSUPPORTED_PARAMETER")
    value, details = quadratic(components, matrices[matrix_id])
    return value, {**details, "matrix_id": matrix_id, "scope": "aggregation_only"}


@calculation()
def catastrophe_zone_aggregation(peril: str, region: str, weighted_sums: Mapping[str, float],
                                 *, context: Context):
    """sqrt(WSI' C WSI) for one Annex XXII–XXVI peril/region; WSI supplied externally."""
    require(isinstance(peril, str) and isinstance(region, str), "peril/region", "string IDs required")
    key = f"{peril}/{region}"
    data = effective_resource("catastrophe_matrices.json", context)
    blocked = data.get("blocked_matrices", {}).get(key)
    require(blocked is None, "peril/region", f"{key}: source matrix requires review: {blocked}", "REVIEW_REQUIRED")
    matrices = data["matrices"]
    require(key in matrices, "peril/region", "unknown catastrophe matrix", "UNSUPPORTED_PARAMETER")
    matrix = matrices[key]
    value, details = quadratic(weighted_sums, matrix)
    return value, {**details, "peril": peril, "region": region, "matrix_id": key,
                   "source_article": matrix["article"], "scope": "weighted_zone_aggregation_only"}


@calculation()
def catastrophe_region_aggregation(peril: str, region_charges: Mapping[str, float],
                                   other_charge: float, *, context: Context):
    """Aggregate externally determined regional catastrophe charges plus other-region charge."""
    require(isinstance(peril, str), "peril", "string peril required")
    perils = effective_resource("catastrophe_regions.json", context)["perils"]
    require(peril in perils, "peril", "unknown catastrophe peril", "UNSUPPORTED_PARAMETER")
    entry = perils[peril]
    require(entry["status"] == "STRUCTURAL_CHECK_PASSED", "peril",
            "regional code conflict requires review", "REVIEW_REQUIRED")
    regional, details = quadratic(region_charges, entry["matrix"])
    other = number(other_charge, "other_charge", 0)
    total = math.hypot(regional, other)
    details["euler_contributions"] = {k: v * regional / total if total else 0
                                      for k, v in details["euler_contributions"].items()}
    return total, {**details, "peril": peril, "regional_aggregate": regional,
                   "other_charge": other, "other_euler_contribution": other ** 2 / total if total else 0,
                   "source_article": {"windstorm": "DR:article-121:1", "earthquake": "DR:article-122:1",
                                      "flood": "DR:article-123:1", "hail": "DR:article-124:1",
                                      "subsidence": "DR:article-125:1"}[peril],
                   "scope": "regional_charge_aggregation_only"}


@calculation()
def catastrophe_weighted_sum(peril: str, region: str, zone_ordinal: int, insured_sum: float,
                             *, context: Context):
    """Q*W*SI for an externally qualified zone ordinal, not an address-to-zone mapping.

    Future subsidence uses Annex VIIIA Q. Unqualified future geographic links
    stay explicitly absent instead of inheriting historical labels.
    """
    require(isinstance(peril, str) and isinstance(region, str), "peril/region", "string IDs required")
    require(isinstance(zone_ordinal, int) and not isinstance(zone_ordinal, bool) and zone_ordinal > 0,
            "zone_ordinal", "positive integer required")
    weights = effective_resource("catastrophe_weights.json", context)
    tables = weights["tables"]
    require(peril in tables, "peril", "unknown catastrophe peril", "UNSUPPORTED_PARAMETER")
    require(f"{peril}/{region}/{zone_ordinal}" not in weights["blocked_cells"],
            "region/zone_ordinal", "published zone has no corresponding Annex IX/XXIV zone",
            "REVIEW_REQUIRED")
    row = tables[peril]["weights"].get(str(zone_ordinal), {})
    require(region in row, "region/zone_ordinal", "no published weight for this region and zone",
            "UNSUPPORTED_PARAMETER")
    if peril == "subsidence" and f"subsidence/{region}" in weights["special_factors"]:
        factor = weights["special_factors"]["subsidence/FR"]["value"]
        factor_source = "DR:article-125:2"
    else:
        regions = effective_resource("catastrophe_regions.json", context)
        factors = regions["perils"][peril]["factors"]
        require(region in factors, "region", "no published regional factor", "UNSUPPORTED_PARAMETER")
        factor, factor_source = factors[region], regions["perils"][peril]["source"]
    insured = number(insured_sum, "insured_sum", 0)
    weight = row[region]
    links_available = weights.get("zone_links_available", True)
    link = (effective_resource("catastrophe_zone_links.json", context)["links"].get(f"{peril}/{region}")
            if links_available else None)
    return factor * weight * insured, {"peril": peril, "region": region, "zone_ordinal": zone_ordinal,
                                     "regional_factor": factor, "zone_weight": weight,
                                     "insured_sum": insured, "scope": "primary_weight_formula_only",
                                     "matrix_zone_label": (link["labels_by_ordinal"].get(str(zone_ordinal))
                                                           if link else None),
                                     "zone_link_status": (link["status"] if link else "NO_ZONE_MATRIX"
                                                          if links_available else "UNQUALIFIED_GEOGRAPHY"),
                                     "_sources": [factor_source, "DR:annex-X"]}


@calculation("DIR:article-104", "DIR:annex-IV:1", "DR:article-87", "DR:article-203")
def basic_scr(components: Mapping[str, float], intangible_charge: float, *, context: Context):
    """Five-module aggregation plus the charge on recognised intangible assets."""
    value, details = quadratic(components, effective_resource("profile.json", context)["matrices"]["bscr"])
    intangible_charge = number(intangible_charge, "intangible_charge", 0)
    return value + intangible_charge, {**details, "intangible_charge": intangible_charge,
                                       "scope": "aggregation_only"}


@calculation("DR:article-83:5")
def scenario_loss(base_bof: float, stressed_bof: float, *, context: Context,
                  assumption_checks: Mapping | None = None):
    """Loss from external BOF; optional gross83 input checks are not a valuation model."""
    checks = _check_gross_assumptions(assumption_checks) if assumption_checks is not None else None
    loss = number(base_bof, "base_bof") - number(stressed_bof, "stressed_bof")
    return max(loss, 0), {"unfloored_loss": loss, "valuation_support": "EXTERNAL_INPUT_ONLY",
                          "gross_assumption_checks": checks,
                          "_sources": ["DR:article-83:1-2", "DR:article-83:4"] if checks else []}


@calculation("DR:article-165:2", "DR:article-142:7", "DR:article-188:7", "DR:article-179:4")
def select_scenario(gross_losses: Mapping[str, float], net_losses: Mapping[str, float],
                    tie_break: str | None = None, *, context: Context):
    """Select the gross charge corresponding to the greatest net-of-FDB loss."""
    return _select_scenario(gross_losses, net_losses, tie_break)


def _select_scenario(gross_losses, net_losses, tie_break=None):
    """Shared selection arithmetic, with provenance attached at public boundaries."""
    require(isinstance(gross_losses, Mapping) and bool(gross_losses), "gross_losses", "nonempty mapping required")
    exact_keys(net_losses, list(gross_losses), "net_losses")
    gross = {k: number(v, k, 0) for k, v in gross_losses.items()}
    net = {k: number(v, k, 0) for k, v in net_losses.items()}
    maximum = max(net.values())
    winners = sorted(k for k, v in net.items() if v == maximum)
    if tie_break is not None:
        require(tie_break in winners, "tie_break", "selection must maximize net loss")
        selected = tie_break
    else:
        require(len({gross[k] for k in winners}) == 1, "tie_break", "ambiguous gross charges at net tie",
                "AMBIGUOUS_SELECTION")
        selected = winners[0]
    return gross[selected], {"selected_scenario": selected, "selected_net_loss": net[selected],
                              "tied_scenarios": winners, "gross_losses": gross, "net_losses": net}
