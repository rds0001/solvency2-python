"""Regulatory rate components, not official curves or market-data qualification."""
import math
import sys
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar


def _reference(reference):
    require(isinstance(reference, str) and bool(reference.strip()),
            "qualification_reference", "external input qualification reference required", "MISSING_INPUT")


@calculation("DR:article-48:2", unit="rate")
def rfr_currency_risk_adjustment(*, qualification_reference: str, context: Context,
                                 calibration: Mapping | None = None):
    """Signed CURA: archived uniform value or a qualified formula illustration.

    EIOPA-BoS-24-533 8.3.2 / EIOPA-BoS-26-198 7.3.2. A company's formula
    result is NOT the uniform adjustment published for all undertakings.
    Qualification includes Article48(1), currency/date and input convention.
    In particular, lac_ratio is the source ratio, not a negative LAC amount.
    """
    _reference(qualification_reference)
    require(context.currency != "EUR", "currency", "CURA requires a qualified currency pegged to EUR")
    future = context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1"
    source = "SRC-0211:7.2-7.4:PDF30-31" if future else "SRC-0205:8.2-8.4:PDF41-43"
    details = {"qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
               "method_source": source, "currency": context.currency, "sign_convention": "signed_nonpositive_rate"}
    if calibration is None:
        currencies = {"DKK"} if future else {"DKK", "BGN"}
        require(context.currency in currencies, "currency", "no published CURA in this archived methodology",
                "UNSUPPORTED_METHOD")
        value = number(scalar("rfr_cura_" + context.currency.lower(), context), "published_cura", maximum=0)
        return value, {**details, "scope": "archived_uniform_cura_not_current_currency_status"}
    keys = ("factor", "best_estimate", "scr_zero", "lac_ratio", "modified_duration", "risk_margin", "technical_provisions")
    require(isinstance(calibration, Mapping), "calibration", "explicit formula-input mapping required")
    exact_keys(calibration, keys, "calibration")
    inputs = {key: number(calibration[key], "calibration." + key) for key in keys}
    number(inputs["factor"], "factor", 0, 1)
    number(inputs["risk_margin"], "risk_margin", 0)
    for key in ("scr_zero", "modified_duration", "technical_provisions"):
        require(inputs[key] > 0, key, "positive identifiable formula denominator required", "REVIEW_REQUIRED")
    f, be, scr, lac, duration, rm, tp = (Fraction(str(inputs[key])) for key in keys)
    raw = -f * be / scr * lac / duration * rm / tp
    require(raw <= 0, "calibration", "positive CURA conflicts with Article48; no implicit LAC sign conversion",
            "REVIEW_REQUIRED")
    try:
        value = float(raw)
    except OverflowError:
        require(False, "calibration", "CURA not representable", "REVIEW_REQUIRED")
    return value, {**details, "inputs": inputs, "scope": "formula_component_not_official_uniform_calibration"}


@calculation("DR:article-44:1", "DR:article-48:2", unit="rate")
def rfr_market_rate_adjustment(market_rate: float, credit_adjustment: float, currency_adjustment: float, *,
                                qualification_reference: str, context: Context):
    """Apply CRA and signed CURA once before existing curve construction.

    Positive CRA is subtracted; nonpositive CURA is added. No zero floor.
    Inputs must refer to the same qualified market instrument/tenor/date;
    this is not a shift to an already extrapolated curve or a VA/MA operation.
    """
    _reference(qualification_reference)
    market = number(market_rate, "market_rate")
    credit = number(credit_adjustment, "credit_adjustment", 0)
    currency = number(currency_adjustment, "currency_adjustment", maximum=0)
    raw = Fraction(str(market)) - Fraction(str(credit)) + Fraction(str(currency))
    try:
        value = float(raw)
    except OverflowError:
        require(False, "market_rate", "adjusted rate not representable", "REVIEW_REQUIRED")
    return value, {"market_rate": market, "credit_adjustment": credit, "currency_adjustment": currency,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "market_instrument_rate_before_curve_construction", "zero_floor_applied": False}


