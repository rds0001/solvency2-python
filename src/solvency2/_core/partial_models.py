"""Annex XVIII fixed integration arithmetic, never an insurer-owned model.

Scope partition, method suitability and approvals are qualified externally.
Decimal intermediates avoid squaring binary64 currency amounts into infinity.
"""
from collections.abc import Mapping
from decimal import Decimal, localcontext
import math

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .external_models import _reference
from .partial_model_certificate import certified_quadratic


def _decimal(value, field):
    return Decimal(str(number(value, field, 0)))


def _out(value, field):
    result = float(value)
    require(math.isfinite(result) and (result != 0 or value == 0), field,
            "result outside supported finite numeric range", "NUMERICAL_ERROR")
    return result


def _sqrt(value, field):
    require(value >= 0, field, "negative radicand; qualified inputs require review", "REVIEW_REQUIRED")
    return value.sqrt()


def _fixed(technique, inputs, profile, path="inputs", ancestors=()):
    require(isinstance(inputs, Mapping), path, "input mapping required")
    require(id(inputs) not in ancestors and len(ancestors) < 64, path,
            "cyclic or excessive integration nesting", "INVALID_INPUT")
    ancestors = (*ancestors, id(inputs))
    if technique == 2:
        squared, details = certified_quadratic(inputs, profile)
        value = Decimal(squared.numerator) / Decimal(squared.denominator)
        return _sqrt(value, path), details
    if technique == 1:
        exact_keys(inputs, ("components", "standard_formula_remainder"), path)
        components = inputs["components"]
        require(isinstance(components, Mapping) and bool(components), path + ".components",
                "nonempty mapping of separately computed model components required")
        require(all(isinstance(key, str) and key.strip() for key in components), path, "nonempty component IDs required")
        amounts = {key: _decimal(value, key) for key, value in components.items()}
        remainder = _decimal(inputs["standard_formula_remainder"], "standard_formula_remainder")
        return sum(amounts.values(), remainder), {"model_components": {k: _out(v, k) for k, v in amounts.items()},
            "standard_formula_remainder": _out(remainder, path), "_sources": []}
    if technique == 3:
        exact_keys(inputs, ("ss", "pc", "ps", "p", "s", "sc"), path)
        v = {key: _decimal(value, key) for key, value in inputs.items()}
        ss, pc, ps, p, s, sc = (v[key] for key in ("ss", "pc", "ps", "p", "s", "sc"))
        d1, d2 = int(not ss or not sc), int(not ps or not pc)
        w1 = (s*s - ss*ss - sc*sc) / (d1 + 2*ss*sc)
        w3 = (p*p - ps*ps - pc*pc) / (d2 + 2*ps*pc)
        require(abs(w1) <= 1 and abs(w3) <= 1, path,
                "implied correlations outside [-1,1]; no clipping", "REVIEW_REQUIRED")
        w2 = w1*w3 + _sqrt((1-w1*w1)*(1-w3*w3), path) / 2
        value = _sqrt(ss*ss + 2*ss*(w1*pc + w2*ps) + p*p, path)
        return value, {"omega1": _out(w1, path), "omega2": _out(w2, path), "omega3": _out(w3, path),
                       "d1": d1, "d2": d2, "_sources": []}

    keys = ("matrix_id", "model_charge", "standard_formula_remainder", "modeled_components", "components")
    exact_keys(inputs, keys + (("separate_model_components",) if technique == 4 else ()), path)
    matrix_id = inputs["matrix_id"]
    require(isinstance(matrix_id, str) and matrix_id in profile["matrices"], "matrix_id",
            "supported standard-formula matrix required", "UNSUPPORTED_PARAMETER")
    matrix = profile["matrices"][matrix_id]
    labels = matrix["labels"]
    modeled = inputs["modeled_components"]
    require(isinstance(modeled, (list, tuple)) and all(isinstance(k, str) for k in modeled),
            "modeled_components", "explicit list of matrix component IDs required")
    require(len(set(modeled)) == len(modeled) and set(modeled) <= set(labels), "modeled_components",
            "unique modeled IDs within the selected matrix required")
    exact_keys(inputs["components"], labels, path + ".components")
    components, children, sources = {}, {}, [matrix["source"]]
    for label in labels:
        supplied = inputs["components"][label]
        if isinstance(supplied, Mapping):
            amount, details = _fixed(technique, supplied, profile, path + "." + label, ancestors)
            sources.extend(details.pop("_sources"))
            children[label] = {"value": _out(amount, label), **details, "intangible_charge": 0}
        else:
            amount = _decimal(supplied, label)
        components[label] = amount
    p = _decimal(inputs["model_charge"], "model_charge")
    ss = _decimal(inputs["standard_formula_remainder"], "standard_formula_remainder")
    outside = [key for key in labels if key not in modeled]
    corr = {(a, b): Decimal(str(matrix["values"][i][j]))
            for i, a in enumerate(labels) for j, b in enumerate(labels)}
    separate = inputs.get("separate_model_components", {})
    require(isinstance(separate, Mapping) and set(separate) <= set(modeled), "separate_model_components",
            "separate model values must belong to modeled scope")
    separate = {key: _decimal(value, key) for key, value in separate.items()}
    if technique == 4:
        cross = sum((corr[i, j] * separate.get(i, components[i]) * components[j]
                     for j in outside for i in modeled), Decimal(0))
        contribution = 2 * cross
        extra = {"separate_model_components": {k: _out(v, k) for k, v in separate.items()}}
    else:
        denominator_squared = sum((corr[i, j] * components[i] * components[j]
                                   for i in modeled for j in modeled), Decimal(0))
        require(denominator_squared > 0, "modeled_components",
                "technique5 denominator must be positive; no invented zero exception", "REVIEW_REQUIRED")
        denominator = denominator_squared.sqrt()
        cross = sum((corr[i, j] * components[i] * components[j]
                     for j in outside for i in modeled), Decimal(0))
        contribution = 2 * p * cross / denominator
        extra = {"modeled_standard_denominator": _out(denominator, path)}
    value = _sqrt(p*p + ss*ss + contribution, path)
    return value, {"matrix_id": matrix_id, "modeled_components": list(modeled),
        "components": {k: _out(v, k) for k, v in components.items()},
        "model_charge": _out(p, path), "standard_formula_remainder": _out(ss, path),
        "children": children, **extra, "_sources": sources}


