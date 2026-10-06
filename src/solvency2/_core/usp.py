"""Prescribed USP components, not insurer models or supervisory authorization."""
from fractions import Fraction
import math
import sys
from typing import Mapping

from .core import Context, calculation, effective_resource, number, require


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


@calculation("DR:annex-XVII:G", unit="factor")
def usp_credibility_factor(years: int, *, method: str, risk_module: str,
                           segment: str | None = None, qualification_reference: str, context: Context):
    """Look up AnnexXVII credibility with the method's correct year basis.

    The year count is not evidence of data representativeness or required
    consecutive history. Revision has no nonlife segment. Terminal table rows
    apply to all later years; no interpolation or below-table extrapolation.
    """
    _reference(qualification_reference, "qualification_reference")
    bases = {"premium": "accident_years", "reserve_1": "financial_years",
             "reserve_2": "accident_years", "revision": "financial_years",
             "nonproportional_1": "reporting_years", "nonproportional_2": "reporting_years"}
    require(isinstance(method, str) and method in bases, "method", "prescribed method required",
            "UNSUPPORTED_METHOD")
    if method == "revision":
        require(isinstance(risk_module, str) and risk_module in {"life", "health_slt"},
                "risk_module", "revision requires life or SLT health", "UNSUPPORTED_METHOD")
        require(segment is None, "segment", "revision has no premium/reserve segment")
        category = "other"
    else:
        require(isinstance(risk_module, str) and risk_module in {"nonlife", "health_nslt"},
                "risk_module", "premium/reserve/NP method requires nonlife or NSLT health", "UNSUPPORTED_METHOD")
        limit = 12 if risk_module == "nonlife" else 4
        require(isinstance(segment, str) and segment in {str(i) for i in range(1, limit + 1)},
                "segment", "explicit prescribed segment required", "UNSUPPORTED_PARAMETER")
        category = "nonlife_1_5_6" if risk_module == "nonlife" and segment in {"1", "5", "6"} else "other"
    count = number(years, "years", 0)
    require(count == int(count), "years", "whole number of qualifying years required")
    count = int(count)
    profile = effective_resource("profile.json", context)
    rows = [r for r in profile["tables"]["usp_credibility_factors"]["rows"] if r[0] == category]
    factors = {}
    for _, row_year, factor in rows:
        row_year = number(row_year, "table_year", 0)
        require(row_year == int(row_year) and int(row_year) not in factors,
                "table_year", "unique whole-year table axes required", "REVIEW_REQUIRED")
        factors[int(row_year)] = number(factor, "credibility_factor", 0, 1)
    require(bool(factors), "table", "credibility class missing", "REVIEW_REQUIRED")
    selected = min(count, max(factors))
    require(selected in factors, "years", "no supported table entry for this history length",
            "UNSUPPORTED_PARAMETER")
    return factors[selected], {
        "method": method, "risk_module": risk_module, "segment": segment,
        "years": count, "table_year": selected, "credibility_class": category, "year_basis": bases[method],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "time_series_verified": False, "supervisory_approval_granted_by_engine": False,
        "scope": "credibility_table_only_not_USP_estimation_or_authorization",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-G"]}


@calculation("DR:annex-XVII:F1:4", "DR:annex-XVII:F2:method-specification-2", unit="factor")
def usp_nonproportional_credibility_blend(estimated_factor: float, standard_factor: float,
                                         credibility: float, *, method: str,
                                         calibration_reference: str, context: Context):
    """c*NP_est + (1-c)*NP_standard; separate from either F1/F2 estimator.

    Input-factor qualification and their source-defined calibration are external.
    The engine neither estimates loss distributions here nor substitutes this
    result into a standard-formula calculation or grants approval.
    """
    _reference(calibration_reference, "calibration_reference")
    require(isinstance(method, str) and method in {"nonproportional_1", "nonproportional_2"},
            "method", "F1 or F2 method required", "UNSUPPORTED_METHOD")
    estimated = number(estimated_factor, "estimated_factor", 0)
    standard = number(standard_factor, "standard_factor", 0)
    weight = number(credibility, "credibility", 0, 1)
    c = Fraction(str(weight))
    value = c * Fraction(str(estimated)) + (1 - c) * Fraction(str(standard))
    profile = effective_resource("profile.json", context)
    return float(value), {
        "estimated_factor": estimated, "standard_factor": standard, "credibility": weight, "method": method,
        "calibration_reference": calibration_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "estimated_factor_computed": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "isolated_nonproportional_credibility_weighting",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-F1-F2"]}


@calculation("DR:annex-XVII:F1:5", "DR:annex-XVII:F1:6", unit="factor")
def usp_excess_of_loss_estimate(ultimate_claims: list[float], retention: float, *,
                                upper_limit: float | None = None,
                                qualification_reference: str, context: Context):
    """Estimate raw NP′ for one homogeneous F1 excess-of-loss group.

    F1 uses the second RAW moment, not variance. ``upper_limit`` is the
    absolute upper loss threshold b2, not layer width. Data representativeness,
    five reporting years, expense exclusion, gross/net basis, lognormal fit
    and treaty eligibility need external qualification. No approval or automatic
    standard-formula substitution follows from this component.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(ultimate_claims, list) and bool(ultimate_claims), "ultimate_claims",
            "nonempty list of ultimate individual claim amounts required")
    claims = [number(v, f"ultimate_claims[{i}]", 0) for i, v in enumerate(ultimate_claims)]
    b1 = number(retention, "retention", 0)
    require(b1 > 0, "retention", "zero-threshold limiting case not qualified by this component",
            "REVIEW_REQUIRED")
    b2 = None if upper_limit is None else number(upper_limit, "upper_limit", 0)
    require(b2 is None or b2 > b1, "upper_limit", "absolute upper threshold must exceed retention")
    scale = max(claims)
    require(scale > 0, "ultimate_claims", "positive nondegenerate lognormal moments required", "REVIEW_REQUIRED")
    # Exact decimal input ratios prevent squared amounts overflowing or tiny
    # amounts underflowing before averaging. Returned moments stay normalized.
    scale_exact = Fraction(str(scale))
    normalized = [Fraction(str(v)) / scale_exact for v in claims]
    mean_exact = sum(normalized) / len(normalized)
    second_exact = sum(v * v for v in normalized) / len(normalized)
    relative_variance = (second_exact - mean_exact * mean_exact) / (mean_exact * mean_exact)
    require(relative_variance > 0, "ultimate_claims", "degenerate lognormal fit needs separate review",
            "REVIEW_REQUIRED")
    mean, second = float(mean_exact), float(second_exact)
    eta = math.sqrt(math.log1p(float(relative_variance)))
    require(eta > 0, "ultimate_claims", "lognormal spread below numeric resolution", "REVIEW_REQUIRED")
    theta = math.log(mean) - eta * eta / 2
    lower = b1 / scale
    upper = None if b2 is None else b2 / scale
    require(math.isfinite(lower) and lower > 0 and
            (upper is None or (math.isfinite(upper) and upper > lower)),
            "thresholds", "scaled thresholds outside stable numeric range", "REVIEW_REQUIRED")

    def tail(z):
        return math.erfc(z / math.sqrt(2)) / 2

    z1 = (math.log(lower) - theta) / eta
    w1 = second * tail(2 * eta - z1) + (lower * tail(z1)) * lower
    terms = [w1]
    if upper is not None:
        z2 = (math.log(upper) - theta) / eta
        # Algebraically the printed w1-w2+w+2*(b2-b1)*(mu2-mu).
        # Direct survival probabilities avoid subtracting CDFs close to one.
        q0, q1, q2 = tail(z2), tail(z2 - eta), tail(z2 - 2 * eta)
        gap = upper - lower
        terms.extend([second * q2, -(upper * q0) * upper,
                      (upper * q0) * gap * 2, -(mean * q1) * gap * 2])
    require(all(math.isfinite(t) for t in terms), "estimate", "intermediate moment overflow",
            "REVIEW_REQUIRED")
    numerator = math.fsum(terms)
    error_bound = 64 * sys.float_info.epsilon * math.fsum(abs(t) for t in terms)
    require(numerator > error_bound, "estimate", "retained moment unresolved or lost to cancellation",
            "REVIEW_REQUIRED")
    value = math.sqrt(numerator / second)
    require(math.isfinite(value) and value <= 1 + 64 * sys.float_info.epsilon,
            "estimate", "retained-loss moment inconsistent with numerical bounds", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return value, {
        "method": "nonproportional_1", "claim_count": len(claims), "amount_normalization": scale,
        "normalized_mean": mean, "normalized_second_raw_moment": second,
        "normalized_theta": theta, "eta": eta, "retention": b1, "upper_limit": b2,
        "upper_limit_semantics": "absolute_claim_threshold_not_layer_width",
        "branch_selection": "explicit_upper_limit_input; source_cross_reference_qualification_external",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "time_series_verified": False, "distribution_fit_verified": False,
        "credibility_applied": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "raw_F1_estimate_single_homogeneous_group",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-F1"]}


@calculation("DR:annex-XVII:F1:7", "DR:annex-XVII:F2:method-specification-5", "DR:article-116:3", unit="factor")
def usp_excess_of_loss_group_weighting(estimated_factors: Mapping[str, float],
                                       premium_volumes: Mapping[str, float], *,
                                       qualification_reference: str, method: str = "nonproportional_1",
                                       context: Context):
    """Weight raw F1/F2 group estimates by externally qualified premium volumes.

    Same-segment homogeneity and Article116(3) volume measurement are not
    inferred from group labels. This is a weighted mean, not diversification,
    credibility weighting or permission to replace a standard parameter.
    F2 only supports weighting externally qualified estimates here; its printed
    estimator/moment anomalies are not repaired or evaluated. No inferred F2 cap.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(method, str) and method in {"nonproportional_1", "nonproportional_2"}, "method",
            "F1 or F2 method required", "UNSUPPORTED_METHOD")
    require(isinstance(estimated_factors, Mapping) and bool(estimated_factors),
            "estimated_factors", "nonempty group-labelled mapping required")
    require(isinstance(premium_volumes, Mapping) and set(premium_volumes) == set(estimated_factors),
            "premium_volumes", "exactly the same group labels required")
    require(all(isinstance(k, str) and bool(k.strip()) for k in estimated_factors),
            "groups", "nonempty string group labels required")
    factors = {k: number(v, f"estimated_factors.{k}", 0, 1 if method == "nonproportional_1" else None)
               for k, v in estimated_factors.items()}
    volumes = {k: number(v, f"premium_volumes.{k}", 0) for k, v in premium_volumes.items()}
    exact_volumes = {k: Fraction(str(v)) for k, v in volumes.items()}
    total = sum(exact_volumes.values())
    require(total > 0, "premium_volumes", "positive total volume required")
    # Ratio of exact sums: even large finite volumes need not have a
    # representable floating-point sum, while their weighted mean does.
    value = sum(exact_volumes[k] * Fraction(str(factors[k])) for k in factors) / total
    profile = effective_resource("profile.json", context)
    return float(value), {
        "method": method, "estimated_factors": factors, "premium_volumes": volumes,
        "group_weights": {k: float(v / total) for k, v in exact_volumes.items()},
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "group_homogeneity_verified": False, "volume_measure_verified": False,
        "credibility_applied": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "group_estimates_computed": False,
        "scope": "raw_nonproportional_estimate_homogeneous_groups_within_one_segment",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                     + (":annex-XVII-F1-7" if method == "nonproportional_1" else ":annex-XVII-F2-5")]}
