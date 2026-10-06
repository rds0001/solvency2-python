"""Prescribed revision compound quantile with disclosed lattice/roundoff controls."""
import math
import sys
from typing import Mapping

from .core import Context, calculation, effective_resource, number, require, scalar
from .usp_revision import usp_revision_moments


def _money(value, scale, field):
    result = value * scale
    require(math.isfinite(result) and (value == 0 or result > 0), field,
            "quantile amount outside representable range", "REVIEW_REQUIRED")
    return result


def _lattice_interval(np, ndtr, mean_count, variance_count, severity_cv2, probability, size):
    """Floor/ceil severity coupling plus tilted FFT; guard is not certified arithmetic."""
    dispersion = (variance_count - mean_count) / mean_count
    shape = mean_count / dispersion
    variance_sum = mean_count * severity_cv2 + variance_count
    extent = 4 * (mean_count + math.sqrt(variance_sum * probability / (1 - probability)))
    require(math.isfinite(extent) and extent > 0, "grid", "compound scale unresolved", "REVIEW_REQUIRED")
    step = extent / size
    eta2 = math.log1p(severity_cv2)
    require(eta2 > 0 and math.isfinite(eta2), "severity", "lognormal shape unresolved", "REVIEW_REQUIRED")
    edges = np.arange(size + 1, dtype=float) * step
    severity_cdf = np.zeros(size + 1)
    severity_cdf[1:] = ndtr((np.log(edges[1:]) + eta2 / 2) / math.sqrt(eta2))
    floor_masses = np.diff(severity_cdf)
    require(bool(np.all(np.isfinite(floor_masses))) and bool(np.all(floor_masses >= 0)),
            "severity", "severity probabilities unresolved", "REVIEW_REQUIRED")
    ceil_masses = np.r_[0.0, floor_masses[:-1]]
    alias_bound = 1e-12
    damping = -math.log(alias_bound) / size
    tilt = np.exp(-damping * np.arange(size))
    limit = size // 4
    # Engineering guard for finite-precision CDF/FFT operations, deliberately
    # distinguished from the exact-arithmetic alias and stochastic order bounds.
    roundoff = (64 * sys.float_info.epsilon * (1 + mean_count) * math.log2(size)
                * np.cumsum(1 / tilt[:limit + 1]))
    quantiles, runs = [], []
    for rounding, masses in (("floor", floor_masses), ("ceil", ceil_masses)):
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            generating = np.fft.fft(masses * tilt)
            # Equivalent to (p/(1-(1-p)*G))**shape, without subtracting
            # nearly equal logarithms when count variance is close to its mean.
            transform = np.exp(-shape * np.log1p(dispersion * (1 - generating)))
            distribution = np.fft.ifft(transform).real[:limit + 1] / tilt[:limit + 1]
        require(bool(np.all(np.isfinite(distribution))), "fft", "nonfinite compound probabilities",
                "REVIEW_REQUIRED")
        negative = np.maximum(-distribution, 0)
        require(bool(np.all(negative <= roundoff)), "fft", "negative masses exceed roundoff guard",
                "REVIEW_REQUIRED")
        clipped_mass = float(np.sum(negative))
        cdf = np.cumsum(np.maximum(distribution, 0))
        guard = roundoff + clipped_mass + alias_bound
        # Upper CDF for a lower quantile; lower CDF for an upper quantile.
        guarded_cdf = cdf + guard if rounding == "floor" else cdf - guard
        crossed = np.flatnonzero(guarded_cdf >= probability)
        index = int(crossed[0]) if len(crossed) else None
        quantiles.append(None if index is None else index * step)
        runs.append({"severity_rounding": rounding, "quantile_index": index,
                     "clipped_negative_mass": clipped_mass,
                     "cdf_at_index": None if index is None else float(cdf[index]),
                     "cdf_guard_at_index": None if index is None else float(guard[index])})
    return quantiles, {"grid_size": size, "normalized_step": step, "normalized_extent": extent,
                       "searched_grid_fraction": .25, "exact_arithmetic_alias_bound": alias_bound,
                       "roundoff_guard_certified": False, "roundings": runs}