@calculation("DR:article-239", "DR:annex-XVIII")
def partial_model_bscr(technique: int, inputs: Mapping, intangible_charge: float, *,
                       qualification_reference: str, context: Context):
    """Annex XVIII techniques1-5, with recursive4/5 and certified external2.

Model charges and scalar module inputs are externally qualified. Nested inputs
use the same technique, with no intangible charge below the outermost BSCR.
    Technique2 verifies a PSD dual certificate of constrained maximisation;
    it does not develop or run an insurer model or an optimisation solver.
"""
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(technique, int) and not isinstance(technique, bool), "technique", "integer technique required")
    require(technique in (1, 2, 3, 4, 5), "technique",
            "Annex XVIII techniques1-5 supported", "UNSUPPORTED_METHOD")
    profile = effective_resource("profile.json", context)
    with localcontext() as decimal_context:
        decimal_context.prec = 80
        intangible = _decimal(intangible_charge, "intangible_charge")
        value, details = _fixed(technique, inputs, profile)
        total = _out(value + intangible, "result")
    return total, {**details, "technique": technique, "intangible_charge": float(intangible),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "model_generated": False, "method_suitability_verified": False, "regulatory_total_released": False,
        "scope": "annex_XVIII_integration_of_externally_qualified_inputs",
        "source_note": "A(2)(a) says C-F; B and A(3)(a) expressly include technique1",
        "_sources": details["_sources"] + [context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                                           + ":annex-XVIII"]}
