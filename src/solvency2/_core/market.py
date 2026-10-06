"""Regulatory shock magnitudes, distinct from capital after full revaluation."""
from typing import Mapping

from ._duration_equity import duration_equity_factor
from .aggregation import _select_scenario
from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DR:article-179:1:4", "DR:article-206:2")
def credit_derivative_scenario_charge(gross_losses: Mapping | None, net_losses: Mapping | None, *,
                                     valuation_reference: str, tie_break: str | None = None,
                                     public_underlying: Mapping | None = None,
                                     hedge_exemption: Mapping | None = None,
                                     context: Context):
    """Select gross credit-derivative charge by maximal net-FDB scenario loss.

    Widening/tightening BOF valuations and Article179(3) hedge exclusions must
    be qualified externally. This is neither derivative pricing nor hedge approval.
    Article180(9) can instead use an explicitly qualified public debt underlying;
    no partial guarantee, other underlying or missing scenarios implies zero.
    """
    require(isinstance(valuation_reference, str) and bool(valuation_reference.strip()),
            "valuation_reference", "external gross/net-FDB scenario valuation required", "MISSING_INPUT")
    if hedge_exemption is not None:
        from .evidence import _declared_bool, _reference
        exact_keys(hedge_exemption, ("risk_mitigation_strategy", "held_exposure_route",
                   "exposure_held", "basis_risk_immaterial_all_circumstances",
                   "qualification_reference"), "hedge_exemption")
        require(public_underlying is None and gross_losses is None and net_losses is None and tie_break is None,
                "hedge_exemption", "use one explicit exemption route without scenario losses or tie choice")
        _reference(hedge_exemption["qualification_reference"], "hedge_exemption.qualification_reference")
        strategy = _declared_bool(hedge_exemption["risk_mitigation_strategy"], "risk_mitigation_strategy")
        held = _declared_bool(hedge_exemption["exposure_held"], "exposure_held")
        route = hedge_exemption["held_exposure_route"]
        require(isinstance(route, str) and route in {"underlying", "other_exposure"},
                "held_exposure_route", "explicit underlying or other_exposure required")
        basis = hedge_exemption["basis_risk_immaterial_all_circumstances"]
        if route == "underlying":
            require(basis is None, "basis_risk_immaterial_all_circumstances",
                    "other-exposure basis-risk declaration unused when holding the actual underlying")
            basis_met = True
        else:
            basis_met = _declared_bool(basis, "basis_risk_immaterial_all_circumstances")
        require(strategy and held and basis_met, "hedge_exemption",
                "Article179(3) declared prerequisites not met", "UNSUPPORTED_METHOD")
        return 0.0, {"hedge_exemption": dict(hedge_exemption), "valuation_reference": valuation_reference,
                     "qualification_status": "EXTERNAL_UNVERIFIED", "scenarios_required": False,
                     "basis_risk_verified": False, "other_risks_exempted": False,
                     "scope": "article179_3_qualified_hedge_spread_charge_only",
                     "_sources": ["DR:article-179:3"]}
    if public_underlying is not None:
        from .zero_factors import public_exposure_zero_factor
        exact_keys(public_underlying, ("category", "conditions", "qualification_reference",
                                       "underlying_is_bond_or_loan"), "public_underlying")
        require(public_underlying["underlying_is_bond_or_loan"] is not None, "underlying_is_bond_or_loan",
                "underlying instrument type unresolved", "REVIEW_REQUIRED")
        require(isinstance(public_underlying["underlying_is_bond_or_loan"], bool), "underlying_is_bond_or_loan",
                "explicit boolean required")
        require(public_underlying["underlying_is_bond_or_loan"], "underlying_is_bond_or_loan",
                "Article180(9) requires a bond or loan underlying", "REVIEW_REQUIRED")
        require(gross_losses is None and net_losses is None and tie_break is None, "public_underlying",
                "explicit zero-treatment route requires None scenarios and no tie choice")
        underlying = public_exposure_zero_factor(public_underlying["category"], public_underlying["conditions"],
            qualification_reference=public_underlying["qualification_reference"], context=context)
        require(underlying.value == 0, "public_underlying",
                "nonzero analyst factor cannot define derivative capital without revaluation", "REVIEW_REQUIRED")
        return 0.0, {"public_underlying": underlying.to_dict(), "valuation_reference": valuation_reference,
                     "valuation_status": "EXTERNAL_UNVERIFIED", "scenarios_required": False,
                     "scope": "article180_9_qualified_public_debt_underlying_spread_charge_only",
                     "_sources": ["DR:article-180:9", "DR:article-180:2"]}
    exact_keys(gross_losses, ["widening", "tightening"], "gross_losses")
    exact_keys(net_losses, ["widening", "tightening"], "net_losses")
    charge, details = _select_scenario(gross_losses, net_losses, tie_break)
    return charge, {**details, "valuation_reference": valuation_reference,
                    "valuation_status": "EXTERNAL_UNVERIFIED",
                    "scope": "credit_derivative_selected_gross_charge_not_valuation_or_hedge_approval"}


