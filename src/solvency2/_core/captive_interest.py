"""Literal DR103 duration-weighted currency formulas, not a complete interest SCR."""
from fractions import Fraction
import sys
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


def _durations(profile):
    return {r[0]: number(r[1], "prescribed_duration", 0)
            for r in profile["tables"]["captive_interest_durations"]["rows"]}


def _finite(value, field):
    require(abs(value) <= Fraction(str(sys.float_info.max)), field,
            "formula amount outside finite numeric range", "REVIEW_REQUIRED")
    result = float(value)
    require(not value or result != 0, field, "nonzero amount lost to underflow", "REVIEW_REQUIRED")
    return result


@calculation("DR:article-103:4", unit="years")
def captive_interest_duration(band: str, *, qualification_reference: str, context: Context):
    """Look up an explicitly qualified lettered band; do not invent boundary rules."""
    _reference(qualification_reference, "qualification_reference")
    profile = effective_resource("profile.json", context)
    durations = _durations(profile)
    require(isinstance(band, str) and band in durations, "band",
            "explicit DR103(4) band a..e required", "UNSUPPORTED_PARAMETER")
    row = next(r for r in profile["tables"]["captive_interest_durations"]["rows"] if r[0] == band)
    return durations[band], {"band": band, "source_interval_description": row[2],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "automatic_band_assignment": False, "boundary_assignment_verified": False,
        "scope": "prescribed_duration_for_explicitly_qualified_band",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-103-4"]}


@calculation("DR:article-103:2", "DR:article-103:3", "DR:article-103:4", "DR:annex-I", unit="currency")
def captive_interest_currency(assets: Mapping[str, dict], technical_provisions: Mapping[str, dict], *,
                               direction: str, eligibility_reference: str, valuation_reference: str,
                               stress_reference: str, context: Context):
    """Evaluate one currency's literal asset-minus-BE formula for a declared scenario.

Relative stresses, rate/duration consistency and eligibility are externally
qualified. Signed inputs are preserved: there is no hidden down-direction
sign flip, floor or stress-curve generation (including blocked 2027 curves).
All five asset bands and all 36 Annex I LoBs must be supplied explicitly.
"""
    for field, value in (("eligibility_reference", eligibility_reference),
                         ("valuation_reference", valuation_reference), ("stress_reference", stress_reference)):
        _reference(value, field)
    require(isinstance(direction, str) and direction in {"up", "down"}, "direction", "up or down required")
    profile = effective_resource("profile.json", context)
    durations = _durations(profile)
    lobs = [r[0] for r in profile["tables"]["technical_provision_lobs"]["rows"]]
    exact_keys(assets, list(durations), "assets")
    exact_keys(technical_provisions, lobs, "technical_provisions")
    asset_terms, provision_terms = {}, {}
    for band, duration in durations.items():
        fields = ["net_value", "rate", "relative_stress"]
        exact_keys(assets[band], fields, f"assets.{band}")
        term = Fraction(str(duration))
        for field in fields:
            term *= Fraction(str(number(assets[band][field], f"assets.{band}.{field}")))
        asset_terms[band] = term
    for lob in lobs:
        fields = ["best_estimate", "modified_duration", "rate", "relative_stress"]
        exact_keys(technical_provisions[lob], fields, f"technical_provisions.{lob}")
        term = Fraction(1)
        for field in fields:
            term *= Fraction(str(number(technical_provisions[lob][field], f"technical_provisions.{lob}.{field}")))
        provision_terms[lob] = term
    asset_sum, provision_sum = sum(asset_terms.values(), Fraction()), sum(provision_terms.values(), Fraction())
    value = _finite(asset_sum - provision_sum, "currency_formula")
    # Individual components may overflow even when their exact difference does
    # not. Preserve exact decimal-rational strings in that uncommon case.
    def audit_amount(amount):
        if abs(amount) > Fraction(str(sys.float_info.max)) or (amount and float(amount) == 0):
            return {"numerator": str(amount.numerator), "denominator": str(amount.denominator)}
        return float(amount)

    return value, {"direction": direction, "currency": context.currency,
        "asset_contributions": {k: audit_amount(v) for k, v in asset_terms.items()},
        "provision_contributions": {k: audit_amount(v) for k, v in provision_terms.items()},
        "asset_sum": audit_amount(asset_sum), "provision_sum": audit_amount(provision_sum),
        "asset_durations": durations, "eligibility_reference": eligibility_reference,
        "valuation_reference": valuation_reference, "stress_reference": stress_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "stress_curve_computed": False,
        "direction_sign_changed": False, "floor_applied": False, "scenario_selected": False,
        "currency_aggregation_performed": False, "eligibility_verified": False,
        "scope": "signed_literal_currency_formula_not_selected_or_released_interest_SCR",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-103"]}
