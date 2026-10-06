"""Article217 common scenario choice and non-diversified notional SCR total.

Portfolio valuation, profit-sharing adjustments and Article216 exemptions are
externally qualified. Signed scenario effects must not be floored before choice.
"""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require


def _scope(kinds, article217_scope_confirmed, reference, context):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "portfolio classification, completeness and Article216/217 qualification required", "MISSING_INPUT")
    require(article217_scope_confirmed is None or isinstance(article217_scope_confirmed, bool),
            "article217_scope_confirmed", "boolean or unresolved None required")
    require(article217_scope_confirmed is not None, "article217_scope_confirmed",
            "Article216 exemption or scope unresolved", "REVIEW_REQUIRED")
    require(article217_scope_confirmed, "article217_scope_confirmed",
            "Article216(2) exempt portfolio requires the ordinary diversified route", "UNSUPPORTED_METHOD")
    require(isinstance(kinds, Mapping) and bool(kinds), "portfolio_kinds", "explicit complete mapping required",
            "MISSING_INPUT")
    method = effective_resource("profile.json", context).get("methods", {}).get("restricted_funds")
    require(method in ("RFF_AND_MA_BASELINE", "RFF_ONLY_2027"), "restricted_funds",
            "versioned restricted portfolio scope required", "UNSUPPORTED_RULESET")
    allowed = {"ring_fenced", "remainder"} | ({"matching_adjustment"} if method == "RFF_AND_MA_BASELINE" else set())
    for key, kind in kinds.items():
        require(isinstance(key, str) and bool(key.strip()), "portfolio_kinds", "nonempty identifiers required")
        require(isinstance(kind, str) and kind in allowed, key, "portfolio kind outside versioned Article217 scope",
                "UNSUPPORTED_METHOD")
    require(list(kinds.values()).count("remainder") == 1, "portfolio_kinds",
            "exactly one explicit remainder, including a zero remainder, required")
    return {"portfolio_kinds": dict(kinds), "rule_scope": method,
            "qualification_reference": reference, "qualification_status": "EXTERNAL_UNVERIFIED",
            "article216_exemption_applied": False}


@calculation("DR:article-216", "DR:article-217:3-7")
def restricted_portfolio_scenario_charge(portfolio_kinds: Mapping, gross_losses: Mapping,
                                          net_losses: Mapping, target_portfolio: str, *,
                                          article217_scope_confirmed: bool | None,
                                          qualification_reference: str, context: Context,
                                          view: str = "gross", tie_break: str | None = None):
    """One portfolio's nonnegative charge under the COMMON worst net scenario.

    Nested losses are portfolio -> scenario -> signed BOF loss, already adjusted
    for217(5) profit participation. A gain is negative and offsets losses when
    selecting the whole-undertaking scenario, never after independent choices.
    net includes qualified FDB absorption; gross and net retain the same scenario.
    """
    details = _scope(portfolio_kinds, article217_scope_confirmed, qualification_reference, context)
    require(isinstance(target_portfolio, str) and target_portfolio in portfolio_kinds,
            "target_portfolio", "explicit in-scope target required", "MISSING_INPUT")
    require(view in ("gross", "net"), "view", "gross or net required")
    exact_keys(gross_losses, list(portfolio_kinds), "gross_losses")
    exact_keys(net_losses, list(portfolio_kinds), "net_losses")
    first = next(iter(portfolio_kinds))
    require(isinstance(gross_losses[first], Mapping) and bool(gross_losses[first]),
            "scenarios", "explicit nonempty scenario set required", "MISSING_INPUT")
    scenarios = list(gross_losses[first])
    require(all(isinstance(k, str) and bool(k.strip()) for k in scenarios), "scenarios",
            "nonempty scenario identifiers required")
    gross, net = {}, {}
    for key in portfolio_kinds:
        exact_keys(gross_losses[key], scenarios, "gross_losses/" + key)
        exact_keys(net_losses[key], scenarios, "net_losses/" + key)
        gross[key] = {s: number(gross_losses[key][s], f"gross/{key}/{s}") for s in scenarios}
        net[key] = {s: number(net_losses[key][s], f"net/{key}/{s}") for s in scenarios}
    totals = {s: math.fsum(net[p][s] for p in portfolio_kinds) for s in scenarios}
    maximum = max(totals.values())
    winners = sorted(s for s in scenarios if totals[s] == maximum)
    if tie_break is not None:
        require(tie_break in winners, "tie_break", "must maximize the whole-undertaking net loss")
        selected = tie_break
    else:
        # Same total does not imply identical portfolio charges. Require one
        # consistent tie decision for all targets, even if this target is equal.
        vectors = {tuple(values[p][s] for values in (gross, net) for p in portfolio_kinds) for s in winners}
        require(len(vectors) == 1, "tie_break", "tied totals have different portfolio effects",
                "AMBIGUOUS_SELECTION")
        selected = winners[0]
    signed = (gross if view == "gross" else net)[target_portfolio][selected]
    return max(signed, 0), {**details, "selected_scenario": selected, "tied_scenarios": winners,
                            "whole_undertaking_net_losses": totals, "target_portfolio": target_portfolio,
                            "signed_selected_loss": signed, "view": view,
                            "profit_sharing_adjustments": "EXTERNALLY_VALUED_ARTICLE217_5",
                            "scope": "common_scenario_selected_portfolio_component_not_notional_scr"}


@calculation("DR:article-216", "DR:article-217:1-2", "DR:article-217:8-9")
def restricted_portfolio_scr_sum(notional_scr: Mapping, portfolio_kinds: Mapping, *,
                                  article217_scope_confirmed: bool | None,
                                  qualification_reference: str, context: Context):
    """Sum complete qualified notional SCRs, including remainder; no diversification."""
    details = _scope(portfolio_kinds, article217_scope_confirmed, qualification_reference, context)
    exact_keys(notional_scr, list(portfolio_kinds), "notional_scr")
    values = {k: number(v, "notional_scr/" + k, 0) for k, v in notional_scr.items()}
    return math.fsum(values.values()), {**details, "notional_scr": values,
                                       "between_portfolio_diversification": False,
                                       "scope": "article217_sum_not_regulatory_total_release"}
