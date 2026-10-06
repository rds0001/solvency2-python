"""DPM metric datatype and explicit enumeration membership, not XML validation.

The metric is selected by its exact DPM MemberCode. Canonical DPM metric
prefixes are preserved, never lowercased or guessed into XML namespace URIs.
Actual enumeration QNames use the separately source-bound namespace map.
"""
from copy import deepcopy
import re

from .reporting_arithmetic import ReportingNumber
from .reporting_bound_rule import _fact
from .reporting_values import ReportingDate, ReportingQName, expand_qname


def _index(rows, key):
    result = {}
    for row in rows:
        identifier = row[key]
        if identifier in result:
            raise ValueError("Ambiguous DPM identifier: " + key)
        result[identifier] = row
    return result


def _enumeration_members(tables, metric, members, namespaces):
    """Traverse explicit parent links; Path text is not interpreted or repaired."""
    domains = _index(tables["mDomain"], "DomainID")
    hierarchies = _index(tables["mHierarchy"], "HierarchyID")
    domain, hierarchy = metric.get("ReferencedDomainID"), metric.get("ReferencedHierarchyID")
    if (domain not in domains or domains[domain].get("IsTypedDomain") != 0
            or hierarchy not in hierarchies or hierarchies[hierarchy]["DomainID"] != domain):
        raise ValueError("Explicit consistent enumeration domain/hierarchy required")
    nodes = _index([row for row in tables["mHierarchyNode"] if row["HierarchyID"] == hierarchy], "MemberID")
    if not nodes:
        raise ValueError("Missing enumeration hierarchy nodes")
    children = {key: [] for key in nodes}
    roots = []
    for identifier, node in nodes.items():
        if identifier not in members or members[identifier]["DomainID"] != domain:
            raise ValueError("Hierarchy member/domain mismatch")
        if type(node.get("IsAbstract")) is not int or node["IsAbstract"] not in (0, 1):
            raise ValueError("Explicit abstract-member flag required")
        parent = node.get("ParentMemberID")
        if parent is None:
            roots.append(identifier)
        elif parent in nodes:
            children[parent].append(identifier)
        else:
            raise ValueError("Hierarchy parent missing")
    pending, visited = list(roots), set()
    while pending:
        identifier = pending.pop()
        if identifier in visited:
            raise ValueError("Cyclic or ambiguous member hierarchy")
        visited.add(identifier)
        pending.extend(children[identifier])
    if visited != set(nodes):
        raise ValueError("Cyclic member hierarchy")
    start = metric.get("HierarchyStartingMemberID")
    if start is None:
        selected = set(nodes)
    else:
        included = metric.get("IsStartingMemberIncluded")
        if start not in nodes or type(included) is not int or included not in (0, 1):
            raise ValueError("Unqualified hierarchy starting member")
        selected = {start} if included else set()
        pending = list(children[start])
        while pending:
            identifier = pending.pop()
            selected.add(identifier)
            pending.extend(children[identifier])
    selected = sorted(identifier for identifier in selected if nodes[identifier]["IsAbstract"] == 0)
    qnames = [expand_qname(members[identifier]["MemberXBRLCode"], namespaces) for identifier in selected]
    if len(set(qnames)) != len(qnames):
        raise ValueError("Ambiguous enumeration QName identity")
    return selected, qnames


def check_metric_value(tables, namespaces, metric_code, fact):
    """Check one explicit atomic value against the archived DPM definition.

    Monetary sign, percentage range, units, periods and business restrictions
    are not inferred from primitive datatypes. Extended/timezoned dates, custom types, absence/nil
    and schema constraints remain unsupported rather than silently accepted.
    """
    if not isinstance(metric_code, str) or re.fullmatch(r"[A-Za-z_][A-Za-z_0-9.-]*", metric_code) is None:
        raise ValueError("Exact DPM metric MemberCode required")
    members = _index(tables["mMember"], "MemberID")
    candidates = [metric for metric in tables["mMetric"]
                  if metric.get("CorrespondingMemberID") in members
                  and members[metric["CorrespondingMemberID"]]["MemberCode"] == metric_code]
    if len(candidates) != 1:
        raise ValueError("Unknown or ambiguous DPM metric code")
    metric = candidates[0]
    if metric.get("CustomDataTypeID") is not None or metric.get("IsAbstract") == 1:
        raise ValueError("Custom or abstract metric not supported")
    atom = _fact(fact)
    if atom is None:
        raise ValueError("Absence/nil admissibility is not a datatype decision")
    dtype = metric["DataType"]
    allowed, member_matches = [], None
    if dtype == "Enumeration/Code":
        allowed, qnames = _enumeration_members(tables, metric, members, namespaces)
        type_matches = isinstance(atom, ReportingQName)
        member_matches = type_matches and atom in qnames
        value = member_matches
    else:
        if any(metric.get(field) is not None for field in
               ("ReferencedDomainID", "ReferencedHierarchyID", "HierarchyStartingMemberID")):
            raise ValueError("Additional non-enumeration domain constraints not supported")
        if dtype in ("Monetary", "Decimal", "Percent", "Integer"):
            type_matches = isinstance(atom, ReportingNumber)
            value = type_matches and (dtype != "Integer" or atom.value.denominator == 1)
        elif dtype == "Boolean":
            value = type_matches = type(atom) is bool
        elif dtype == "String":
            value = type_matches = type(atom) is str
        elif dtype == "Date":
            value = type_matches = type(atom) is ReportingDate
        else:
            raise ValueError("Unsupported metric datatype: " + str(dtype))
    return {"value": value, "metric_code": metric_code, "metric_id": metric["MetricID"],
            "metric_xbrl_code": members[metric["CorrespondingMemberID"]]["MemberXBRLCode"],
            "data_type": dtype, "atomic_type_matches": type_matches,
            "enumeration_member_matches": member_matches, "allowed_member_ids": allowed,
            "metric_definition": deepcopy(metric), "status": "DPM_METRIC_VALUE_COMPONENT",
            "xml_schema_validated": False, "presence_or_nil_admissibility_verified": False,
            "context_or_unit_verified": False, "business_rules_executed": False,
            "legal_applicability_verified": False, "full_report_validated": False}


def reporting_metric_value_check(metric_code, fact, *, technical_version):
    """Public explicit-version DPM value check; not a report or XML importer."""
    from .core import CalculationError, _resource_snapshot, fingerprint
    from .reporting_catalog import _reporting_namespace_bindings, reporting_data

    with _resource_snapshot():
        data = reporting_data("dictionary", technical_version=technical_version)
        namespaces = _reporting_namespace_bindings(technical_version=technical_version)
        try:
            result = check_metric_value(data["tables"], namespaces, metric_code, fact)
        except CalculationError:
            raise
        except (ValueError, TypeError) as error:
            raise CalculationError("UNSUPPORTED_METHOD", "metric_value", str(error)) from error
        result.update({"technical_version": technical_version, "source": data["source"],
                       "input_hash": fingerprint({"metric_code": metric_code, "fact": fact,
                                                  "technical_version": technical_version})})
        return result
