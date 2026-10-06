"""Currency-coherent interest scenarios; valuations supplied externally in run currency."""
import math
from typing import Mapping

from .aggregation import _select_scenario, quadratic
from .core import Context, calculation, effective_resource, exact_keys, number, require


@calculation("DR:article-166:3", "DR:article-167:3")
def interest_participation_bof_change(participations: Mapping, *, direction: str,
                                     qualification_reference: str, context: Context):
    """Retain gains but exclude losses on Art68-deducted financial holdings.

    Signed BOF deltas are externally valued for one up/down scenario and one
    consistent gross/net-FDB basis. Apply before full currency-scenario losses,
    never subtract the result from an already floored SCR. No pricing or legal
    deduction qualification is inferred. The arithmetic is shared with188(6).
    """
    from .currency import _participation_bof_change
    require(direction in ("up", "down"), "direction", "explicit up/down scenario required")
    value, details = _participation_bof_change(participations, qualification_reference)
    return value, {**details, "direction": direction,
        "scope": "signed_interest_participation_delta_not_valuation_or_interest_scr"}


def _interest(gross_by_currency, net_by_currency, valuation_reference, tie_break):
    require(isinstance(valuation_reference, str) and bool(valuation_reference.strip()),
            "valuation_reference", "external currency/FDB valuation reference required", "MISSING_INPUT")
    require(isinstance(gross_by_currency, Mapping) and bool(gross_by_currency),
            "gross_by_currency", "nonempty explicit currency mapping required", "MISSING_INPUT")
    exact_keys(net_by_currency, list(gross_by_currency), "net_by_currency")
    validated = []
    for name, mapping in (("gross", gross_by_currency), ("net", net_by_currency)):
        values = {}
        for currency, row in mapping.items():
            require(isinstance(currency, str) and bool(currency.strip()), "currency", "nonempty currency ID required")
            exact_keys(row, ["up", "down"], f"{name}.{currency}")
            values[currency] = {direction: number(row[direction], f"{name}.{currency}.{direction}", 0)
                                for direction in ("up", "down")}
        validated.append(values)
    gross, net = [{direction: math.fsum(row[direction] for row in mapping.values())
                   for direction in ("up", "down")} for mapping in validated]
    # Neutral equal-charge/equal-net tie: deterministic up; unequal gross stays explicit.
    choice = "up" if tie_break is None and gross["up"] == gross["down"] and net["up"] == net["down"] else tie_break
    charge, details = _select_scenario(gross, net, choice)
    equals_up = charge == gross["up"]
    return charge, {**details, "gross_by_currency": validated[0], "net_by_currency": validated[1],
                     "matrix_id": "market_up" if equals_up else "market_down",
                     "matrix_selection_basis": "selected_charge_equals_up_charge" if equals_up else "selected_charge_differs_from_up",
                     "valuation_reference": valuation_reference, "valuation_status": "EXTERNAL_UNVERIFIED",
                     "scope": "supplied_currency_scenarios_only"}


@calculation("DR:article-165", "DR:article-164:3", "DR:article-206:2")
def interest_scenario_charge(gross_by_currency: Mapping, net_by_currency: Mapping, *,
                             valuation_reference: str, tie_break: str | None = None, context: Context):
    """Sum each direction across qualified currency groups before scenario selection.

    Future EUR/peg joint scenarios must already be qualified and grouped externally,
    with no duplicate exposure. Currency/group keys never trigger automatic merging.
    """
    return _interest(gross_by_currency, net_by_currency, valuation_reference, tie_break)


@calculation("DR:article-164:2-3", "DR:article-165", "DR:article-206:2")
def market_risk_from_interest_scenarios(other_components: Mapping, gross_by_currency: Mapping,
                                       net_by_currency: Mapping, *, valuation_reference: str,
                                       tie_break: str | None = None, context: Context):
    """Aggregate supplied market submodules, with the source's interest-charge equality rule.

    Keys identify externally qualified stress currencies/groups; all monetary inputs are already in context
    currency. This function neither values instruments nor certifies completeness.
    The selected profile supplies its own matrices, including the2027 interest/spread B coefficient.
    """
    exact_keys(other_components, ["equity", "property", "spread", "concentration", "currency"], "other_components")
    interest, selection = _interest(gross_by_currency, net_by_currency, valuation_reference, tie_break)
    matrix_id = selection["matrix_id"]
    matrix = effective_resource("profile.json", context)["matrices"][matrix_id]
    value, details = quadratic({**other_components, "interest": interest}, matrix)
    return value, {**details, "interest_charge": interest, "interest_selection": selection,
                   "matrix_id": matrix_id, "scope": "market_component_aggregation_only"}
