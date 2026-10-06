"""Audit a supported rule expression on explicitly pre-resolved synthetic/real facts.

This deliberately does not claim a report validation: applicability, entity,
period, units and completeness of candidate fact selection remain externally
qualified. Supported local filters are applied to declared candidates; global
filters/joins/scopes remain rejected, never silently discarded.
"""
import re

from .core import CalculationError, _resource_snapshot, fingerprint, require
from .reporting_arithmetic import ReportingNumber
from .reporting_catalog import _reporting_namespace_bindings, reporting_data
from .reporting_expression import ExpressionError, evaluate, parse
from .reporting_values import ReportingDate, ReportingQName, expand_qname


def _fields(selector):
    """Split only top-level selector attributes, not nested expressions/strings."""
    body = selector[1:-1]
    parts, start, depth, quote, position = [], 0, 0, None, 0
    while position < len(body):
        char = body[position]
        if quote:
            if char == quote:
                if position + 1 < len(body) and body[position + 1] == quote:
                    position += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(body[start:position])
            start = position + 1
        position += 1
    parts.append(body[start:])
    output = {}
    for part in parts:
        key, separator, value = part.partition(":")
        key, value = key.strip(), value.strip()
        require(bool(separator) and bool(key) and bool(value) and key not in output,
                "selector", "ambiguous selector attributes", "UNSUPPORTED_METHOD")
        output[key] = value
    require(depth == 0 and quote is None, "selector", "unbalanced selector", "UNSUPPORTED_METHOD")
    return output


def _fact(record):
    # Explicit tags keep strings/booleans/absence distinct from numeric facts.
    if isinstance(record, dict) and set(record) == {"date"}:
        try:
            return ReportingDate(record["date"])
        except ValueError as error:
            raise CalculationError("INVALID_INPUT", "bindings", str(error)) from error
    if isinstance(record, dict) and set(record) == {"text"}:
        require(isinstance(record["text"], str) and len(record["text"]) <= 100000,
                "bindings", "explicit supported text value required")
        return record["text"]
    if isinstance(record, dict) and set(record) == {"boolean"}:
        require(type(record["boolean"]) is bool, "bindings", "explicit Boolean value required")
        return record["boolean"]
    if isinstance(record, dict) and set(record) == {"absent"}:
        require(record["absent"] is True, "bindings", "absence must be explicitly true")
        return None
    if isinstance(record, dict) and set(record) == {"qname"}:
        value = record["qname"]
        require(isinstance(value, dict) and set(value) == {"namespace", "local_name"},
                "bindings", "expanded QName requires namespace and local_name")
        try:
            return ReportingQName(**value)
        except ValueError as error:
            raise CalculationError("INVALID_INPUT", "bindings", str(error)) from error
    require(isinstance(record, dict) and set(record) == {"value", "decimals"},
            "bindings", "each numeric fact requires exactly value and decimals")
    value = record["value"]
    require(not isinstance(value, bool) and isinstance(value, (str, int, float)),
            "bindings", "JSON numeric value or decimal string required")
    try:
        return ReportingNumber.reported(value, record["decimals"])
    except (ValueError, TypeError, OverflowError) as error:
        raise CalculationError("INVALID_INPUT", "bindings", str(error)) from error


