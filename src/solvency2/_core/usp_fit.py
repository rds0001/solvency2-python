"""Numerical Annex XVII B/C1 fit, separate from data qualification and approval.

SciPy is loaded lazily for unequal volumes. Its deterministic multi-start
search is a numerical implementation, not proof of a global minimum.
"""
import math

from .core import Context, calculation, effective_resource, number, require
from .usp_lognormal import _lognormal_components, _method, _reference


def _fit_evaluator(log_ratios, log_volume_ratios):
    """Profile the mean; return objective and its analytic delta/gamma gradient."""
    count = len(log_ratios)
    anchor = log_ratios[0]

    def evaluate(pair):
        delta, gamma = map(float, pair)
        variances, derivatives = [], []
        for log_q in log_volume_ratios:
            if delta == 0:
                mixture = log_q
            elif delta == 1:
                mixture = 0.0
            else:
                a, b = math.log1p(-delta) + log_q, math.log(delta)
                mixture = max(a, b) + math.log1p(math.exp(-abs(a - b)))
            exponent = mixture + 2 * gamma
            variance = (exponent + math.log1p(math.exp(-exponent)) if exponent > 0
                        else math.log1p(math.exp(exponent)))
            if not math.isfinite(variance) or variance <= 0:
                raise ArithmeticError("unresolved lognormal variance")
            # (1-q)/a, evaluated from logs; no overflow-prone raw xbar/x.
            change = math.exp(-mixture) - math.exp(log_q - mixture)
            sigmoid = -math.expm1(-variance)
            variances.append(variance)
            derivatives.append((sigmoid * change, 2 * sigmoid))
        smallest = min(variances)
        weights = [smallest / v for v in variances]
        total = math.fsum(weights)
        if not all(w > 0 for w in weights):
            raise ArithmeticError("unresolved precision weights")
        mean = math.fsum(w * (r - anchor) for w, r in zip(weights, log_ratios)) / total
        average_variance = smallest * (count / total)
        terms, gd, gg = [], [], []
        for r, v, (vd, vg) in zip(log_ratios, variances, derivatives):
            residual = r - anchor - mean + (v - average_variance) / 2
            standardized = residual / math.sqrt(v)
            terms.append(standardized * standardized + math.log(v))
            derivative = (1 + residual - standardized * standardized) / v
            gd.append(derivative * vd)
            gg.append(derivative * vg)
        result = math.fsum(terms), (math.fsum(gd), math.fsum(gg))
        if not all(math.isfinite(x) for x in (result[0], *result[1])):
            raise ArithmeticError("unresolved likelihood or gradient")
        return result

    return evaluate


def _projected_gradient(delta, gradient):
    """KKT residual for the prescribed closed delta interval; gamma is free."""
    gd, gg = gradient
    if delta == 0:
        gd = min(gd, 0.0)
    elif delta == 1:
        gd = max(gd, 0.0)
    return max(abs(gd), abs(gg))


