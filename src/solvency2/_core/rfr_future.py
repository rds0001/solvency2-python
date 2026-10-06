"""Published 2027 VA arithmetic, never supervisory approval or curve construction."""
import math

from .core import Context, calculation, effective_resource, number, require, scalar


def _pegged_pair(context, currency):
    require(isinstance(currency, str) and len(currency) == 3 and currency.isascii()
            and currency.isalpha() and currency.isupper() and currency != "EUR",
            "pegged_currency", "explicit non-EUR three-letter currency required")
    require(context.currency in ("EUR", currency), "currency",
            "reporting currency must belong to the explicitly qualified pair", "UNSUPPORTED_METHOD")


def _cssr(assets, liabilities):
    # Branch before division, including the explicit nonpositive-BEL exception.
    if liabilities <= 0:
        return 1, "NONPOSITIVE_LIABILITY_PVBP"
    if assets <= 0:
        return 0, "ZERO_FLOOR"
    if assets >= liabilities:
        return 1, "ONE_CAP"
    return assets / liabilities, "RATIO"


def _qualified(context, reference, source, *, euro=False):
    profile = effective_resource("profile.json", context)
    require(profile.get("methods", {}).get("volatility_adjustment") == "VA_2027",
            "profile_id", "2027 VA method required", "UNSUPPORTED_RULESET")
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external input qualification reference required", "MISSING_INPUT")
    if euro:
        require(context.currency == "EUR", "currency", "macro VA is a euro component", "UNSUPPORTED_METHOD")
    instrument, article = source.split(":", 1)
    return {"qualification_reference": reference, "qualification_status": "EXTERNAL_UNVERIFIED",
            "_sources": [context.profile_id + ":" + profile["sources"][instrument]["sha256"] + ":" + article]}


@calculation("DR:article-51:2-3", unit="rate")
def rfr_risk_correction_2027(spread: float, long_term_average_spread: float, asset_class: str, *,
                            qualification_reference: str, context: Context):
    """Piecewise correction for a qualified homogeneous spread bucket, decimal rates.

    EEA sovereign classification, matching duration/quality and 30-year LTAS
    estimation are external. This is not a choice of portfolio-weight denominator.
    """
    details = _qualified(context, qualification_reference, "DR:article-51:2-3")
    require(asset_class in ("eea_government", "other"), "asset_class", "eea_government or other required")
    spread_positive = max(number(spread, "spread"), 0)
    ltas = max(number(long_term_average_spread, "long_term_average_spread"), 0)
    coefficients = {key: number(scalar(f"rfr_rc_{asset_class}_{key}", context), key, 0)
                    for key in ("first", "second", "third", "cap")}
    # Subtraction rather than 2*LTAS avoids overflow for large finite inputs.
    excess = max(spread_positive - ltas, 0)
    bands = (min(spread_positive, ltas), min(excess, ltas), max(excess - ltas, 0))
    uncapped = math.fsum(coefficients[key] * band
                         for key, band in zip(("first", "second", "third"), bands))
    cap = coefficients["cap"] * ltas
    return min(uncapped, cap), {**details, "asset_class": asset_class, "positive_spread": spread_positive,
                              "positive_ltas": ltas, "band_amounts": bands, "coefficients": coefficients,
                              "uncapped": uncapped, "cap": cap, "scope": "qualified_bucket_correction_only"}


@calculation("DR:article-51a:1", unit="ratio")
def rfr_credit_spread_sensitivity(asset_pvbp: float | None, liability_pvbp: float | None, *,
                                  qualification_reference: str, context: Context, reuse: dict | None = None):
    """CSSR from separately qualified PVBP amounts, not their revaluation model."""
    details = _qualified(context, qualification_reference, "DR:article-51a:1")
    if reuse is not None:
        require(asset_pvbp is None and liability_pvbp is None, "reuse", "omit current PVBP when reusing CSSR")
        from .rfr_va_controls import reuse_cssr
        value, reused = reuse_cssr(reuse, context)
        reused["_sources"] = [*details["_sources"], *reused["_sources"]]
        return value, {**details, **reused, "scope": "qualified_single_currency_cssr_reuse_not_revaluation"}
    assets = number(asset_pvbp, "asset_pvbp")
    liabilities = number(liability_pvbp, "liability_pvbp")
    value, branch = _cssr(assets, liabilities)
    return value, {**details, "asset_pvbp": assets, "liability_pvbp": liabilities,
                   "branch": branch, "scope": "single_currency_cssr_from_external_revaluations"}


@calculation("DR:article-51a:2-3", "DR:article-51b:2-3", unit="currency_per_rate")
def rfr_va_pvbp(unadjusted_value: float, adjusted_value: float, notional_va: float, valuation_kind: str, *,
                 qualification_reference: str, context: Context, pegged_currency: str | None = None,
                 pegged_notional_va: float | None = None):
    """Literal revaluation difference/VA*, not a valuation model or per-bp rescaling.

    Qualified asset values exclude immaterial unit-linked spread exposure.
    Qualified BEL includes future discretionary benefits without feeding back
    the asset spread shock. Paired values are already in one reporting currency.
    """
    source = "DR:article-51a:2-3" if pegged_currency is None else "DR:article-51b:2-3"
    details = _qualified(context, qualification_reference, source)
    require(valuation_kind in ("assets", "liabilities"), "valuation_kind", "assets or liabilities required")
    before = number(unadjusted_value, "unadjusted_value")
    after = number(adjusted_value, "adjusted_value")
    notional = number(notional_va, "notional_va")
    if pegged_currency is None:
        require(pegged_notional_va is None, "pegged_notional_va", "unexpected second VA for single currency")
        selected = notional
    else:
        _pegged_pair(context, pegged_currency)
        second = number(pegged_notional_va, "pegged_notional_va")
        selected = max(notional, second)
    require(selected != 0, "notional_va", "zero VA leaves the difference quotient undefined", "REVIEW_REQUIRED")
    value = (before - after) / selected
    return value, {**details, "valuation_kind": valuation_kind, "unadjusted_value": before,
                   "adjusted_value": after, "notional_va": notional, "pegged_currency": pegged_currency,
                   "pegged_notional_va": pegged_notional_va, "selected_notional_va": selected,
                   "scope": "external_revaluation_difference_per_decimal_rate_not_model_approval"}


