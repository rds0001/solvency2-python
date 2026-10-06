"""AnnexXVII B/C1 likelihood components; fitting and qualification stay explicit."""
from fractions import Fraction
import math
import sys

from .core import Context, calculation, effective_resource, number, require, scalar


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


def _method(method):
    require(isinstance(method, str) and method in {"premium", "reserve_1"}, "method",
            "premium or reserve_1 method required", "UNSUPPORTED_METHOD")
    return "accident_years" if method == "premium" else "financial_years"


def _years(years, context):
    minimum = number(scalar("usp_lognormal_minimum_years", context), "minimum_years", 2)
    require(minimum == int(minimum), "minimum_years", "whole-year parameter required", "REVIEW_REQUIRED")
    count = number(years, "years", 0)
    require(count == int(count), "years", "whole number of years required")
    require(count >= minimum, "years", "insufficient history for selected method", "UNSUPPORTED_PARAMETER")
    return int(count)


def _lognormal_components(losses, volumes, mixing, log_coefficient, context):
    """Profile the conditional normal log-ratio mean at a GIVEN delta/gamma."""
    require(isinstance(losses, list) and isinstance(volumes, list) and
            bool(losses) and len(losses) == len(volumes), "data",
            "nonempty equal-length loss and volume lists required")
    count = _years(len(losses), context)
    ys = [number(y, f"losses[{i}]", 0) for i, y in enumerate(losses)]
    xs = [number(x, f"volumes[{i}]", 0) for i, x in enumerate(volumes)]
    require(all(v > 0 for v in ys + xs), "data",
            "strictly positive amounts required by lognormal formula; zero case needs review", "REVIEW_REQUIRED")
    delta = number(mixing, "mixing", 0, 1)
    gamma = number(log_coefficient, "log_coefficient")
    max_x = max(xs)
    log_mean_x = math.log(max_x) + math.log(math.fsum(x / max_x for x in xs) / count)
    log_ratios = [math.log(y) - math.log(x) for x, y in zip(xs, ys)]
    variances = []
    for x in xs:
        if delta == 1:
            log_mixture = 0.0
        elif delta == 0:
            log_mixture = log_mean_x - math.log(x)
        else:
            a, b = math.log1p(-delta) + log_mean_x - math.log(x), math.log(delta)
            larger, smaller = max(a, b), min(a, b)
            log_mixture = larger + math.log1p(math.exp(smaller - larger))
        exponent = log_mixture + 2 * gamma
        require(math.isfinite(exponent), "log_coefficient", "log-variance exponent outside numeric range",
                "REVIEW_REQUIRED")
        # Softplus: ln(1+exp(exponent)), without overflow in exp.
        variance = (exponent + math.log1p(math.exp(-exponent)) if exponent > 0
                    else math.log1p(math.exp(exponent)))
        require(variance > 0 and math.isfinite(variance), "log_coefficient",
                "lognormal variance unresolved at numeric precision", "REVIEW_REQUIRED")
        variances.append(variance)
    smallest = min(variances)
    weights = [smallest / v for v in variances]
    require(all(w > 0 for w in weights), "data", "precision weights lost to underflow", "REVIEW_REQUIRED")
    total_weight = math.fsum(weights)
    anchor = log_ratios[0]
    centered_mean = math.fsum(w * (r - anchor) for w, r in zip(weights, log_ratios)) / total_weight
    average_variance = (smallest / total_weight) * count
    log_sigma = gamma + anchor + centered_mean + average_variance / 2
    require(math.isfinite(log_sigma) and log_sigma <= math.log(sys.float_info.max), "sigma",
            "sigma outside finite numeric range", "REVIEW_REQUIRED")
    sigma = math.exp(log_sigma)
    require(sigma > 0 and math.isfinite(sigma), "sigma", "sigma lost to underflow", "REVIEW_REQUIRED")
    # Equals sum(pi*r^2)-sum(log(pi)), but uses centered residuals and
    # log-variances directly; no unstable gamma-log(sigma) cancellation.
    contributions = []
    for r, variance in zip(log_ratios, variances):
        residual = (r - anchor) - centered_mean + (variance - average_variance) / 2
        standardized = residual / math.sqrt(variance)
        contribution = standardized * standardized + math.log(variance)
        require(math.isfinite(contribution), "objective", "likelihood outside finite numeric range",
                "REVIEW_REQUIRED")
        contributions.append(contribution)
    objective = math.fsum(contributions)
    require(math.isfinite(objective), "objective", "likelihood outside finite numeric range", "REVIEW_REQUIRED")
    return sigma, {"mixing": delta, "log_coefficient": gamma, "years": count,
                   "log_sigma": log_sigma, "lognormal_variances": variances,
                   "normalized_precision_weights": [w / total_weight for w in weights], "objective": objective}