@calculation("DR:article-174")
def property_value_stress(property_value: float, *, valuation_reference: str, context: Context):
    """Stress an externally identified property asset, not total BOF or property SCR."""
    require(isinstance(valuation_reference, str) and bool(valuation_reference.strip()),
            "valuation_reference", "external property valuation reference required", "MISSING_INPUT")
    value = number(property_value, "property_value", 0)
    shock = number(scalar("property", context), "property_shock", 0, 1)
    return value * (1 - shock), {"base_value": value, "relative_shock": shock,
                                "valuation_reference": valuation_reference, "valuation_status": "EXTERNAL_UNVERIFIED",
                                "scope": "property_asset_value_only_not_capital"}


@calculation("DR:article-179:1-2", unit="annual_rate")
def credit_spread_stress(spread: float, direction: str, *, category: str, qualification_reference: str,
                         credit_quality_step: str | None = None, context: Context):
    """Absolute widening versus relative tightening; hedge exclusions require separate assessment."""
    require(direction in ("widening", "tightening"), "direction", "widening or tightening required")
    require(category in ("rated", "unrated"), "category", "rated or unrated required", "UNSUPPORTED_METHOD")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external underlying/rating/scope reference required", "MISSING_INPUT")
    base = number(spread, "spread")
    if category == "rated":
        rows = dict(effective_resource("profile.json", context)["tables"]["credit_spread_widening"]["rows"])
        require(isinstance(credit_quality_step, str) and credit_quality_step in rows,
                "credit_quality_step", "explicit CQS0 through6 required")
        widening = number(rows[credit_quality_step], "widening", 0)
    else:
        require(credit_quality_step is None, "credit_quality_step", "omit unused CQS for unrated")
        widening = number(scalar("credit_spread_unrated_widening", context), "widening", 0)
    tightening = number(scalar("credit_spread_tightening", context), "tightening", 0, 1)
    stressed = base + widening if direction == "widening" else base * (1 - tightening)
    return stressed, {"base_spread": base, "direction": direction, "category": category,
                       "credit_quality_step": credit_quality_step, "absolute_widening": widening,
                       "relative_tightening": tightening, "qualification_reference": qualification_reference,
                       "qualification_status": "EXTERNAL_UNVERIFIED",
                       "scope": "underlying_spread_scenario_only_not_derivative_valuation"}