@calculation("DR:article-53:1", "DR:article-54:2")
def rfr_default_adjusted_cashflow(cashflow: float, default_probability: float, *,
                                   qualification_reference: str, context: Context):
    """De-risk one asset cashflow under EIOPA-BoS-24-533 section 12.5.9.

    The probability must match this cashflow's horizon; it is not a credit
    spread. Do not apply this twice to already adjusted cashflows. This does
    not project cashflows, select eligible assets or authorize matching.
    """
    _reference(qualification_reference)
    amount = number(cashflow, "cashflow", 0)
    probability = number(default_probability, "default_probability", 0, 1)
    recovery = number(scalar("rfr_fs_recovery_fraction", context), "recovery_fraction", 0, 1)
    factor = math.fsum([1 - probability, recovery * probability])
    return amount * factor, {
        "cashflow": amount, "default_probability": probability,
        "recovery_fraction": recovery, "adjustment_factor": factor,
        "method_source": "SRC-0205:12.5.9:PDF78",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "single_asset_cashflow_derisking_not_projection_or_ma_approval"}


@calculation("DR:article-53:2", unit="rate")
def rfr_fundamental_spread_other_than_pd(fundamental_spread: float, default_spread: float,
                                         downgrade_spread: float, *,
                                         qualification_reference: str, context: Context):
    """Published corporate residual-FS rule: max(CoD, FS-PD), decimal rates.

    Requires matching externally qualified sector/CQS/tenor inputs. Not an
    automatic residual selection for every possible matching portfolio.
    """
    _reference(qualification_reference)
    fs = number(fundamental_spread, "fundamental_spread", 0)
    pd = number(default_spread, "default_spread", 0)
    cod = number(downgrade_spread, "downgrade_spread", 0)
    return max(cod, fs - pd), {
        "fundamental_spread": fs, "default_spread": pd, "downgrade_spread": cod,
        "spread_difference": fs - pd, "unit": "decimal_rate",
        "method_source": "SRC-0245:PD_CoD:EUR!AN6/AN46;SRC-0205:12.4.7",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "corporate_fs_other_than_pd_not_automatic_ma_residual_qualification"}


