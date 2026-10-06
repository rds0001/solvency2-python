"""Acyclic linear look-through on qualified factors, not NAV or risk classification."""
from fractions import Fraction
import heapq
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require
from .loss_given_default import _known_flag, _reference


def _identifier(value, field):
    require(isinstance(value, str) and bool(value.strip()), field, "nonempty string ID required")


def _values(values, field):
    require(isinstance(values, Mapping), field, "labelled numeric mapping required")
    result = {}
    for key, value in values.items():
        _identifier(key, field + ".id")
        result[key] = number(value, field + "." + key)
    return result


def _fraction(value):
    return Fraction(str(value))


def _finite(value, field):
    try:
        result = float(value)
    except OverflowError:
        require(False, field, "look-through amount/factor exceeds finite range", "REVIEW_REQUIRED")
    require(result != 0 or value == 0, field, "nonzero look-through amount/factor underflows", "REVIEW_REQUIRED")
    return result


@calculation("DR:article-84:1-2", "LOOKTHROUGH_GUIDANCE:guideline-2")
def lookthrough_exposure_amount(funds: Mapping, holdings: Mapping, *, exposure_id: str,
                                complete_scope: bool | None, basis_reference: str, context: Context):
    """Sum one underlying exposure across all qualified direct/indirect fund paths.

    Factors are supplied linear multipliers, NOT inferred ownership fractions.
    Signed/leverage inputs remain externally qualified; no normalisation, NAV
    solving, asset classification, fallback completion or risk-charge netting.
    Kahn traversal avoids recursion limits and exponential path enumeration.
    """
    _reference(basis_reference, "basis_reference")
    complete = _known_flag(complete_scope, "complete_scope")
    require(complete, "complete_scope", "complete chosen look-through scope must be qualified", "REVIEW_REQUIRED")
    require(isinstance(funds, Mapping), "funds", "labelled fund mapping required")
    require(bool(funds), "funds", "nonempty fund graph required", "MISSING_INPUT")
    root_values = _values(holdings, "holdings")
    require(bool(root_values), "holdings", "nonempty explicit holding set required", "MISSING_INPUT")
    rows, exposures = {}, set()
    for label, row in funds.items():
        _identifier(label, "fund_id")
        exact_keys(row, ("positions", "fund_links"), label)
        positions = _values(row["positions"], label + ".positions")
        links = _values(row["fund_links"], label + ".fund_links")
        require(bool(positions) or bool(links), label, "empty fund is not complete exposure data", "MISSING_INPUT")
        rows[label] = {"positions": positions, "fund_links": links}
        exposures.update(positions)
    require(set(root_values) <= set(rows), "holdings", "unknown root fund", "MISSING_INPUT")
    for label, row in rows.items():
        require(set(row["fund_links"]) <= set(rows), label + ".fund_links", "unknown underlying fund", "MISSING_INPUT")
    reachable, pending = set(), list(root_values)
    while pending:
        label = pending.pop()
        if label not in reachable:
            reachable.add(label)
            pending.extend(rows[label]["fund_links"])
    require(reachable == set(rows), "funds", "unreachable supplied fund not part of chosen scope")
    require(isinstance(exposure_id, str) and exposure_id in exposures, "exposure_id",
            "explicit known underlying exposure ID required", "UNSUPPORTED_PARAMETER")

    indegree = {label: 0 for label in rows}
    factors = {label: Fraction(0) for label in rows}
    for label, value in root_values.items():
        factors[label] += _fraction(value)
    for row in rows.values():
        for child in row["fund_links"]:
            indegree[child] += 1
    ready = [label for label, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    totals = {key: Fraction(0) for key in exposures}
    contributions, order = {}, []
    while ready:
        label = heapq.heappop(ready)
        order.append(label)
        row = rows[label]
        contributions[label] = {}
        for key, amount in row["positions"].items():
            contribution = factors[label] * _fraction(amount)
            contributions[label][key] = contribution
            totals[key] += contribution
        for child, multiplier in row["fund_links"].items():
            factors[child] += factors[label] * _fraction(multiplier)
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    require(len(order) == len(rows), "fund_links", "cyclic fund structures require separate qualification/solution",
            "UNSUPPORTED_METHOD")
    amounts = {key: _finite(totals[key], "underlying." + key) for key in sorted(totals)}
    audit = {}
    for label in sorted(rows):
        audit[label] = {"positions": dict(sorted(rows[label]["positions"].items())),
                        "fund_links": dict(sorted(rows[label]["fund_links"].items())),
                        "effective_factor": _finite(factors[label], "effective_factor." + label),
                        "allocated_positions": {key: _finite(value, label + ".allocated." + key)
                                                for key, value in sorted(contributions[label].items())}}
    return amounts[exposure_id], {"exposure_id": exposure_id, "underlying_amounts": amounts,
        "funds": audit, "holdings": dict(sorted(root_values.items())), "topological_order": order,
        "complete_scope_declared": complete, "basis_reference": basis_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "completeness_verified": False,
        "factors_normalised": False, "nav_or_ownership_computed": False,
        "asset_or_risk_classification_performed": False, "capital_charge_computed": False,
        "scope": "acyclic_qualified_linear_underlying_amounts_not_full_lookthrough_SCR"}
