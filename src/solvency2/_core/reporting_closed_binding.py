"""Explicit coordinates in a closed DPM table, without defaults.

Facts are already mapped to version-qualified physical-table business cells.
This is not an XBRL instance importer: entity/period/unit declarations remain
external facts, and no legal applicability or completeness is certified.
"""
from itertools import product
import re


def _validate_context(context):
    if not isinstance(context, dict) or set(context) != {"entity", "period", "unit"} or any(
        not isinstance(value, str) or not value.strip() for value in context.values()
    ):
        raise ValueError("Explicit entity, period and unit required")


def reporting_closed_rule_check(validation_code, facts, *, technical_version, fact_context, binding_reference):
    """Public component boundary: closed DPM cells to a typed expression check.

    Requires declared, externally qualified facts and one entity/period/unit
    context. It does not apply filing indicators, determine legal applicability,
    check current deactivations, expand open tables or construct an XBRL report.
    """
    from solvency2._core import reporting_bound_rule_check, reporting_data, reporting_table
    from solvency2._core.core import CalculationError, _resource_snapshot, fingerprint, require

    require(isinstance(validation_code, str) and bool(validation_code), "validation_code", "exact source code required")
    with _resource_snapshot():
        resource = reporting_data("rules", technical_version=technical_version)
        rules = resource["tables"]["vValidationRuleExpressions"]
        selected = [rule for rule in rules if rule["ValidationCode"] == validation_code]
        require(len(selected) == 1, "validation_code", "unknown or ambiguous archived rule", "UNSUPPORTED_PARAMETER")
        try:
            if selected[0].get("Scope"):
                from .reporting_scope import check_scoped_closed_rule
                from .reporting_catalog import _reporting_namespace_bindings
                return check_scoped_closed_rule(selected[0],
                    lambda code: reporting_table(code, technical_version=technical_version), facts, fact_context,
                    technical_version=technical_version, binding_reference=binding_reference,
                    source=resource["source"], namespace_loader=lambda: _reporting_namespace_bindings(technical_version=technical_version))
            prepared = bind_rule_selectors(selected[0],
                                           lambda code: reporting_table(code, technical_version=technical_version),
                                           facts, fact_context)
        except CalculationError:
            # Preserve resource-integrity and existing controlled error codes.
            raise
        except (ValueError, TypeError) as error:
            raise CalculationError("UNSUPPORTED_METHOD", "closed_binding", str(error)) from error
        result = reporting_bound_rule_check(validation_code, prepared["bindings"], technical_version=technical_version,
                                           binding_reference=binding_reference)
        result.update({"status": "CLOSED_TABLE_EXPRESSION_COMPONENT", "cell_bindings": prepared["evidence"],
                       "closed_cell_selection_verified": True,
                       "fact_selection_hash": fingerprint({"facts": facts, "fact_context": fact_context})})
        return result


def bind_rule_selectors(rule, table_lookup, facts, context, *, coordinate_scope=None):
    """Prepare typed bindings from the actual archived expression selectors.

    table_lookup must use the same explicit technical version as the rule.
    Reuse the expression parser; do not invent another interpretation of its
    selector syntax. A local per-rule table cache avoids repeated decompression.
    """
    from solvency2._core.reporting_bound_rule import _fields
    from solvency2._core.reporting_expression import parse

    _validate_context(context)
    if not isinstance(facts, list):
        raise ValueError("Explicit fact list required")
    if any(rule.get(key) for key in ("Filter", "Join", "Scope", "Precondition", "Prerequisites")):
        raise ValueError("Filtered/joined/scoped rule not supported")
    pending = [parse(rule["Rule"])]
    selectors = {}
    bindings, evidence, tables = {}, {}, {}
    scoped_tables_used = set()
    while pending:
        node = pending.pop()
        pending.extend(node.children)
        if node.kind != "selector":
            continue
        fields = _fields(node.value)
        identifier = fields.get("id")
        if not isinstance(identifier, str) or re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", identifier) is None:
            raise ValueError("Explicit source variable identifier required")
        if identifier in selectors:
            if selectors[identifier] != node.value:
                raise ValueError("Conflicting selectors for one variable")
            continue
        code = fields.get("t")
        if not isinstance(code, str) or not code:
            raise ValueError("Explicit physical table required")
        if code not in tables:
            tables[code] = table_lookup(code)
        coordinate_audit = {}
        if coordinate_scope is not None:
            from .reporting_scope import complete_coordinates
            fields, coordinate_audit = complete_coordinates(fields, tables[code], coordinate_scope.get(code, {}))
            if coordinate_audit["inherited_scope_coordinates"]:
                scoped_tables_used.add(code)
        result = bind_closed_selector(fields, tables[code], facts, context)
        selectors[identifier] = node.value
        bindings[identifier] = result["binding"]
        evidence[identifier] = {key: value for key, value in result.items() if key != "binding"}
        evidence[identifier].update(coordinate_audit)
    if coordinate_scope is not None and scoped_tables_used != set(coordinate_scope):
        raise ValueError("Scope table has no inherited selector coordinates")
    return {"bindings": bindings, "selectors": selectors, "evidence": evidence,
            "status": "CLOSED_TABLE_BINDING_COMPONENT", "full_report_validated": False}