@calculation("DR:annex-XVII:B:5", "DR:annex-XVII:B:6",
             "DR:annex-XVII:C:5", "DR:annex-XVII:C:6", unit="factor")
def usp_lognormal_sigma(losses: list[float], volumes: list[float], mixing: float,
                        log_coefficient: float, *, method: str,
                        qualification_reference: str, context: Context):
    """Evaluate prescribed sigma and objective at explicit delta/gamma.

    This does NOT claim the supplied pair minimizes the objective. B uses
    accident-year aggregated claims and earned premiums; C1 uses financial-year
    end reserves plus payments for opening claims, and opening reserves.
    Both include servicing expenses, unlike the F1 individual-claim estimator.
    Consecutiveness, adjustments, statistical assumptions and fitting need
    separate qualification. No automatic standard-formula replacement.
    """
    _reference(qualification_reference, "qualification_reference")
    basis = _method(method)
    value, details = _lognormal_components(losses, volumes, mixing, log_coefficient, context)
    profile = effective_resource("profile.json", context)
    return value, {**details, "method": method, "year_basis": basis,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "minimization_performed": False, "minimum_certified": False, "time_series_verified": False,
        "credibility_applied": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "sigma_and_objective_at_supplied_parameters_not_fitted_USP",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-B-C"]}


@calculation("DR:annex-XVII:B:4", "DR:annex-XVII:C:4", unit="factor")
def usp_lognormal_credibility_blend(estimated_sigma: float, standard_sigma: float,
                                   credibility: float, years: int, *, method: str,
                                   calibration_reference: str, context: Context):
    """Apply B/C1 finite-history correction BEFORE credibility blending.

    c*sigma_hat*sqrt((T+1)/(T-1)) + (1-c)*sigma_standard. This correction
    does not belong to F1/F2 or reserve method2. Appropriate standard sigma
    and fitted sigma qualification are explicit external inputs.
    """
    _reference(calibration_reference, "calibration_reference")
    basis = _method(method)
    count = _years(years, context)
    estimated = number(estimated_sigma, "estimated_sigma", 0)
    standard = number(standard_sigma, "standard_sigma", 0)
    c = number(credibility, "credibility", 0, 1)
    adjustment = math.sqrt(1 + 2 / (count - 1))
    weight = Fraction(str(c))
    exact = weight * Fraction(str(estimated)) * Fraction(str(adjustment)) + (1 - weight) * Fraction(str(standard))
    require(exact <= Fraction(str(sys.float_info.max)), "sigma", "weighted sigma outside finite range",
            "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return float(exact), {
        "estimated_sigma": estimated, "standard_sigma": standard, "credibility": c,
        "years": count, "year_basis": basis, "method": method, "finite_history_adjustment": adjustment,
        "calibration_reference": calibration_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "minimization_performed": False, "time_series_verified": False, "standard_parameter_replaced": False,
        "standard_sigma_selection": "explicit_external_input_not_inferred_from_C4e_prem_label",
        "supervisory_approval_granted_by_engine": False,
        "scope": "isolated_B_C1_finite_history_and_credibility_weighting",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-B-C"]}
