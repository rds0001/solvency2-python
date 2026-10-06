"""Sufficient optimality certificate for Annex XVIII C; not an SDP solver.

All matrix inequalities and the dual bound use exact rational arithmetic on
decimal input representations. Uncertifiable rounded candidates require review.
"""
from collections.abc import Mapping
from fractions import Fraction

from .core import exact_keys, number, require


def _fraction(value, field):
    return Fraction(str(number(value, field)))


def _matrix(supplied, labels, field):
    exact_keys(supplied, labels, field)
    out = {}
    for i in labels:
        exact_keys(supplied[i], labels, field + "." + i)
        for j in labels:
            out[i, j] = _fraction(supplied[i][j], field)
    require(all(out[i, j] == out[j, i] for i in labels for j in labels), field,
            "symmetric matrix required")
    return out


def _psd(matrix, labels, field):
    # For a PSD Schur complement, a zero diagonal entails a zero row/column.
    # Exact elimination handles singular PSD certificates without jitter.
    work = [[matrix[i, j] for j in labels] for i in labels]
    for k in range(len(labels)):
        pivot = work[k][k]
        require(pivot >= 0, field, "matrix is not positive semidefinite", "REVIEW_REQUIRED")
        if pivot == 0:
            require(all(work[i][k] == 0 for i in range(k + 1, len(labels))), field,
                    "zero PSD pivot has nonzero column", "REVIEW_REQUIRED")
        else:
            for i in range(k + 1, len(labels)):
                for j in range(i, len(labels)):
                    work[i][j] -= work[i][k] * work[j][k] / pivot
                    work[j][i] = work[i][j]


def certified_quadratic(inputs, profile):
    """Return exact optimal quadratic value plus explicit proof/scope metadata."""
    exact_keys(inputs, ("components", "correlations", "lower_bounds", "upper_bounds",
                        "standard_components", "optimality_certificate"), "inputs")
    components = inputs["components"]
    require(isinstance(components, Mapping) and bool(components), "components", "nonempty mapping required")
    labels = list(components)
    require(all(isinstance(k, str) and k.strip() for k in labels), "components", "nonempty string IDs required")
    x = {key: Fraction(str(number(value, key, 0))) for key, value in components.items()}
    corr = _matrix(inputs["correlations"], labels, "correlations")
    lower = _matrix(inputs["lower_bounds"], labels, "lower_bounds")
    upper = _matrix(inputs["upper_bounds"], labels, "upper_bounds")
    for i in labels:
        for j in labels:
            lower[i, j], upper[i, j] = max(lower[i, j], -1), min(upper[i, j], 1)
            require(lower[i, j] <= corr[i, j] <= upper[i, j], "correlations",
                    "correlation outside effective bounds")
        require(corr[i, i] == 1, "correlations", "unit diagonal required")
    _psd(corr, labels, "correlations")

    standard = inputs["standard_components"]
    require(isinstance(standard, Mapping) and set(standard) <= set(labels), "standard_components",
            "standard bindings must refer to supplied components")
    bindings, scopes, sources = {}, {}, []
    permitted = {"bscr", "life", "nonlife", "health", "market_up", "market_down"}
    for key, binding in standard.items():
        exact_keys(binding, ("matrix_id", "label"), "standard_components." + key)
        matrix_id, label = binding["matrix_id"], binding["label"]
        require(isinstance(matrix_id, str) and matrix_id in permitted, "matrix_id",
                "AnnexXVIII C(2) standard module/submodule matrix required", "UNSUPPORTED_PARAMETER")
        matrix = profile["matrices"][matrix_id]
        require(isinstance(label, str) and label in matrix["labels"], "label", "unknown standard component")
        parent = "market" if matrix_id.startswith("market_") else matrix_id
        require(parent not in scopes or scopes[parent] == matrix_id, "standard_components",
                "one consistent matrix/scenario per standard parent required")
        scopes[parent] = matrix_id
        require((parent, label) not in bindings.values(), "standard_components", "duplicate standard binding")
        bindings[key] = (parent, label)
        sources.append(matrix["source"])
    whole = {label for parent, label in bindings.values() if parent == "bscr"}
    require(not whole.intersection(parent for parent, _ in bindings.values() if parent != "bscr"),
            "standard_components", "whole module and its submodules cannot both be included")
    for i, (parent, label) in bindings.items():
        matrix = profile["matrices"][scopes[parent]]
        for j, (other_parent, other_label) in bindings.items():
            if parent != other_parent:
                continue
            expected = Fraction(str(matrix["values"][matrix["labels"].index(label)]
                                                     [matrix["labels"].index(other_label)]))
            require(corr[i, j] == expected, "correlations", "standard-formula pair correlation must be retained")
            lower[i, j] = upper[i, j] = expected

    supplied = inputs["optimality_certificate"]
    z = ({(i, j): Fraction(0) for i in labels for j in labels} if supplied is None
         else _matrix(supplied, labels, "optimality_certificate"))
    _psd(z, labels, "optimality_certificate")
    objective = sum((x[i]*x[j]*corr[i, j] for i in labels for j in labels), Fraction(0))
    bound = sum((x[i]*x[i] + z[i, i] for i in labels), Fraction(0))
    for a, i in enumerate(labels):
        for j in labels[a+1:]:
            coefficient = x[i]*x[j] + z[i, j]
            bound += 2 * coefficient * (upper[i, j] if coefficient >= 0 else lower[i, j])
    require(objective == bound, "optimality_certificate",
            "candidate maximum not proved by supplied PSD certificate and bounds; no solver or tolerance relaxation",
            "REVIEW_REQUIRED")
    return objective, {"labels": labels, "optimality_verified": True,
        "optimality_method": "exact_PSD_dual_bound_equality_on_decimal_inputs",
        "optimality_certificate_supplied": supplied is not None,
        "standard_components": dict(standard), "scope_and_bounds_suitability_verified": False,
        "_sources": sources}
