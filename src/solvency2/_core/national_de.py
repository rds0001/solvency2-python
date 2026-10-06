"""Explicit archived German overlays; never inferred from an EU rule profile.

Sources determine arithmetic and evidence scope, not insurer-specific facts or
automatic current national applicability. No permissions or filings are issued.
"""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory, _reference


def _national_reference(version, expected, reference):
    require(version == expected, "source_version", "explicit archived national version required", "UNSUPPORTED_RULESET")
    _reference(reference, "applicability_reference")


@calculation("DE_VAG:2026-03-25:125:2;126:2;127:1", unit="EUR")
def de_cover_assets_minimum(components: Mapping, *, source_version: str,
                            applicability_reference: str, current_cover_assets: float | None = None,
                            foreign_security_exception: float = 0,
                            foreign_security_reference: str | None = None, context: Context):
    """German book-value cover pool minimum, distinct from Solvency-II TP.

    Gross direct-insurance figures precede reinsurance deductions. Eligible
    current pool value must already reflect the separate Article126 rules.
    Extra supervisory requirements under127(2) are not inferred here.
    """
    _national_reference(source_version, "2026-03-25", applicability_reference)
    require(context.currency == "EUR", "currency", "EUR book values required", "UNSUPPORTED_CURRENCY")
    keys = ("unearned_premiums", "mathematical_provision", "outstanding_claims_and_repurchases",
            "non_profit_related_refunds", "dormant_unused_premiums", "allocated_undistributed_profit_shares",
            "direct_policyholder_liabilities", "refundable_received_premiums")
    exact_keys(components, keys, "components")
    values = {key: number(components[key], key, 0) for key in keys}
    minimum = number(math.fsum(values.values()), "minimum", 0)
    exempt = number(foreign_security_exception, "foreign_security_exception", 0)
    if exempt:
        _reference(foreign_security_reference, "foreign_security_reference")
    else:
        require(foreign_security_reference is None, "foreign_security_reference", "unused exception reference")
    if current_cover_assets is None:
        require(exempt == 0, "foreign_security_exception", "current cover pool needed to assess top-up", "MISSING_INPUT")
        current = topup = None
    else:
        current = number(current_cover_assets, "current_cover_assets", 0)
        topup = max(minimum - current - exempt, 0)
    months = number(scalar("de_cover_asset_register_months", context), "de_cover_asset_register_months", 0)
    require(months > 0, "de_cover_asset_register_months", "positive period required")
    return minimum, {"gross_direct_book_components": values, "current_cover_assets": current,
        "statutory_topup_before_additional_supervisory_orders": topup,
        "foreign_security_exception": exempt, "foreign_security_reference": foreign_security_reference,
        "register_reporting_months_after_financial_year_end": months,
        "national_applicability_verified": False, "applicability_reference": applicability_reference,
        "source_version": source_version, "reinsurance_deducted_from_minimum": False,
        "article126_asset_eligibility_verified": False, "supervisory_additional_requirements_assessed": False,
        "scope": "statutory_cover_pool_book_value_minimum_not_solvency_TP_or_total_supervisory_requirement"}


