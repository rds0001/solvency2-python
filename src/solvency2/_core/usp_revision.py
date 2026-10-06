"""AnnexXVII E positive-change moments and separately qualified quantile blending."""
from fractions import Fraction
import math
import sys
from typing import Mapping

from .core import Context, calculation, effective_resource, number, require, scalar


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


@calculation("DR:annex-XVII:E:2:b", "DR:annex-XVII:E:3", "DR:annex-XVII:E:5",
             "DR:annex-XVII:E:7", "DR:annex-XVII:E:8")
def usp_revision_moments(annual_benefits: Mapping[str, list[float]], *,
                         qualification_reference: str, context: Context):
    """Return expected annual increases and prescribed sample moments.

    Each beneficiary supplies aligned A0..AT, including the initial baseline.
    Only strictly positive changes enter severity statistics. Frequency includes
    ALL years, including zero-event years. Negative changes are not netted.
    Computable moments do not prove negative-binomial/lognormal suitability,
    independence, immaterial inflation risk or the prescribed aggregate quantile.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(annual_benefits, Mapping) and bool(annual_benefits), "annual_benefits",
            "nonempty beneficiary-labelled mapping required")
    require(all(isinstance(k, str) and bool(k.strip()) for k in annual_benefits), "beneficiaries",
            "nonempty string beneficiary labels required")
    rows = list(annual_benefits.values())
    require(all(isinstance(row, list) and bool(row) for row in rows), "annual_benefits",
            "nonempty list of annual amounts per beneficiary required")
    length = len(rows[0])
    require(all(len(row) == length for row in rows), "annual_benefits",
            "aligned equal-length rows required; missing years are never zero-filled")
    years = length - 1
    minimum = number(scalar("usp_revision_minimum_years", context), "minimum_years", 2)
    require(minimum == int(minimum), "minimum_years", "whole-year minimum required", "REVIEW_REQUIRED")
    require(years >= minimum, "years", "insufficient financial years plus explicit initial baseline",
            "UNSUPPORTED_PARAMETER")
    counts = [0] * years
    positive = []
    for label, row in annual_benefits.items():
        values = [Fraction(str(number(v, f"annual_benefits.{label}[{t}]", 0))) for t, v in enumerate(row)]
        for t in range(years):
            change = values[t + 1] - values[t]
            if change > 0:
                counts[t] += 1
                positive.append(change)
    require(len(positive) >= 2, "positive_changes", "at least two positive changes needed for n-1 variance",
            "REVIEW_REQUIRED")
    count_mean = Fraction(sum(counts), years)
    count_variance = sum((Fraction(n) - count_mean) ** 2 for n in counts) / (years - 1)
    severity_mean = sum(positive) / len(positive)
    amount_scale = max(positive)
    normalized = [v / amount_scale for v in positive]
    normalized_mean = severity_mean / amount_scale
    severity_variance = sum((v - normalized_mean) ** 2 for v in normalized) / (len(positive) - 1)
    expected = sum(positive) / years
    require(expected <= Fraction(str(sys.float_info.max)), "mean_increase", "expected increase outside finite range",
            "REVIEW_REQUIRED")
    value = float(expected)
    require(value > 0, "mean_increase", "expected increase lost to underflow", "REVIEW_REQUIRED")
    severity_std = float(amount_scale) * math.sqrt(float(severity_variance))
    require(math.isfinite(severity_std) and (severity_std > 0 or severity_variance == 0), "severity_stddev",
            "severity standard deviation unresolved", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return value, {
        "method": "revision", "year_basis": "financial_years", "years": years,
        "beneficiaries": len(rows), "annual_positive_counts": counts, "positive_change_count": len(positive),
        "mean_positive_amount": float(severity_mean), "positive_amount_stddev": severity_std,
        "mean_annual_count": float(count_mean), "annual_count_stddev": math.sqrt(float(count_variance)),
        "negative_binomial_moments_nondegenerate": count_variance > count_mean,
        "lognormal_moments_nondegenerate": severity_variance > 0,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "distribution_fit_verified": False, "time_series_verified": False,
        "quantile_computed": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "revision_sample_moments_not_compound_distribution_quantile_or_USP_shock",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-E"]}


@calculation("DR:annex-XVII:E:4", "DR:article-141", "DR:article-158", unit="factor")
def usp_revision_credibility_blend(mean_increase: float, quantile_increase: float, credibility: float, *,
                                  quantile_probability: float, risk_module: str,
                                  calibration_reference: str, context: Context):
    """c*(quantile-mean)/mean+(1-c)*S, preserving the source's absence of a floor.

    The quantile of the independent negative-binomial/lognormal compound sum is
    externally qualified, NOT generated here. Probability must match the active
    profile (including explicit analyst override). Credibility is supplied, not
    inferred from the ambiguous printed E(4)a 'section7' cross-reference.
    """
    _reference(calibration_reference, "calibration_reference")
    require(isinstance(risk_module, str) and risk_module in {"life", "health_slt"}, "risk_module",
            "revision requires life or SLT health", "UNSUPPORTED_METHOD")
    mean = number(mean_increase, "mean_increase", 0)
    require(mean > 0, "mean_increase", "positive mean required by source ratio", "REVIEW_REQUIRED")
    quantile = number(quantile_increase, "quantile_increase", 0)
    weight = number(credibility, "credibility", 0, 1)
    required = number(scalar("usp_revision_quantile_probability", context), "required_probability", 0, 1)
    require(0 < required < 1, "required_probability", "interior quantile probability required", "REVIEW_REQUIRED")
    probability = number(quantile_probability, "quantile_probability", 0, 1)
    require(probability == required, "quantile_probability", "quantile must match active rule probability",
            "UNSUPPORTED_PARAMETER")
    parameter = "life_revision" if risk_module == "life" else "health_revision"
    standard = number(scalar(parameter, context), "standard_shock", 0)
    c = Fraction(str(weight))
    value = c * (Fraction(str(quantile)) / Fraction(str(mean)) - 1) + (1 - c) * Fraction(str(standard))
    require(abs(value) <= Fraction(str(sys.float_info.max)), "shock", "weighted shock outside finite range",
            "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return float(value), {
        "method": "revision", "mean_increase": mean, "quantile_increase": quantile,
        "quantile_probability": probability, "credibility": weight, "risk_module": risk_module,
        "standard_shock": standard, "standard_parameter_id": parameter, "zero_floor_applied": False,
        "calibration_reference": calibration_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "quantile_computed": False, "distribution_fit_verified": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "isolated_revision_quantile_credibility_weighting_not_distribution_model_or_authorization",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-E-4"]}