@calculation("DR:article-51b:1", unit="ratio")
def rfr_pegged_credit_spread_sensitivity(asset_pvbp: float, liability_pvbp: float, pegged_currency: str, *,
                                         qualification_reference: str, context: Context):
    """Common CSSR from qualified combined amounts, never average individual CSSRs.

    Peg eligibility and use of the adjusted euro curve under Article48 are
    external. The currency identifier alone is not evidence of their validity.
    """
    details = _qualified(context, qualification_reference, "DR:article-51b:1")
    _pegged_pair(context, pegged_currency)
    assets = number(asset_pvbp, "asset_pvbp")
    liabilities = number(liability_pvbp, "liability_pvbp")
    value, branch = _cssr(assets, liabilities)
    return value, {**details, "asset_pvbp": assets, "liability_pvbp": liabilities,
                   "pegged_currency": pegged_currency, "branch": branch,
                   "scope": "qualified_combined_euro_pegged_currency_cssr"}


@calculation("DIR:article-77d:3", unit="rate")
def rfr_volatility_adjustment_2027(risk_corrected_spread: float, credit_spread_sensitivity: float, *,
                                   qualification_reference: str, context: Context, firm_adjustment: dict | None = None):
    """Currency VA only; no automatic macro addition or undertaking-specific approval."""
    details = _qualified(context, qualification_reference, "DIR:article-77d:3")
    spread = number(risk_corrected_spread, "risk_corrected_spread")
    cssr = number(credit_spread_sensitivity, "credit_spread_sensitivity", 0, 1)
    ratio = number(scalar("rfr_va_transmission", context), "transmission", 0, 1)
    from .rfr_va_controls import firm_adjusted_spread
    adjusted, firm = firm_adjusted_spread(spread, firm_adjustment, context)
    if "_sources" in firm:
        firm["_sources"] = [*details["_sources"], *firm["_sources"]]
    return ratio * cssr * adjusted, {**details, **firm, "risk_corrected_spread": spread,
                                  "effective_risk_corrected_spread": adjusted,
                                  "credit_spread_sensitivity": cssr, "transmission": ratio,
                                  "scope": "currency_va_only_not_curve_application"}


@calculation("DIR:article-77d:4", unit="ratio")
def rfr_macro_country_factor(country_risk_corrected_spread: float, debt_asset_share: float, *,
                              qualification_reference: str, context: Context):
    """Country debt/all-assets share, not an insurer's own portfolio weight."""
    details = _qualified(context, qualification_reference, "DIR:article-77d:4", euro=True)
    spread = number(country_risk_corrected_spread, "country_risk_corrected_spread")
    share = number(debt_asset_share, "debt_asset_share", 0, 1)
    threshold = number(scalar("rfr_macro_activation_threshold", context), "threshold", 0)
    width = number(scalar("rfr_macro_activation_width", context), "width", 0)
    require(width > 0, "width", "strictly positive activation width required")
    excess = spread * share - threshold
    value = 0 if excess <= 0 else 1 if excess >= width else excess / width
    return value, {**details, "country_risk_corrected_spread": spread, "debt_asset_share": share,
                   "threshold": threshold, "width": width, "scope": "country_macro_activation_only"}


@calculation("DIR:article-77d:4", "DIR:article-77d:1c", unit="rate")
def rfr_macro_volatility_adjustment(country_risk_corrected_spread: float, euro_risk_corrected_spread: float,
                                     credit_spread_sensitivity: float, country_factor: float, *,
                                     undertaking_specific_adjustment_applies: bool,
                                     qualification_reference: str, context: Context):
    """Euro macro add-on; explicitly incompatible with undertaking-specific adjustment."""
    details = _qualified(context, qualification_reference, "DIR:article-77d:4", euro=True)
    require(isinstance(undertaking_specific_adjustment_applies, bool), "undertaking_specific_adjustment_applies",
            "explicit method decision required")
    require(not undertaking_specific_adjustment_applies, "undertaking_specific_adjustment_applies",
            "macro addition excluded with undertaking-specific adjustment", "UNSUPPORTED_METHOD")
    country = number(country_risk_corrected_spread, "country_risk_corrected_spread")
    euro = number(euro_risk_corrected_spread, "euro_risk_corrected_spread")
    cssr = number(credit_spread_sensitivity, "credit_spread_sensitivity", 0, 1)
    factor = number(country_factor, "country_factor", 0, 1)
    multiplier = number(scalar("rfr_macro_euro_multiplier", context), "euro_multiplier", 0)
    transmission = number(scalar("rfr_va_transmission", context), "transmission", 0, 1)
    excess = max(country - multiplier * euro, 0)
    return transmission * cssr * excess * factor, {**details, "country_risk_corrected_spread": country,
        "euro_risk_corrected_spread": euro, "credit_spread_sensitivity": cssr, "country_factor": factor,
        "positive_excess": excess, "euro_multiplier": multiplier, "transmission": transmission,
        "undertaking_specific_adjustment_applies": False, "scope": "euro_macro_addon_only_not_total_va"}