@calculation("DE_VAG:2026-03-25:125:3", unit="EUR")
def de_cover_property_value(book_value: float, market_value: float, *, encumbered: bool,
                            supervisory_value: float | None = None,
                            supervisory_reference: str | None = None,
                            expert_valuation_reference: str | None = None, source_version: str,
                            applicability_reference: str, context: Context):
    """Book/market minimum, or explicitly supervisor-determined property value.

    A doubled market-to-book threshold permits review of an increase; it does
    not prescribe the increase. Encumbered property always needs an external
    supervisory value. Neither value may feed a Solvency-II market valuation
    merely because this separate cover-pool rule accepts it.
    """
    _national_reference(source_version, "2026-03-25", applicability_reference)
    require(context.currency == "EUR", "currency", "EUR property values required", "UNSUPPORTED_CURRENCY")
    book, market = number(book_value, "book_value", 0), number(market_value, "market_value", 0)
    burdened = _declared_bool(encumbered, "encumbered")
    uplift = number(scalar("de_cover_property_market_uplift", context), "de_cover_property_market_uplift", 0)
    if supervisory_value is None:
        require(not burdened, "supervisory_value", "encumbered property requires authority-set value", "REVIEW_REQUIRED")
        require(supervisory_reference is None and expert_valuation_reference is None,
                "references", "unused without externally determined value")
        value = min(book, market)
        method = "LOWER_BOOK_MARKET"
    else:
        value = number(supervisory_value, "supervisory_value", 0)
        _reference(supervisory_reference, "supervisory_reference")
        if not burdened:
            require(book > 0 and market / book >= 1 + uplift, "market_value",
                    "unencumbered uplift threshold not met or zero-book basis unresolved", "REVIEW_REQUIRED")
            require(value >= book, "supervisory_value", "this branch is an authorised increase")
            _reference(expert_valuation_reference, "expert_valuation_reference")
        else:
            require(expert_valuation_reference is None, "expert_valuation_reference", "use supervisory reference for encumbered determination")
        method = "EXTERNAL_SUPERVISORY_VALUE"
    return value, {"book_value": book, "market_value": market, "encumbered": burdened,
        "method": method, "market_uplift_threshold": uplift,
        "supervisory_reference": supervisory_reference, "expert_valuation_reference": expert_valuation_reference,
        "applicability_reference": applicability_reference, "source_version": source_version,
        "national_applicability_verified": False, "supervisory_value_adequacy_verified": False,
        "scope": "German_cover_pool_property_not_solvency_balance_sheet"}


@calculation("DE_VAG:2026-03-25:69:2;69:5;70:1", unit="EUR")
def de_branch_minimum_amount(unadjusted_absolute_floor: float, requirement: str, *,
                             reinsurance_branch: bool, domestic_deposit_relief: bool,
                             relief_reference: str | None = None, source_version: str,
                             applicability_reference: str, context: Context):
    """Calculate a qualified German branch asset minimum or domestic deposit.

    The input is the unhalved applicable AMCR, not the branch MCR. A German
    deposit waiver does not waive the deposit at the chosen supervisory state.
    Asset location, admissibility and any higher actual SCR/MCR stay separate.
    """
    _national_reference(source_version, "2026-03-25", applicability_reference)
    require(context.currency == "EUR", "currency", "EUR floor required", "UNSUPPORTED_CURRENCY")
    amount = number(unadjusted_absolute_floor, "unadjusted_absolute_floor", 0)
    require(amount > 0, "unadjusted_absolute_floor", "positive applicable unhalved floor required")
    require(requirement in ("deposit", "asset_minimum"), "requirement", "deposit or asset_minimum required")
    reinsurer = _declared_bool(reinsurance_branch, "reinsurance_branch")
    relief = _declared_bool(domestic_deposit_relief, "domestic_deposit_relief")
    if relief:
        require(not reinsurer, "domestic_deposit_relief", "reinsurance exemption is69(5), not an assumed70 grant")
        _reference(relief_reference, "relief_reference")
    else:
        require(relief_reference is None, "relief_reference", "unused relief reference")
    key = "de_branch_deposit_fraction" if requirement == "deposit" else "de_branch_asset_minimum_fraction"
    fraction = number(scalar(key, context), key, 0, 1)
    exempt = requirement == "deposit" and (reinsurer or relief)
    return 0 if exempt else amount * fraction, {
        "requirement": requirement, "unadjusted_absolute_floor": amount, "fraction": fraction,
        "reinsurance_branch": reinsurer, "domestic_deposit_relief": relief,
        "relief_reference": relief_reference, "source_version": source_version,
        "applicability_reference": applicability_reference, "national_applicability_verified": False,
        "deposit_added_to_own_funds": False, "asset_location_assessed": False,
        "scope": "minimum_amount_not_authorisation_total_capital_or_global_deposit_waiver"}