@calculation("DR:annex-XVII:B:5", "DR:annex-XVII:C:5", unit="factor")
def usp_lognormal_fit(losses: list[float], volumes: list[float], *, method: str,
                      qualification_reference: str, context: Context,
                      max_iterations: int = 1000, gradient_tolerance: float = 1e-7):
    """Fit prescribed delta/gamma, returning raw sigma before credibility.

Both boundary faces and deterministic interior starts are searched. Optional
numerical controls are reported, never treated as regulatory parameters.
Nonconvergence and constant log-ratios are REVIEW_REQUIRED, not zero sigma.
Data assumptions, consecutive history and supervisory approval stay external.
"""
    _reference(qualification_reference, "qualification_reference")
    basis = _method(method)
    iterations = number(max_iterations, "max_iterations", 1)
    require(iterations == int(iterations), "max_iterations", "whole iteration count required")
    tolerance = number(gradient_tolerance, "gradient_tolerance", 0)
    require(0 < tolerance <= 1e-3, "gradient_tolerance",
            "numerical gradient tolerance must be positive and at most 1e-3")
    # Shared validation and history rules; later evaluations do not reload profiles.
    _lognormal_components(losses, volumes, .5, 0, context)
    count = len(losses)
    log_ratios = [math.log(y) - math.log(x) for x, y in zip(volumes, losses)]
    anchor = log_ratios[0]
    mean = math.fsum(r - anchor for r in log_ratios) / count
    variance = math.fsum((r - anchor - mean) ** 2 for r in log_ratios) / count
    require(variance > 1e-28, "data", "constant or numerically unresolved log-ratios have no finite fit",
            "REVIEW_REQUIRED")
    log_mean_x = math.log(max(volumes)) + math.log(math.fsum(x / max(volumes) for x in volumes) / count)
    evaluate = _fit_evaluator(log_ratios, [log_mean_x - math.log(x) for x in volumes])
    # log(expm1(v))/2, including large-v stability.
    initial_gamma = (variance + math.log1p(-math.exp(-variance)) if variance > 1
                     else math.log(math.expm1(variance))) / 2
    diagnostics = []
    if all(x == volumes[0] for x in volumes):
        delta, gamma = 0.0, initial_gamma
        backend, version = "analytic_equal_volumes", None
        objective, gradient = evaluate((delta, gamma))
        projected = _projected_gradient(delta, gradient) / count
        require(projected <= tolerance, "fit", "analytic fit unresolved at requested tolerance",
                "REVIEW_REQUIRED")
    else:
        try:
            import scipy
            from scipy.optimize import minimize
        except ImportError:
            require(False, "optimizer", "optional optimization dependency SciPy is unavailable", "REVIEW_REQUIRED")
        backend, version = "scipy.optimize.L-BFGS-B", scipy.__version__
        candidates = []
        for boundary in (None, 0.0, 1.0):
            for start_delta in ((0.0, .5, 1.0) if boundary is None else (boundary,)):
                for offset in (-1.0, 0.0, 1.0):
                    start_gamma = initial_gamma + offset

                    def objective_gradient(pair):
                        point = pair if boundary is None else (boundary, pair[0])
                        value, grad = evaluate(point)
                        return value, grad if boundary is None else (grad[1],)

                    try:
                        fit = minimize(objective_gradient,
                            (start_delta, start_gamma) if boundary is None else (start_gamma,),
                            jac=True, method="L-BFGS-B",
                            bounds=((0, 1), (None, None)) if boundary is None else ((None, None),),
                            options={"maxiter": int(iterations), "ftol": 1e-14,
                                     "gtol": tolerance * count * .1, "maxls": 50})
                        d, g = (map(float, fit.x) if boundary is None else (boundary, float(fit.x[0])))
                        value, grad = evaluate((d, g))
                        residual = _projected_gradient(d, grad) / count
                        accepted = bool(fit.success) and residual <= tolerance
                        diagnostics.append({"boundary": boundary, "start": [start_delta, start_gamma],
                            "success": bool(fit.success), "accepted": accepted,
                            "iterations": int(fit.nit), "message": str(fit.message),
                            "objective": value, "projected_gradient_per_year": residual})
                        candidates.append((value, d, g, residual, accepted))
                    except (ArithmeticError, ValueError):
                        diagnostics.append({"boundary": boundary, "start": [start_delta, start_gamma],
                                            "success": False, "accepted": False,
                                            "message": "numeric evaluation unresolved"})
        accepted = [row for row in candidates if row[4]]
        require(bool(accepted), "fit", "no converged fit satisfying projected-gradient tolerance",
                "REVIEW_REQUIRED")
        objective, delta, gamma, projected, _ = min(accepted)
        require(not any(row[0] < objective - 1e-8 * (1 + abs(objective)) for row in candidates),
                "fit", "lower unconverged candidate needs review", "REVIEW_REQUIRED")
    sigma, details = _lognormal_components(losses, volumes, delta, gamma, context)
    require(math.isclose(objective, details["objective"], rel_tol=1e-10, abs_tol=1e-10),
            "fit", "independent evaluation paths disagree", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return sigma, {**details, "method": method, "year_basis": basis,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "minimization_performed": True, "minimum_certified": False, "time_series_verified": False,
        "delta_identifiable": backend != "analytic_equal_volumes",
        "equal_volume_delta_convention": 0 if backend == "analytic_equal_volumes" else None,
        "optimizer": {"backend": backend, "version": version, "max_iterations": int(iterations),
                      "log_ratio_variance_resolution": 1e-28,
                      "gradient_tolerance": tolerance, "gamma_bounds": None,
                      "projected_gradient_per_year": projected, "runs": diagnostics},
        "credibility_applied": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "numerically_fitted_B_C1_sigma_not_data_qualification_or_supervisory_approval",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-XVII-B-C"]}
