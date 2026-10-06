"""Apply explicit closed-table III.2.7 scopes, preserving the original rule audit."""
from itertools import product
import re

from .core import fingerprint
from .reporting_bound_rule import _fields, check_bound_rule
from .reporting_expression import _tokens


def scope_coordinates(expression):
    """No inferred cross-table range pairing; unsupported ambiguity stays review."""
    tokens = _tokens(expression)
    if tokens[:2] != ["scope", "("] or tokens[-1:] != [")"]:
        raise ValueError("Explicit scope(selector,...) required")
    body = tokens[2:-1]
    if not body or len(body) % 2 != 1 or any(t != "," for t in body[1::2]):
        raise ValueError("Explicit scope selector list required")
    tables, axes = {}, []
    for token in body[::2]:
        if not token.startswith("{") or not token.endswith("}"):
            raise ValueError("Scope requires only table selectors")
        fields = _fields(token)
        if not {"t", "f", "fv"} <= fields.keys() or fields.keys() - {"t", "r", "c", "z", "f", "fv"}:
            raise ValueError("Only explicit table/row/column/sheet scopes supported")
        if fields["f"] != "solvency" or fields["fv"] != "solvency2" or fields["t"] in tables:
            raise ValueError("Unknown scope framework or repeated table")
        dimensions = {k: fields[k] for k in ("r", "c", "z") if k in fields}
        if not dimensions:
            raise ValueError("Scope must declare coordinates")
        tables[fields["t"]] = dimensions
        for axis, value in dimensions.items():
            members = [item.strip() for item in value.split(";")]
            if len(set(members)) != len(members) or any(re.fullmatch(axis.upper() + r"[0-9]{4}", m) is None for m in members):
                raise ValueError("Only distinct explicit scope coordinates supported")
            axes.append((fields["t"], axis, members))
    if len(tables) > 1 and any(len(members) != 1 for _, _, members in axes):
        raise ValueError("Cross-table range pairing requires separate qualification")
    count = 1
    for _, _, members in axes:
        count *= len(members)
    if count > 10000:
        raise ValueError("Technical scope expansion limit")
    output = []
    for values in product(*(members for _, _, members in axes)):
        selected = {table: {} for table in tables}
        for (table, axis, _), value in zip(axes, values):
            selected[table][axis] = value
        output.append(selected)
    return output


def complete_coordinates(fields, table, coordinates):
    """Inherit explicit scope, then only unique closed-table axis coordinates.

    No facts are invented: uniqueness is checked against the source table cells,
    not the submitted data. Explicit selector coordinates retain precedence.
    """
    if not table["axes"] or any(axis["IsOpenAxis"] != 0 for axis in table["axes"]):
        raise ValueError("Open-table scope binding not supported")
    completed, inherited, singleton, absent_axes = dict(fields), {}, {}, []
    for axis in ("r", "c", "z"):
        if axis not in completed and axis in coordinates:
            completed[axis] = coordinates[axis]
            inherited[axis] = coordinates[axis]
    for index, axis in enumerate(("r", "c", "z"), 1):
        if axis in completed:
            continue
        members = set()
        for cell in table["cells"]:
            code = cell["BusinessCode"].strip("{}").split(",")
            if len(code) not in (3, 4) or code[0] != fields["t"]:
                raise ValueError("Ambiguous closed-table business coordinate")
            members.add(code[index] if index < len(code) else None)
        if len(members) != 1:
            raise ValueError("Missing coordinate is not a unique closed-table axis")
        if members == {None} and axis == "z":
            if any(a.get("AxisOrientation") == "Z" for a in table["axes"]):
                raise ValueError("Sheet axis conflicts with source business cells")
            absent_axes.append(axis)
            continue
        completed[axis] = next(iter(members))
        singleton[axis] = completed[axis]
    return completed, {"inherited_scope_coordinates": inherited, "source_singleton_coordinates": singleton,
                       "source_absent_axes": absent_axes}


def check_scoped_closed_rule(rule, table_lookup, facts, context, *, technical_version,
                             binding_reference, source, namespace_loader, unit_by_cell=None):
    from .reporting_closed_binding import bind_rule_selectors

    # Clear only the scope actually applied below; filters/joins remain rejected.
    evaluation_rule = {**rule, "Scope": None}
    checks = []
    tables = {}

    def lookup(code):
        if code not in tables:
            tables[code] = table_lookup(code)
        return tables[code]

    for coordinates in scope_coordinates(rule["Scope"]):
        prepared = bind_rule_selectors(evaluation_rule, lookup, facts, context, coordinate_scope=coordinates)
        if unit_by_cell is not None:
            selected = {cell for item in prepared["evidence"].values() for cell in item["cell_ids"]}
            units = {tuple(sorted(unit_by_cell[cell].items())) for cell in selected if unit_by_cell[cell] is not None}
            if len(units) > 1:
                raise ValueError("Cross-unit expression requires qualified dimensional evaluation")
        result = check_bound_rule(evaluation_rule, prepared["bindings"], technical_version=technical_version,
            binding_reference=binding_reference, source=source, namespace_loader=namespace_loader)
        result["evaluation_rule_hash"] = result["rule_hash"]
        result["rule_hash"] = fingerprint(rule)
        checks.append({"coordinates": coordinates, "expression": result, "cell_bindings": prepared["evidence"]})
    return {"value": all(check["expression"]["value"] for check in checks),
            "status": "SCOPED_CLOSED_TABLE_EXPRESSION_COMPONENT", "scope_checks": checks,
            "validation_code": rule["ValidationCode"], "technical_version": technical_version,
            "source": source, "rule_hash": fingerprint(rule), "original_scope": rule["Scope"],
            "binding_reference": binding_reference, "closed_cell_selection_verified": True,
            "binding_qualification_verified": False, "full_report_validated": False,
            "legal_applicability_verified": False, "fact_schema_validated": False,
            "fact_domain_membership_verified": False, "current_deactivations_checked": False,
            "fact_selection_hash": fingerprint({"facts": facts, "fact_context": context})}