def reporting_bound_rule_check(validation_code: str, bindings: dict, *, technical_version: str,
                              binding_reference: str) -> dict:
    """Check only the supported expression of one archived rule.

    Bind each source variable ID to {value, decimals} or, for seq=True, to
    {values: [{value, decimals}, ...]}. Atomic alternatives are {text: str},
    {boolean: bool}, {qname: {namespace, local_name}}, {date: "YYYY-MM-DD"}
    and {absent: true}; absence
    is not an item within a sequence. All syntactic variables must be supplied;
    there is no implicit zero/default fill, even for an inactive branch. An empty
    sequence must be explicitly supplied. The binding reference records external
    qualification, not an engine verification of correct selection or filing.

    A fact may alternatively carry an explicit dimension list in the wrapper
    {fact: atom, dimensions: [{dimension: {namespace, local_name}, value: atom}]}.
    Dimension admissibility and defaults remain externally qualified. Supported
    local filters run on every supplied candidate; rejected scalars become
    absent, not source-default zero. Sequence candidates are filtered before
    aggregation. Global filters, joins and cross-fact local filters are rejected.
    """
    require(isinstance(validation_code, str) and bool(validation_code), "validation_code", "exact source rule code required")
    require(isinstance(binding_reference, str) and bool(binding_reference.strip()),
            "binding_reference", "external fact-selection/entity/period/unit qualification reference required", "MISSING_INPUT")
    require(isinstance(bindings, dict), "bindings", "source-variable-labelled fact mapping required")
    with _resource_snapshot():
        resource = reporting_data("rules", technical_version=technical_version)
        selected = [row for row in resource["tables"]["vValidationRuleExpressions"]
                    if row["ValidationCode"] == validation_code]
        require(len(selected) == 1, "validation_code", "unknown or ambiguous rule", "UNSUPPORTED_PARAMETER")
        rule = selected[0]
        return check_bound_rule(rule, bindings, technical_version=technical_version,
                                binding_reference=binding_reference, source=resource["source"],
                                namespace_loader=lambda: _reporting_namespace_bindings(technical_version=technical_version))


def check_bound_rule(rule, bindings, *, technical_version, binding_reference, source, namespace_loader):
    """Evaluate an already source-bound rule; reuse loaded data for report batches.

    Same semantics as the public single-rule checker, with no repeated resource
    decompression. The caller supplies a hash-checked rule and namespace loader.
    """
    validation_code = rule["ValidationCode"]
    require(isinstance(binding_reference, str) and bool(binding_reference.strip()),
            "binding_reference", "external qualification reference required", "MISSING_INPUT")
    require(isinstance(bindings, dict), "bindings", "source-variable-labelled mapping required")
    require(rule["IsEnabled"] == 1, "validation_code", "archived rule disabled", "UNSUPPORTED_METHOD")
    require(not any(rule.get(key) for key in ("Filter", "Join", "Scope", "Precondition", "Prerequisites")),
            "validation_code", "rule filter/join/scope/precondition not supported", "UNSUPPORTED_METHOD")
    try:
        tree = parse(rule["Rule"])
    except ExpressionError as error:
        raise CalculationError("UNSUPPORTED_METHOD", "validation_code", str(error)) from error
    selectors, attributes, pending, filter_qnames = {}, {}, [tree], set()
    needs_namespaces = False
    while pending:
        node = pending.pop()
        pending.extend(node.children)
        needs_namespaces = needs_namespaces or node.kind == "qname"
        if node.kind != "selector":
            continue
        fields = _fields(node.value)
        identifier = fields.get("id", "")
        require(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", identifier) is not None,
                "selector", "source variable ID required", "UNSUPPORTED_METHOD")
        require(fields.get("seq") in ("True", "False"),
                "selector", "implicit sequence mode not supported", "UNSUPPORTED_METHOD")
        if fields.get("filter"):
            needs_namespaces = True
            try:
                filter_tree = parse(fields["filter"])
            except ExpressionError as error:
                raise CalculationError("UNSUPPORTED_METHOD", "filter", str(error)) from error
            filter_nodes = [filter_tree]
            while filter_nodes:
                filter_node = filter_nodes.pop()
                filter_nodes.extend(filter_node.children)
                require(filter_node.kind != "selector", "filter", "cross-fact filters unsupported", "UNSUPPORTED_METHOD")
                if filter_node.kind == "qname":
                    filter_qnames.add(filter_node.value)
        require(identifier not in selectors or selectors[identifier] == node.value,
                "selector", "conflicting source definitions for variable", "UNSUPPORTED_METHOD")
        selectors[identifier], attributes[identifier] = node.value, fields
    require(set(bindings) == set(selectors), "bindings", "exactly the declared source variables are required", "MISSING_INPUT")
    namespaces = namespace_loader() if needs_namespaces else None
    try:
        for lexical in filter_qnames:
            expand_qname(lexical, namespaces)
    except ValueError as error:
        raise CalculationError("UNSUPPORTED_METHOD", "filter", str(error)) from error
    resolved, dimension_bindings, applied_filters = {}, {}, []
    for identifier, selector in selectors.items():
        record = bindings[identifier]
        if attributes[identifier]["seq"] == "True":
            require(isinstance(record, dict) and set(record) == {"values"} and isinstance(record["values"], list),
                    "bindings", "sequence variable requires an explicit values list")
            candidates = [_bound_fact(value) for value in record["values"]]
            require(all(value[0] is not None for value in candidates), "bindings",
                    "absence is not an item in a declared sequence; use an explicit empty values list")
            resolved[selector] = [value for value, dimensions in candidates
                                  if _filter_candidate(attributes[identifier].get("filter"), (value, dimensions), namespaces)]
        else:
            value, dimensions = _bound_fact(record)
            accepted = _filter_candidate(attributes[identifier].get("filter"), (value, dimensions), namespaces)
            resolved[selector] = value if accepted else None
            dimension_bindings[selector] = dimensions
        if attributes[identifier].get("filter"):
            applied_filters.append(identifier)
    try:
        value = evaluate(rule["Rule"], resolved.__getitem__, namespaces=namespaces, dimensions=dimension_bindings)
    except ExpressionError as error:
        raise CalculationError("REVIEW_REQUIRED", "expression", str(error)) from error
    require(isinstance(value, bool), "expression", "rule expression did not return boolean", "UNSUPPORTED_METHOD")
    return {"value": value, "status": "REFERENCE_EXPRESSION_COMPONENT", "validation_code": validation_code,
            "technical_version": technical_version, "source": source,
            "rule_hash": fingerprint(rule),
            "input_hash": fingerprint({"bindings": bindings, "binding_reference": binding_reference,
                                       "technical_version": technical_version, "validation_code": validation_code}),
            "selectors": selectors, "binding_reference": binding_reference,
            "local_filters_applied": sorted(applied_filters),
            "fact_dimension_admissibility_verified": False,
            "binding_qualification_verified": False, "legal_applicability_verified": False,
            "fact_schema_validated": False, "fact_domain_membership_verified": False,
            "current_deactivations_checked": False, "full_report_validated": False,
            "archived_is_enabled": rule["IsEnabled"], "archived_include_in_xbrl": rule["IncludeInXBRL"]}


