"""Standard-formula aggregation of externally qualified effective P/R sigmas."""
from fractions import Fraction
import math
import sys
from typing import Mapping

from .aggregation import quadratic
from .core import Context, calculation, effective_resource, exact_keys, number, require


def _product(*values, field):
    """Avoid overflowing multiplication intermediates; reject lost positives."""
    exact = Fraction(1)
    for value in values:
        exact *= Fraction(str(value))
    require(abs(exact) <= Fraction(str(sys.float_info.max)), field,
            "product outside finite numeric range", "REVIEW_REQUIRED")
    result = float(exact)
    require(result != 0 or exact == 0, field, "positive product lost to underflow", "REVIEW_REQUIRED")
    return result


@calculation("DR:article-115", "DR:article-117:1-2", "DR:article-146",
             "DR:article-148:1-2", "DR:annex-III:5-7")
def premium_reserve_parameterised_risk(risk_type: str, segments: Mapping, *,
        parameter_reference: str, context: Context):
    """Aggregate supplied effective sigmas, without repeating NP/ADC adjustments.

    Parameter admissibility, USP approval, HRES determination and sequencing
    are external. Each row declares whether AnnexIII's USP-sigma restriction
    applies; the engine enforces that numeric restriction, not its truth.
    All12 nonlife or4 health-NSLT segments must be explicit, even when empty.
    Existing standard-parameter APIs remain the default automatic selectors.
    """
    require(isinstance(risk_type, str) and risk_type in {"nonlife", "health_nslt"}, "risk_type",
            "nonlife orhealth_nslt required", "UNSUPPORTED_PARAMETER")
    require(isinstance(parameter_reference, str) and bool(parameter_reference.strip()), "parameter_reference",
            "effective parameter provenance, scope and approval qualification required", "MISSING_INPUT")
    profile = effective_resource("profile.json", context)
    table = "health_segments" if risk_type == "health_nslt" else "nonlife_segments"
    matrix = profile["matrices"][table]
    labels = matrix["labels"]
    exact_keys(segments, labels, "segments")
    forced = profile["methods"]["geographic_forced_segments"][risk_type]
    values = profile["scalars"]
    base = number(values["geography_base"]["value"], "geography_base", 0)
    weight = number(values["geography_weight"]["value"], "geography_weight", 0)
    default = number(values["geography_default"]["value"], "geography_default", 0, 1)
    require(default > 0, "geography_default", "positive default required", "REVIEW_REQUIRED")
    multiplier_key = "health_premium_reserve_multiplier" if risk_type == "health_nslt" else "premium_reserve_multiplier"
    multiplier = number(values[multiplier_key]["value"], multiplier_key, 0)
    amounts, audit = {}, {}
    keys = ("premium_volume", "reserve_volume", "geographic_diversification",
            "sigma_premium", "sigma_reserve", "uses_usp_sigma")
    for label in labels:
        row = segments[label]
        exact_keys(row, keys, label)
        require(row["uses_usp_sigma"] is not None, label + ".uses_usp_sigma", "USP-sigma status unknown", "REVIEW_REQUIRED")
        require(isinstance(row["uses_usp_sigma"], bool), label + ".uses_usp_sigma", "explicit boolean required")
        numeric = {key: number(row[key], label + "." + key, 0,
                              1 if key == "geographic_diversification" else None) for key in keys[:-1]}
        div = numeric["geographic_diversification"]
        require(div > 0, label + ".geographic_diversification", "positive DIV required")
        if label in forced or row["uses_usp_sigma"]:
            require(div == default, label + ".geographic_diversification",
                    "profile segment or USP sigma requires the no-diversification factor")
        p = _product(numeric["sigma_premium"], numeric["premium_volume"], field=label + ".premium_sigma_volume")
        r = _product(numeric["sigma_reserve"], numeric["reserve_volume"], field=label + ".reserve_sigma_volume")
        scale = max(p, r)
        # sqrt(p²+p*r+r²) = hypot(p+r/2,sqrt(3)*r/2).
        # Scaling before sums/squares prevents overflow/underflow of squares.
        norm = math.hypot(p / scale + .5 * (r / scale), math.sqrt(.75) * (r / scale)) if scale else 0
        geo = number(base + weight * div, label + ".geography_scale", 0)
        amounts[label] = _product(scale, norm, geo, field=label + ".sigma_volume")
        audit[label] = {**numeric, "uses_usp_sigma": row["uses_usp_sigma"],
                        "sigma_volume": amounts[label], "geography_scale": geo,
                        "geography_forced": label in forced or row["uses_usp_sigma"]}
    scale = max(amounts.values())
    normalized = {key: value / scale if scale else 0 for key, value in amounts.items()}
    norm, aggregation = quadratic(normalized, matrix)
    result = _product(scale, norm, multiplier, field="premium_reserve_capital")
    return result, {"risk_type": risk_type, "segments": audit, "matrix_id": table,
                    "aggregation_scale": scale, "normalised_quadratic_form": aggregation["quadratic_form"],
                    "capital_multiplier": multiplier, "parameter_reference": parameter_reference,
                    "parameter_qualification_status": "EXTERNAL_UNVERIFIED",
                    "effective_sigmas_used_without_further_adjustment": True,
                    "parameter_selection_verified": False, "supervisory_approval_granted_by_engine": False,
                    "internal_model_developed": False,
                    "scope": "prescribed_aggregation_of_qualified_effective_parameters_not_parameter_approval",
                    "_sources": [matrix["source"], context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                                 + (":articles-146-149" if risk_type == "health_nslt" else ":articles-115-117")]}