@calculation("DR:article-45", unit="rate")
def rfr_credit_risk_adjustment(annual_mean_spread: float, *,
                               qualification_reference: str, context: Context):
    """Bound half the externally qualified one-year mean spread (decimal rates).

    The mean's observation calendar, market quality and maturity matching are
    external inputs. This component does not bootstrap or extrapolate a curve.
    Under the 2027 Article44 rule this arithmetic is only for qualified non-OIS
    swaps requiring adjustment; the external reference must establish that scope.
    """
    _reference(qualification_reference)
    mean = number(annual_mean_spread, "annual_mean_spread")
    multiplier = number(scalar("rfr_cra_multiplier", context), "multiplier", 0)
    floor = number(scalar("rfr_cra_floor", context), "floor", 0)
    cap = number(scalar("rfr_cra_cap", context), "cap", 0)
    require(floor <= cap, "cra_bounds", "floor must not exceed cap")
    raw = number(mean * multiplier, "unbounded_adjustment")
    return min(cap, max(floor, raw)), {
        "annual_mean_spread": mean, "multiplier": multiplier,
        "floor": floor, "cap": cap, "unbounded_adjustment": raw,
        "unit": "decimal_rate", "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "credit_adjustment_only_not_official_risk_free_curve"}


@calculation("DR:article-50", unit="rate")
def rfr_reference_portfolio_spread(government_weight: float, corporate_weight: float,
                                   government_spread: float, corporate_spread: float, *,
                                   qualification_reference: str, context: Context):
    """Whole-portfolio weights: do not renormalize the two bond categories."""
    _reference(qualification_reference)
    wg = number(government_weight, "government_weight", 0, 1)
    wc = number(corporate_weight, "corporate_weight", 0, 1)
    require(math.fsum([wg, wc]) <= 1, "weights", "whole-portfolio weights must sum to at most one")
    sg = number(government_spread, "government_spread")
    sc = number(corporate_spread, "corporate_spread")
    government = wg * max(sg, 0)
    corporate = wc * max(sc, 0)
    return math.fsum([government, corporate]), {
        "government_contribution": government, "corporate_contribution": corporate,
        "other_asset_weight": 1 - math.fsum([wg, wc]), "unit": "decimal_rate",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "reference_portfolio_spread_not_official_va"}


@calculation("DR:article-51", unit="rate")
def rfr_portfolio_risk_correction(government_weight: float, corporate_weight: float,
                                  government_risk_correction: float | None,
                                  corporate_risk_correction: float | None, *,
                                  qualification_reference: str, context: Context,
                                  fundamental_spread_inputs: Mapping | None = None):
    """Aggregate category corrections under EIOPA-BoS-24-533 section 10.3.5.

    Weights refer to the whole reference portfolio, not just bonds. Category
    corrections and classifications remain externally qualified inputs. This
    published positive-part formula is distinct from calibrating each input.
    """
    _reference(qualification_reference)
    wg = number(government_weight, "government_weight", 0, 1)
    wc = number(corporate_weight, "corporate_weight", 0, 1)
    require(math.fsum([wg, wc]) <= 1, "weights", "whole-portfolio weights must sum to at most one")
    derivations = {}
    if fundamental_spread_inputs is not None:
        require(government_risk_correction is None and corporate_risk_correction is None,
                "risk_corrections", "omit direct category inputs when deriving from fundamental spread")
        exact_keys(fundamental_spread_inputs, ("government", "corporate"), "fundamental_spread_inputs")
        for category, inputs in fundamental_spread_inputs.items():
            exact_keys(inputs, ("long_term_average_spread", "asset_class", "default_statistics_reliable",
                                "default_spread", "downgrade_spread"), category)
            if category == "corporate":
                require(inputs["asset_class"] == "other", "corporate.asset_class", "corporate inputs cannot use government floor")
            derivations[category] = rfr_fundamental_spread(
                **inputs, qualification_reference=qualification_reference, context=context)
        government_risk_correction = derivations["government"].value
        corporate_risk_correction = derivations["corporate"].value
    rg = number(government_risk_correction, "government_risk_correction")
    rc = number(corporate_risk_correction, "corporate_risk_correction")
    government = wg * max(rg, 0)
    corporate = wc * max(rc, 0)
    return math.fsum([government, corporate]), {
        "government_contribution": government, "corporate_contribution": corporate,
        "government_risk_correction": rg, "corporate_risk_correction": rc,
        "category_derivations": {key: result.to_dict() for key, result in derivations.items()},
        "category_method_status": "FUNDAMENTAL_SPREAD_METHOD" if derivations else "EXTERNAL_CATEGORY_INPUTS",
        "other_asset_weight": 1 - math.fsum([wg, wc]), "unit": "decimal_rate",
        "method_source": "SRC-0205:10.3.5:PDF58-59",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "portfolio_risk_correction_not_market_credit_estimation_or_official_va",
        "_sources": ["SRC-0205:12.1.1-3"] if derivations else []}


@calculation("DIR:article-77d:3", "DR:article-51", unit="rate")
def rfr_risk_corrected_spread(spread: float, risk_correction: float, *,
                             qualification_reference: str, context: Context):
    """Subtract an externally qualified risk correction without an output floor."""
    _reference(qualification_reference)
    spread = number(spread, "spread", 0)
    correction = number(risk_correction, "risk_correction", 0)
    return spread - correction, {
        "spread": spread, "risk_correction": correction, "unit": "decimal_rate",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "risk_corrected_spread_not_risk_correction_derivation"}


@calculation("DIR:article-77d:3-4", unit="rate")
def rfr_volatility_adjustment(currency_spread: float, country_applicable: bool, *,
                               country_spread: float | None = None,
                               qualification_reference: str, context: Context):
    """Compute VA from risk-corrected spreads; neither authorize nor apply it.

    Country uplift is added BEFORE the factor and requires both strict tests.
    Official data, MA exclusion and pre-extrapolation application remain external.
    """
    _reference(qualification_reference)
    currency = number(currency_spread, "currency_spread")
    require(isinstance(country_applicable, bool), "country_applicable", "explicit boolean required")
    factor = number(scalar("rfr_va_factor", context), "factor", 0, 1)
    multiplier = number(scalar("rfr_va_currency_multiplier", context), "currency_multiplier", 0)
    require(multiplier > 0, "currency_multiplier", "positive multiplier required")
    threshold = number(scalar("rfr_va_country_threshold", context), "country_threshold", 0)
    country, difference, increase = None, None, 0.0
    if country_applicable:
        country = number(country_spread, "country_spread")
        difference = number(country - multiplier * currency, "country_difference")
        if difference > 0 and country > threshold:
            increase = difference
    else:
        require(country_spread is None, "country_spread", "country input not allowed when country branch is disabled")
    return factor * number(currency + increase, "adjusted_spread"), {
        "currency_spread": currency, "country_spread": country,
        "country_applicable": country_applicable, "country_difference": difference,
        "country_increase": increase, "factor": factor, "currency_multiplier": multiplier,
        "country_threshold": threshold, "unit": "decimal_rate",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "va_component_not_official_data_or_curve_application"}


@calculation("DR:article-54:4", "DIR:article-77c:2:a:ii")
def rfr_downgrade_expected_loss(scenarios: Mapping, *, qualification_reference: str, context: Context):
    """Weight qualified immediate replacement losses, not a rating/migration model.

    Distinct downgrade states share a horizon and valuation basis. Residual
    probability is no downgrade, with no downgrade loss; never renormalize.
    The result is a currency amount, NOT a spread or a market-value percentage.
    """
    _reference(qualification_reference)
    require(isinstance(scenarios, Mapping) and bool(scenarios), "scenarios", "explicit downgrade scenarios required", "MISSING_INPUT")
    from .rfr_ma_controls import _conditions
    fields = ("downgrade_event", "immediate_replacement", "same_cashflow_pattern", "same_asset_class",
              "replacement_quality_at_least_pre_downgrade")
    probability, loss, audit = Fraction(0), Fraction(0), {}
    for label, row in scenarios.items():
        require(isinstance(label, str) and bool(label.strip()), "scenario_id", "nonempty scenario ID required")
        exact_keys(row, ("probability", "replacement_loss", "conditions"), label)
        pd = number(row["probability"], label + ".probability", 0, 1)
        amount = number(row["replacement_loss"], label + ".replacement_loss")
        flags = _conditions(row["conditions"], fields)
        weight = Fraction(str(pd))
        probability += weight
        loss += weight * Fraction(str(amount))
        audit[label] = {"probability": pd, "replacement_loss": amount, "conditions": flags}
    require(probability <= 1, "scenarios", "distinct downgrade-state probabilities exceed one")
    return float(loss), {"scenarios": audit, "downgrade_probability_sum": float(probability),
        "residual_no_downgrade_probability": float(1 - probability),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scenario_exclusivity_or_valuation_verified": False, "replacement_valuation_performed": False,
        "scope": "probability_weighted_replacement_loss_not_credit_spread_or_rating_model"}


@calculation("DIR:article-77c:2", unit="rate")
def rfr_fundamental_spread(long_term_average_spread: float, asset_class: str,
                            default_statistics_reliable: bool, *,
                            default_spread: float | None = None,
                            downgrade_spread: float | None = None,
                            qualification_reference: str, context: Context):
    """Compose external credit spreads with the class floor or exact fallback.

    eu_central means EU member-state central governments/central banks, not
    all public-sector entities. Statistics and 30-year history qualification
    remain external; this does not derive PDs or downgrade replacement losses.
    """
    _reference(qualification_reference)
    require(isinstance(asset_class, str) and asset_class in {"eu_central", "other"},
            "asset_class", "eu_central or other required")
    require(isinstance(default_statistics_reliable, bool), "default_statistics_reliable",
            "explicit externally qualified reliability decision required")
    average = number(long_term_average_spread, "long_term_average_spread")
    fraction = number(scalar("rfr_fs_floor_" + asset_class, context), "floor_fraction", 0, 1)
    floor = number(average * fraction, "long_term_floor")
    default, downgrade, component_sum = None, None, None
    if default_statistics_reliable:
        default = number(default_spread, "default_spread", 0)
        downgrade = number(downgrade_spread, "downgrade_spread", 0)
        component_sum = number(math.fsum([default, downgrade]), "component_sum", 0)
        value = max(component_sum, floor)
    else:
        require(default_spread is None and downgrade_spread is None, "credit_components",
                "omit both components when using the unreliable-statistics fallback")
        value = floor
    return value, {
        "asset_class": asset_class, "long_term_average_spread": average,
        "floor_fraction": fraction, "long_term_floor": floor,
        "default_statistics_reliable": default_statistics_reliable,
        "default_spread": default, "downgrade_spread": downgrade,
        "component_sum": component_sum, "fallback_used": not default_statistics_reliable,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "unit": "decimal_rate", "scope": "fundamental_spread_composition_not_official_data_or_ma"}


@calculation("DIR:article-77c:1:a-b", "DR:article-53:2", unit="rate")
def rfr_matching_adjustment(asset_equivalent_rate: float, liability_equivalent_rate: float,
                             residual_fundamental_spread: float, *,
                             qualification_reference: str, context: Context,
                             application: Mapping | None = None, restructured_assets: Mapping | None = None,
                             subinvestment_grade_comparison: Mapping | None = None):
    """Subtract effective annual rates on the SAME liability cashflows and residual FS.

    The asset-equivalent rate matches their PV to eligible assigned asset value;
    the liability-equivalent rate matches their PV to the basic-curve BE.
    The residual FS excludes any part already included in asset cashflow
    adjustment. Optional declared application/asset comparisons add controlled
    eligibility and FS limits; without them these aspects stay NOT_ASSESSED.
    No asset coupon substitution, automatic rating, permission or curve application.
    """
    _reference(qualification_reference)
    asset = number(asset_equivalent_rate, "asset_equivalent_rate")
    liability = number(liability_equivalent_rate, "liability_equivalent_rate")
    require(asset > -1, "asset_equivalent_rate", "effective annual rate must exceed -1")
    require(liability > -1, "liability_equivalent_rate", "effective annual rate must exceed -1")
    residual = number(residual_fundamental_spread, "residual_fundamental_spread")
    raw = math.fsum([asset, -liability, -residual])
    from .rfr_ma_controls import apply_subinvestment_comparison, check_matching_application
    value, comparison = apply_subinvestment_comparison(raw, residual, subinvestment_grade_comparison)
    controls = check_matching_application(application, restructured_assets, value, qualification_reference, context)
    if subinvestment_grade_comparison is not None:
        controls["_sources"].append("DIR:article-77c:1:c")
    return value, {**controls, **comparison, "unconstrained_matching_adjustment": raw,
        "asset_equivalent_rate": asset, "liability_equivalent_rate": liability,
        "residual_fundamental_spread": residual, "unit": "decimal_rate",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "ma_rate_difference_with_external_residual_fs_not_full_ma"}


@calculation("DIR:article-77c:1:a", unit="rate")
def rfr_equivalent_annual_rate(cashflows: Mapping, present_value: float, *,
                               qualification_reference: str, context: Context):
    """Solve the unique annual rate for nonnegative externally qualified cashflows.

    Times are supplied year fractions, not an implicit day-count convention.
    Mixed signs need external review because uniqueness is not guaranteed.
    Numerical tolerances below are implementation choices, not legal parameters.
    """
    _reference(qualification_reference)
    require(isinstance(cashflows, Mapping) and bool(cashflows), "cashflows", "nonempty mapping required")
    require(all(isinstance(key, str) and key.strip() for key in cashflows),
            "cashflows", "nonempty string IDs required")
    target = number(present_value, "present_value", 0)
    future, immediate = [], []
    for key, row in cashflows.items():
        exact_keys(row, ["amount", "time_years"], key)
        amount = number(row["amount"], key + ".amount")
        require(amount >= 0, key + ".amount", "mixed-sign cashflows require external root review", "REVIEW_REQUIRED")
        time = number(row["time_years"], key + ".time_years", 0)
        if time == 0:
            immediate.append(amount)
        elif amount > 0:
            future.append((math.log(amount), time))
    require(bool(future), "cashflows", "positive future cashflow required for a unique rate", "REVIEW_REQUIRED")
    immediate_value = math.fsum(immediate)
    future_target = number(target - immediate_value, "future_target")
    require(future_target > 0, "present_value", "target must exceed immediate cashflows", "REVIEW_REQUIRED")
    log_target = math.log(future_target)

    def log_error(log_rate):
        # Log-sum-exp avoids overflow for ordinary large/small currency units.
        terms = [log_amount - time * log_rate for log_amount, time in future]
        largest = max(terms)
        if not math.isfinite(largest):
            return largest
        return largest + math.log(math.fsum(math.exp(term - largest) for term in terms)) - log_target

    low = math.log1p(math.nextafter(-1.0, 0.0))
    high = math.log(sys.float_info.max)
    require(log_error(low) >= 0 and log_error(high) <= 0, "rate",
            "root lies outside representable annual rates", "REVIEW_REQUIRED")
    candidate, iterations = 0.0, 0
    # An exact zero-rate solution is common and avoids gratuitous rounding.
    if abs(log_error(0.0)) > 1e-13:
        for iterations in range(1, 257):
            candidate = low + (high - low) / 2
            error = log_error(candidate)
            if abs(error) <= 1e-13 or candidate == low or candidate == high:
                break
            if error > 0:
                low = candidate
            else:
                high = candidate
    rate = math.expm1(candidate)
    require(math.isfinite(rate) and rate > -1, "rate", "annual rate not representable", "REVIEW_REQUIRED")
    final_error = log_error(math.log1p(rate))
    require(abs(final_error) <= math.log1p(1e-10), "rate",
            "representable rate does not meet PV residual tolerance", "REVIEW_REQUIRED")
    return rate, {
        "present_value": target, "immediate_value": immediate_value, "future_target": future_target,
        "future_cashflow_count": len(future), "method": "log_rate_bisection_monotone_nonnegative_cashflows",
        "iterations": iterations, "relative_future_pv_residual": math.expm1(final_error),
        "numerical_tolerance": 1e-10, "unit": "effective_annual_decimal_rate",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "equivalent_rate_only_not_cashflow_projection_or_ma_approval"}


@calculation("DR:article-52:1-3", unit="rate")
def rfr_matching_mortality_stress(rate: float, scenario: str, *, rate_basis: str,
                                   selected: bool | None, qualification_reference: str, context: Context):
    """MA qualification stress assumption, not life SCR or automatic scenario selection."""
    _reference(qualification_reference)
    require(isinstance(scenario, str) and scenario in {"permanent", "next_twelve_months"},
            "scenario", "supported MA mortality scenario required")
    require(rate_basis in ("probability", "intensity"), "rate_basis", "explicit rate basis required")
    require(scenario != "next_twelve_months" or rate_basis == "probability", "rate_basis",
            "absolute twelve-month shock requires probability input", "UNSUPPORTED_METHOD")
    require(selected is None or isinstance(selected, bool), "selected", "boolean or None required")
    require(selected is not None, "selected", "contract selection unresolved", "REVIEW_REQUIRED")
    base = number(rate, "rate", 0, 1 if rate_basis == "probability" else None)
    key = "rfr_ma_mortality_relative" if scenario == "permanent" else "rfr_ma_mortality_absolute"
    change = number(scalar(key, context), key, 0)
    stressed = base
    if selected:
        stressed = base * (1 + change) if scenario == "permanent" else base + change
    stressed = number(stressed, "stressed_rate", 0)
    require(rate_basis != "probability" or stressed <= 1, "stressed_rate",
            "stress exceeds probability range; no cap specified", "REVIEW_REQUIRED")
    return stressed, {
        "base_rate": base, "scenario": scenario, "rate_basis": rate_basis, "selected": selected,
        "change": change, "parameter_id": "scalars/" + key,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "ma_mortality_assumption_not_bof_scenario_selection_or_ma_eligibility"}


@calculation("DR:article-54:2")
def rfr_default_loss_on_market_value(market_value: float, *,
                                      qualification_reference: str, context: Context):
    """Loss conditional on default under the fundamental-spread recovery assumption."""
    _reference(qualification_reference)
    value = number(market_value, "market_value", 0)
    recovery = number(scalar("rfr_fs_recovery_fraction", context), "recovery_fraction", 0, 1)
    return value * (1 - recovery), {
        "market_value": value, "recovery_fraction": recovery, "recovered_value": value * recovery,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "conditional_default_loss_not_pd_weighted_loss_or_credit_spread"}


@calculation("DIR:article-77b:1:f")
def rfr_matching_mortality_headroom(base_best_estimate: float, stressed_best_estimate: float, *,
                                    qualification_reference: str, context: Context):
    """Headroom against the 5% BE condition, using the externally BOF-selected stress.

    Nonnegative means this numerical condition passes, not overall MA eligibility.
    Nonpositive base BE is deliberately referred for review, not reinterpreted.
    """
    _reference(qualification_reference)
    base = number(base_best_estimate, "base_best_estimate")
    require(base > 0, "base_best_estimate", "nonpositive BE requires percentage-condition review", "REVIEW_REQUIRED")
    stressed = number(stressed_best_estimate, "stressed_best_estimate")
    fraction = number(scalar("rfr_ma_mortality_be_limit", context), "be_limit", 0)
    allowance = number(base * fraction, "allowance", 0)
    increase = number(stressed - base, "be_increase")
    headroom = number(allowance - increase, "headroom")
    return headroom, {
        "base_best_estimate": base, "stressed_best_estimate": stressed,
        "be_increase": increase, "limit_fraction": fraction, "allowance": allowance,
        "quantitative_condition_met": headroom >= 0,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "ma_mortality_be_condition_only_not_overall_ma_eligibility"}


@calculation("DR:article-52:1")
def rfr_matching_mortality_selected_be(scenarios: Mapping, *,
                                        selected_scenario: str | None = None,
                                        qualification_reference: str, context: Context,
                                        contract_selection: Mapping | None = None):
    """Return BE from the worst BOF scenario, not the scenario with maximum BE.

    Scenario valuations must share a base and currency. Equal BOF with distinct
    BE values requires explicit selection among the ties; there is no legal
    worst-BE tie rule invented here. Valuation and overall eligibility stay external.
    """
    _reference(qualification_reference)
    from .rfr_ma_controls import check_mortality_contract_selection
    selection_audit = check_mortality_contract_selection(contract_selection)
    exact_keys(scenarios, ["permanent", "next_twelve_months"], "scenarios")
    rows = {}
    for key, row in scenarios.items():
        exact_keys(row, ["basic_own_funds", "best_estimate"], key)
        rows[key] = {field: number(row[field], key + "." + field)
                     for field in ("basic_own_funds", "best_estimate")}
    lowest = min(row["basic_own_funds"] for row in rows.values())
    tied = sorted(key for key, row in rows.items() if row["basic_own_funds"] == lowest)
    if selected_scenario is not None:
        require(isinstance(selected_scenario, str) and selected_scenario in tied,
                "selected_scenario", "selection must be among the worst BOF scenarios")
        selected = selected_scenario
    else:
        require(len({rows[key]["best_estimate"] for key in tied}) == 1, "selected_scenario",
                "equal BOF with distinct BE requires explicit tied-scenario selection", "REVIEW_REQUIRED")
        selected = tied[0]
    return rows[selected]["best_estimate"], {
        **selection_audit,
        "scenarios": rows, "selected_scenario": selected, "tied_scenarios": tied,
        "explicit_selection": selected_scenario is not None, "selection_rule": "MIN_STRESSED_BASIC_OWN_FUNDS",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "external_scenario_selection_not_projection_or_ma_approval"}


@calculation("DR:article-37:1", unit="ratio")
def rfr_spot_discount_factor(spot_rate: float, time_years: float, *,
                              qualification_reference: str, context: Context):
    """Convert a matching annual zero-coupon spot rate to a discount factor.

    Year fractions and curve qualification are explicit external inputs; this
    performs no interpolation, day-count choice or VA/MA eligibility decision.
    """
    _reference(qualification_reference)
    rate = number(spot_rate, "spot_rate")
    require(rate > -1, "spot_rate", "annual spot rate must exceed -1")
    time = number(time_years, "time_years", 0)
    factor = math.exp(-time * math.log1p(rate))
    require(factor > 0, "discount_factor", "positive discount factor underflows numeric range", "REVIEW_REQUIRED")
    return factor, {"spot_rate": rate, "time_years": time,
        "compounding": "ANNUAL_ZERO_COUPON", "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "discount_factor_only_not_curve_interpolation_or_cashflow_projection"}