def _bound_fact(record):
    """Optional externally qualified dimensions; no default/domain inference.

    Preserve the original atom form. The alternative is exactly
    {fact: atom, dimensions: [{dimension: {namespace,local_name}, value: atom}]}.
    Dimension values are not facts with measurement uncertainty.
    """
    if not isinstance(record, dict) or set(record) != {"fact", "dimensions"}:
        return _fact(record), None
    value = _fact(record["fact"])
    declared = record["dimensions"]
    require(isinstance(declared, list) and len(declared) <= 1000,
            "dimensions", "explicit bounded dimension declarations required")
    dimensions = {}
    for item in declared:
        require(isinstance(item, dict) and set(item) == {"dimension", "value"},
                "dimensions", "dimension name and tagged value required")
        name = item["dimension"]
        require(isinstance(name, dict) and set(name) == {"namespace", "local_name"},
                "dimensions", "expanded dimension QName required")
        try:
            name = ReportingQName(**name)
        except ValueError as error:
            raise CalculationError("INVALID_INPUT", "dimensions", str(error)) from error
        require(bool(name.namespace) and name not in dimensions, "dimensions", "nonempty namespace and unique dimension required")
        dimension_value = _fact(item["value"])
        require(not isinstance(dimension_value, ReportingNumber) or dimension_value.tolerance == 0,
                "dimensions", "numeric dimension values require exact precision")
        dimensions[name] = dimension_value
    return value, dimensions


def _filter_candidate(expression, candidate, namespaces):
    if not expression:
        return True
    require(candidate[0] is not None, "filter", "an absent scalar is not a candidate fact", "UNSUPPORTED_METHOD")
    try:
        result = evaluate(expression, {}.__getitem__, namespaces=namespaces, current_fact=candidate)
    except ExpressionError as error:
        raise CalculationError("REVIEW_REQUIRED", "filter", str(error)) from error
    require(type(result) is bool, "filter", "local filter must return Boolean", "UNSUPPORTED_METHOD")
    return result