@calculation("DE_BAFIN_PPP:05/2025:14", unit="ratio")
def de_liquidity_coverage(gross_inflows: float, gross_outflows: float, realisable_cash: float,
                          total_investments: float, *, source_version: str,
                          applicability_reference: str, horizon_reference: str, context: Context):
    """Coverage, cash-flow gap and liquidity level for one qualified horizon.

    Inflows and cash are disjoint sources; no netting or double counting.
    Projections, liquidation assumptions and scenarios are insurer inputs.
    The circular specifies no universal minimum ratio or fixed time bands.
    """
    _national_reference(source_version, "05/2025", applicability_reference)
    _reference(horizon_reference, "horizon_reference")
    inflows, outflows = number(gross_inflows, "gross_inflows", 0), number(gross_outflows, "gross_outflows", 0)
    cash, assets = number(realisable_cash, "realisable_cash", 0), number(total_investments, "total_investments", 0)
    require(outflows > 0, "gross_outflows", "zero denominator requires separate review", "REVIEW_REQUIRED")
    require(cash <= assets, "realisable_cash", "available investment cash must not exceed total investments")
    sources = number(math.fsum((inflows, cash)), "liquidity_sources", 0)
    return sources / outflows, {
        "cashflow_gap": inflows - outflows, "liquidity_sources": sources,
        "liquidity_level": cash / assets if assets else None,
        "liquidity_level_status": "CALCULATED" if assets else "UNDEFINED_ZERO_INVESTMENTS",
        "horizon_reference": horizon_reference, "source_version": source_version,
        "applicability_reference": applicability_reference, "national_applicability_verified": False,
        "minimum_coverage_ratio_prescribed": False, "projections_verified": False,
        "scope": "qualified_horizon_liquidity_arithmetic_not_liquidity_model"}


def _de_ppp_assessment(assessment: Mapping | None, context: Context):
    if assessment is None:
        return True, {"status": "NOT_ASSESSED"}
    exact_keys(assessment, ("source_version", "applicability_reference", "evidence", "trading_assessment"), "de_ppp")
    _national_reference(assessment["source_version"], "05/2025", assessment["applicability_reference"])
    table = effective_resource("profile.json", context)["tables"]["de_ppp_controls"]
    complete, details = _evidence_inventory(assessment["evidence"], table, assessment["applicability_reference"])
    maximum = number(scalar("de_ppp_price_interval_months", context), "de_ppp_price_interval_months", 0)
    require(maximum > 0, "de_ppp_price_interval_months", "positive interval required")
    trading = assessment["trading_assessment"]
    treatment = {"status": "NOT_ASSESSED", "maximum_price_interval_months": maximum}
    if trading is not None:
        exact_keys(trading, ("listed", "actual_regular_trading", "price_interval_months"), "trading_assessment")
        listed = _declared_bool(trading["listed"], "listed")
        if listed:
            actual = _declared_bool(trading["actual_regular_trading"], "actual_regular_trading")
            interval = number(trading["price_interval_months"], "price_interval_months", 0)
            require(interval > 0, "price_interval_months", "positive observed price interval required")
            required = not actual or interval > maximum
        else:
            require(trading["actual_regular_trading"] is None and trading["price_interval_months"] is None,
                    "trading_assessment", "unused listed-trading facts for unlisted asset")
            required = True
        treatment = {**treatment, "status": "DECLARED_FACT_SCREEN",
            "non_regular_or_unlisted_treatment_required": required,
            "market_maker_quotes_alone_sufficient": False, "facts_verified": False}
    return bool(complete), {**details, "status": "DECLARED_EVIDENCE_INVENTORY",
        "source_version": "05/2025", "national_applicability_verified": False, "trading": treatment,
        "usual_alm_interval_years": number(scalar("de_ppp_usual_alm_interval_years", context), "usual_alm_interval", 0),
        "alm_interval_is_unconditional_maximum": False,
        "usual_eligible_incentive_rfb_fraction": number(scalar("de_ppp_usual_incentive_rfb_fraction", context), "rfb_fraction", 0, 1),
        "rfb_allocation_calculated": False, "internal_investment_limits_prescribed": False}