def bind_closed_selector(fields, table, facts, context):
    """Select fully declared r/c/z lists, preserving their source order.

    Only a closed table, explicit coordinates and explicit atomic fact records
    are supported. Missing source cells, shaded cells, duplicate facts and
    missing selected facts fail rather than being treated as a zero fallback.
    Legacy numeric records retain value/decimals. Other atoms use a nested
    ``fact`` record with the same tags as reporting_bound_rule_check. Explicit
    absence is allowed only for scalar selection, never as a sequence item.
    Datatype/schema admissibility remains externally qualified.
    """
    from .reporting_bound_rule import _fact

    required = {"t", "r", "c", "id", "seq", "f", "fv"}
    if not isinstance(fields, dict) or not required <= fields.keys() or set(fields) - required - {"dv", "z"}:
        raise ValueError("Only explicit closed-cell selector attributes supported")
    if fields["f"] != "solvency" or fields["fv"] != "solvency2" or fields["seq"] not in ("True", "False"):
        raise ValueError("Unsupported framework or sequence mode")
    if fields["t"] != table["table"]["TableCode"]:
        raise ValueError("Wrong physical table")
    if not table["axes"] or any(axis["IsOpenAxis"] != 0 for axis in table["axes"]):
        raise ValueError("Open or unqualified table axes not supported")
    _validate_context(context)
    coordinates = []
    count = 1
    for key, prefix in (("r", "R"), ("c", "C"), ("z", "Z")):
        if key == "z" and key not in fields:
            if (not table["cells"] or any(a.get("AxisOrientation") == "Z" for a in table["axes"])
                    or any(len(c["BusinessCode"].strip("{}").split(",")) != 3 for c in table["cells"])):
                raise ValueError("Missing sheet coordinate requires a source table without sheet axis")
            coordinates.append([None])
            continue
        value = fields[key]
        if not isinstance(value, str):
            raise ValueError("Explicit coordinate list required")
        items = [item.strip() for item in value.split(";")]
        if len(set(items)) != len(items) or any(re.fullmatch(prefix + r"[0-9]{4}", item) is None for item in items):
            raise ValueError("Unsupported or repeated coordinate")
        coordinates.append(items)
        count *= len(items)
    if count > 10000 or fields["seq"] == "False" and count != 1:
        raise ValueError("Unsupported cell selection cardinality")
    indexed = {}
    for cell in table["cells"]:
        code = cell["BusinessCode"]
        if code in indexed:
            raise ValueError("Ambiguous physical cell")
        indexed[code] = cell
    if not isinstance(facts, list):
        raise ValueError("Explicit fact list required")
    selected_facts = {}
    for fact in facts:
        if not isinstance(fact, dict) or set(fact) not in (
            {"cell", "context", "value", "decimals"}, {"cell", "context", "fact"}
        ):
            raise ValueError("Explicit cell/context and either value/decimals or one tagged fact required")
        if not isinstance(fact["cell"], str) or not isinstance(fact["context"], dict):
            raise ValueError("Invalid fact cell or context")
        if fact["context"] == context:
            if fact["cell"] in selected_facts:
                raise ValueError("Duplicate fact for cell/context")
            selected_facts[fact["cell"]] = fact
    values, cell_ids, signatures, xbrl_signatures = [], [], [], []
    for row, column, sheet in product(*coordinates):
        code = "{" + ",".join(value for value in (fields["t"], row, column, sheet) if value is not None) + "}"
        cell = indexed.get(code)
        if cell is None or cell["IsShaded"] != 0:
            raise ValueError("Missing or shaded source cell")
        signature = cell["DatapointSignature"]
        if not isinstance(signature, str) or not signature or any(char in signature for char in "*[]?"):
            raise ValueError("Unresolved data-point signature not supported")
        if code not in selected_facts:
            raise ValueError("Missing explicitly qualified fact; no implicit fallback")
        fact = selected_facts[code]
        atom = fact["fact"] if "fact" in fact else {"value": fact["value"], "decimals": fact["decimals"]}
        validated = _fact(atom)
        if validated is None and fields["seq"] == "True":
            raise ValueError("Absence is not a sequence item; no implicit fallback")
        # Keep the language-neutral source input rather than serializing an
        # internal Fraction/QName. The expression boundary revalidates it.
        values.append(dict(atom))
        cell_ids.append(cell["CellID"])
        signatures.append(cell["DatapointSignature"])
        xbrl_signatures.append(cell.get("DPS"))
    return {"binding": {"values": values} if fields["seq"] == "True" else values[0],
            "cell_ids": cell_ids, "datapoint_signatures": signatures,
            "xbrl_signatures": xbrl_signatures,
            "context": dict(context), "context_qualification_verified": False,
            "fallbacks_applied": False}
