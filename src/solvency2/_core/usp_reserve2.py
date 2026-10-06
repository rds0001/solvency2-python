"""AnnexXVII D square-triangle reserve method2 and explicit numerical limits."""
from fractions import Fraction
import math
import sys

from .core import Context, calculation, effective_resource, number, require, scalar


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


@calculation("DR:annex-XVII:D:2", "DR:annex-XVII:D:4", "DR:annex-XVII:D:5", unit="factor")
def usp_reserve2_estimate(cumulative_claims: list[list[float]], *,
                          qualification_reference: str, context: Context):
    """Compute sqrt(MSEP)/reserve for a qualified square cumulative triangle.

    Rows run oldest to newest accident year with lengths n,n-1,...,1.
    I>J is permitted by D(2)e but needs a separately qualified treatment of
    the printed formula's out-of-range diagonal indices; no silent padding.
    Consecutive years, expense inclusion, matching net reinsurance basis,
    negligible oldest-year tail and stochastic assumptions remain external.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(cumulative_claims, list) and bool(cumulative_claims), "cumulative_claims",
            "nonempty cumulative triangle required")
    require(all(isinstance(row, list) and bool(row) for row in cumulative_claims), "cumulative_claims",
            "each accident-year row must be a nonempty list")
    count, development_count = len(cumulative_claims), len(cumulative_claims[0])
    require(development_count <= count, "development_years", "D(2)e requires accident years >= development years")
    for key, observed in (("usp_reserve2_minimum_accident_years", count),
                          ("usp_reserve2_minimum_development_years", development_count)):
        minimum = number(scalar(key, context), key, 4)
        require(minimum == int(minimum), key, "whole-year minimum required", "REVIEW_REQUIRED")
        require(observed >= minimum, key, "insufficient method-specific history", "UNSUPPORTED_PARAMETER")
    require(count == development_count, "triangle_shape",
            "I>J rectangular history requires separate formula-index qualification", "REVIEW_REQUIRED")
    require(all(len(row) == count - i for i, row in enumerate(cumulative_claims)), "triangle_shape",
            "square upper triangle with row lengths n,n-1,...,1 required; no filling missing cells")
    amounts = [[number(v, f"cumulative_claims[{i}][{j}]", 0) for j, v in enumerate(row)]
               for i, row in enumerate(cumulative_claims)]
    require(all(v > 0 for row in amounts for v in row), "cumulative_claims",
            "zero-cell divisions require separate qualification", "REVIEW_REQUIRED")
    scale = max(max(row) for row in amounts)
    c = [[v / scale for v in row] for row in amounts]
    require(all(v > 0 for row in c for v in row), "cumulative_claims",
            "normalized cells lost to underflow", "REVIEW_REQUIRED")
    last = count - 1
    sums = [math.fsum(c[i][j] for i in range(last - j)) for j in range(last)]
    updated_sums = [math.fsum(c[i][j] for i in range(last - j + 1)) for j in range(last)]
    factors = [math.fsum(c[i][j + 1] for i in range(last - j)) / sums[j] for j in range(last)]
    require(all(math.isfinite(f) and f > 0 for f in factors), "development_factors",
            "unresolved or overflowing development factor", "REVIEW_REQUIRED")
    variances = []
    for j in range(last - 1):
        residuals = [(c[i][j + 1] - factors[j] * c[i][j]) / math.sqrt(c[i][j])
                     for i in range(last - j)]
        variance = math.fsum(r * r for r in residuals) / (last - j - 1)
        require(math.isfinite(variance) and (variance > 0 or all(r == 0 for r in residuals)),
                "development_variance", "variance unresolved at numeric precision", "REVIEW_REQUIRED")
        variances.append(variance)
    # Printed terminal rule: min(v[J-2],v[J-3],v[J-2]^2/v[J-3]).
    # No arbitrary tail factor and no repair of a zero denominator.
    a, b = variances[-1], variances[-2]
    require(b > 0, "terminal_variance", "zero denominator in prescribed tail-variance rule", "REVIEW_REQUIRED")
    terminal = a * (a / b) if a <= b else b
    require(terminal > 0 or a == 0, "terminal_variance", "terminal variance lost to underflow", "REVIEW_REQUIRED")
    variances.append(terminal)
    q = [(v / f) / f for v, f in zip(variances, factors)]
    require(all(math.isfinite(x) and (x > 0 or v == 0) for x, v in zip(q, variances)), "q",
            "scaled development variance unresolved", "REVIEW_REQUIRED")
    ultimates = []
    for i in range(count):
        ultimate = c[i][-1]
        for j in range(last - i, last):
            ultimate *= factors[j]
        require(math.isfinite(ultimate), "ultimate", "projected ultimate outside finite range", "REVIEW_REQUIRED")
        ultimates.append(ultimate)
    reserve = math.fsum(u - row[-1] for u, row in zip(ultimates, c))
    require(reserve > 64 * sys.float_info.epsilon * math.fsum(ultimates), "reserve",
            "nonpositive or numerically unresolved projected reserve", "REVIEW_REQUIRED")
    terms = []
    for i in range(1, count):
        d = last - i
        shared = q[d] / sums[d] + math.fsum(
            (c[last - j][j] / updated_sums[j]) * (q[j] / sums[j]) for j in range(d + 1, last))
        terms.append(ultimates[i] * ultimates[i] * (q[d] / c[i][d] + shared))
        for k in range(i + 1, count):
            terms.append(2 * ultimates[i] * ultimates[k] * shared)
    require(all(math.isfinite(t) and t >= 0 for t in terms), "MSEP",
            "prediction-error sum outside finite nonnegative range", "REVIEW_REQUIRED")
    msep = math.fsum(terms)
    require(msep > 0, "MSEP", "zero or unresolved prediction error requires review", "REVIEW_REQUIRED")
    value = math.sqrt(msep) / reserve
    profile = effective_resource("profile.json", context)
    return value, {
        "method": "reserve_2", "year_basis": "accident_years", "accident_years": count,
        "development_years": development_count, "triangle_scope": "I_equals_J_square_only",
        "amount_normalization": scale, "development_factors": factors,
        "normalized_development_variances": variances, "normalized_ultimates": ultimates,
        "normalized_reserve": reserve, "normalized_msep": msep,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "time_series_verified": False, "tail_materiality_verified": False,
        "credibility_applied": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "raw_reserve2_square_triangle_estimate_not_USP_authorization",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-D"]}


@calculation("DR:annex-XVII:D:4", unit="factor")
def usp_reserve2_credibility_blend(estimated_sigma: float, standard_sigma: float,
                                  credibility: float, *, calibration_reference: str, context: Context):
    """D(4) linear blend, WITHOUT the different B/C1 finite-history correction."""
    _reference(calibration_reference, "calibration_reference")
    estimated = number(estimated_sigma, "estimated_sigma", 0)
    standard = number(standard_sigma, "standard_sigma", 0)
    weight = Fraction(str(number(credibility, "credibility", 0, 1)))
    value = weight * Fraction(str(estimated)) + (1 - weight) * Fraction(str(standard))
    profile = effective_resource("profile.json", context)
    return float(value), {
        "method": "reserve_2", "estimated_sigma": estimated, "standard_sigma": standard,
        "credibility": float(weight), "finite_history_adjustment_applied": False,
        "calibration_reference": calibration_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "standard_parameter_replaced": False, "supervisory_approval_granted_by_engine": False,
        "scope": "isolated_reserve2_credibility_weighting",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-D-4"]}