@calculation("DR:annex-XVII:E:4:c", "DR:annex-XVII:E:6:a-c", "DR:annex-XVII:E:7-8", unit="currency")
def usp_revision_compound_quantile(annual_benefits: Mapping[str, list[float]], *,
                                    qualification_reference: str, context: Context,
                                    relative_tolerance: float = .001, max_grid_power: int = 20):
    """Return the upper numerical bracket of the prescribed compound quantile.

    Uses prescribed raw-data moments, not a Monte Carlo or internally chosen
    insurer model. The lower/upper severity-rounding order is mathematical;
    the floating-point guard is NOT formally certified interval arithmetic.
    Numerical controls, backend versions, bounds and clipping are disclosed.
    Nonconvergence or degenerate distribution fits require external review.
    """
    tolerance = number(relative_tolerance, "relative_tolerance", 0, .1)
    require(tolerance > 0, "relative_tolerance", "positive numerical tolerance required")
    power = number(max_grid_power, "max_grid_power", 10, 22)
    require(power == int(power), "max_grid_power", "whole grid exponent required")
    # Reuse the public source-bound moment calculation. This is a small
    # deterministic preprocessing step, not a second independent data model.
    moments = usp_revision_moments(annual_benefits, qualification_reference=qualification_reference,
                                   context=context)
    stats = moments.details
    require(stats["negative_binomial_moments_nondegenerate"] and stats["lognormal_moments_nondegenerate"],
            "distribution_moments", "nondegenerate negative-binomial and lognormal moments required",
            "REVIEW_REQUIRED")
    count_mean = stats["mean_annual_count"]
    count_variance = stats["annual_count_stddev"] ** 2
    amount_mean = stats["mean_positive_amount"]
    severity_cv2 = (stats["positive_amount_stddev"] / amount_mean) ** 2
    require(math.isfinite(count_variance) and count_variance > count_mean and
            math.isfinite(severity_cv2) and severity_cv2 > 0,
            "distribution_moments", "distribution parameters unresolved at numeric precision", "REVIEW_REQUIRED")
    dispersion = (count_variance - count_mean) / count_mean
    shape = count_mean / dispersion
    require(shape > 0 and math.isfinite(shape) and math.isfinite(dispersion), "count_distribution",
            "negative-binomial parameters unresolved", "REVIEW_REQUIRED")
    probability = number(scalar("usp_revision_quantile_probability", context), "quantile_probability", 0, 1)
    require(0 < probability < 1, "quantile_probability", "interior quantile probability required", "REVIEW_REQUIRED")
    zero_mass = math.exp(-shape * math.log1p(dispersion))
    require(abs(zero_mass - probability) > 64 * sys.float_info.epsilon, "quantile_probability",
            "probability is numerically indistinguishable from the zero atom", "REVIEW_REQUIRED")
    history = []
    backend = {"method": "analytic_zero_atom", "numpy_version": None, "scipy_version": None}
    if zero_mass > probability:
        lower = upper = width = 0.0
    else:
        try:
            import numpy as np
            import scipy
            from scipy.special import ndtr
        except ImportError:
            require(False, "numerical_backend", "optional NumPy/SciPy backend unavailable", "REVIEW_REQUIRED")
        backend = {"method": "tilted_fft_floor_ceil_compound", "numpy_version": np.__version__,
                   "scipy_version": scipy.__version__}
        converged = False
        for exponent in range(10, int(power) + 1):
            try:
                bounds, details = _lattice_interval(np, ndtr, count_mean, count_variance, severity_cv2,
                                                    probability, 2 ** exponent)
            except (ArithmeticError, ValueError) as error:
                # Preserve controlled calculation failures instead of disguising them.
                from .core import CalculationError
                if isinstance(error, CalculationError):
                    raise
                require(False, "numerical_quantile", "compound arithmetic unresolved", "REVIEW_REQUIRED")
            history.append(details)
            if None in bounds:
                continue
            lower, upper = bounds
            require(0 <= lower <= upper and upper > 0, "quantile_interval",
                    "rounding bounds crossed or unresolved", "REVIEW_REQUIRED")
            width = (upper - lower) / upper
            if width <= tolerance:
                converged = True
                break
        require(converged, "numerical_quantile", "quantile interval did not converge within grid budget",
                "REVIEW_REQUIRED")
        lower, upper = _money(lower, amount_mean, "lower_quantile"), _money(upper, amount_mean, "upper_quantile")
    profile = effective_resource("profile.json", context)
    return upper, {"method": "revision", "quantile_probability": probability,
        "quantile_interval": {"lower": lower, "upper": upper, "relative_width": width},
        "returned_bound": "upper", "mean_increase": moments.value, "years": stats["years"],
        "mean_annual_count": count_mean, "annual_count_variance": count_variance,
        "mean_positive_amount": amount_mean, "positive_amount_stddev": stats["positive_amount_stddev"],
        "negative_binomial_shape": shape, "negative_binomial_success_probability": 1 / (1 + dispersion),
        "probability_of_zero": zero_mass, "relative_tolerance": tolerance, "max_grid_power": int(power),
        "numerical_tolerance_met": True, "backend": backend, "grid_history": history,
        "floating_point_error_formally_certified": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "distribution_fit_verified": False, "independence_verified": False, "credibility_applied": False,
        "standard_parameter_replaced": False, "supervisory_approval_granted_by_engine": False,
        "scope": "prescribed_compound_quantile_numeric_upper_bracket_not_approved_USP",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-E"]}