@calculation("DR:article-166", "DR:article-167", unit="annual_rate")
def interest_stress(rate: float, maturity: float, direction: str, *, context: Context):
    """Stress a basic annual spot rate; linear factor interpolation including endpoints."""
    rate = number(rate, "rate", -1)
    require(rate > -1, "rate", "annual discount rate must exceed -1")
    maturity = number(maturity, "maturity", 0)
    require(direction in {"up", "down"}, "direction", "up or down required")
    rows = effective_resource("profile.json", context)["tables"]["interest"]["rows"]
    column = 1 if direction == "up" else 2
    factor = rows[-1][column]
    if maturity <= rows[0][0]:
        factor = rows[0][column]
    else:
        for lo, hi in zip(rows, rows[1:]):
            if lo[0] <= maturity <= hi[0]:
                weight = (maturity - lo[0]) / (hi[0] - lo[0])
                factor = lo[column] + weight * (hi[column] - lo[column])
                break
    if direction == "up":
        value = rate + max(rate * factor, scalar("interest_up_floor", context))
    else:
        value = rate if rate < 0 else rate * (1 - factor)
    return value, {"relative_factor": factor, "absolute_change": value - rate,
                    "scope": "basic_curve_shock_only"}


@calculation("DR:article-172:2-4", unit="ratio")
def symmetric_adjustment(current_index: float, average_index: float, *, context: Context):
    """Use an externally qualified daily mean; the selected profile determines its window and cap."""
    current_index = number(current_index, "current_index", 0)
    average_index = number(average_index, "average_index", 0)
    require(current_index > 0 and average_index > 0, "indices", "positive index levels required")
    raw = scalar("sa_scale", context) * ((current_index - average_index) / average_index
                                         - scalar("sa_offset", context))
    limit = number(scalar("sa_limit", context), "sa_limit", 0)
    months = number(scalar("sa_window_months", context), "sa_window_months", 1)
    require(months.is_integer(), "sa_window_months", "whole months required")
    return max(-limit, min(limit, raw)), {"uncapped_adjustment": raw,
        "adjustment_limit": limit, "required_average_window_months": int(months),
        "average_qualification": "EXTERNAL_INPUT_ONLY",
        "average_method": "equal_weight_daily_index_excluding_days_without_index"}


@calculation(unit="ratio")
def equity_shock(category: str, symmetric_adjustment: float, *,
                 duration_based: Mapping | None = None, context: Context,
                 classification: Mapping | None = None):
    """Shock factor with optional qualified168 route checks, never asset valuation.

    Without classification, eligibility remains external. Optional route inputs
    bind market/fund scope or existing qualification screens to the chosen factor.
    Strategic/long-term recognition and own-funds deductions remain separate.
    """
    sa = number(symmetric_adjustment, "symmetric_adjustment",
                -scalar("sa_limit", context), scalar("sa_limit", context))
    from .equity_classification import equity_classification
    classification_audit, classification_sources = equity_classification(category, classification, context)
    if duration_based is not None:
        value, details = duration_equity_factor(category, sa, duration_based, context)
        details["classification"] = classification_audit
        details["_sources"].extend(classification_sources)
        return value, details
    rows = {row[0]: row[1:] for row in effective_resource("profile.json", context)["tables"]["equity"]["rows"]}
    require(category in rows, "category", "unknown/unimplemented equity category", "UNSUPPORTED_METHOD")
    base, weight = rows[category]
    return base + weight * sa, {"base_shock": base, "sa_weight": weight,
                                "classification": classification_audit,
                                "_sources": ["DR:article-169", *classification_sources],
                                "eligibility_support": "EXTERNAL_INPUT_ONLY",
                                "scope": "factor_only_not_position_valuation_or_short_position_treatment"}


@calculation("DR:article-142:2-3", unit="probability")
def lapse_stress(rate: float, direction: str, *, context: Context):
    """Stress the relevant option-exercise rate after the required contract selection."""
    value = _lapse_rate(rate, direction, scalar("lapse_relative", context), scalar("lapse_down_cap", context))
    return value, {"direction": direction, "scope": "selected_contract_rate_only"}


def _lapse_rate(rate, direction, relative, cap):
    """Shared arithmetic only; callers bind their own legal sources and parameters."""
    rate = number(rate, "rate", 0, 1)
    require(direction in ("up", "down"), "direction", "up or down required")
    relative = number(relative, "lapse_relative", 0, 1)
    if direction == "up":
        value = min(1, rate * (1 + relative))
    else:
        cap = number(cap, "lapse_down_cap", 0, 1)
        value = rate - min(rate * relative, cap)
    return value
