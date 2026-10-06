"""Bind an archived DPM datapoint signature to original schema declarations.

No case-folding aliases or inferred open-axis values. This common boundary
serves closed and open tables; hierarchy/row-key completeness remains a
separate report validation obligation, not a claim made by this projection.
"""
import re

from .reporting_metric import check_metric_value, _enumeration_members
from .reporting_values import expand_qname


def bind_cell_fact(cell, atom, open_dimensions, *, tables, namespaces, declarations, unit=None):
    """Return a source-bound XML fact plus explicit unchecked obligations.

    open_dimensions maps exact DPS dimension prefixes to either an explicit
    member QName string or typed text (None only for a nillable typed domain).
    The caller must first bind the cell to its requested module/table/version.
    """
    if cell.get("IsShaded") != 0 or not cell.get("DPS"):
        raise ValueError("Unshaded cell with explicit DPS required")
    if not isinstance(open_dimensions, dict):
        raise ValueError("Explicit open dimension mapping required")

    def declared(lexical, *, reference=False):
        q = expand_qname(lexical, namespaces)
        key = "{" + q.namespace + "}" + q.local_name
        if key not in declarations:
            raise ValueError("QName not declared in archived dictionary: " + lexical)
        declaration = declarations[key]
        if declaration["namespace"] != q.namespace or declaration["local_name"] != q.local_name:
            raise ValueError("Dictionary declaration identity mismatch")
        # Dimension names and explicit members occur as QName references, not
        # element instances. XML Schema abstract=true does not prohibit those
        # references; dimensional usable/hierarchy constraints are separate.
        if not reference and declaration["attributes"].get("abstract", "false") not in ("false", "0"):
            raise ValueError("Abstract dictionary element cannot be emitted")
        return {"namespace": q.namespace, "local_name": q.local_name}, declaration

    parts = []
    for part in cell["DPS"].split("|"):
        match = re.fullmatch(r"([^()]+)\(([^()]*)\)", part)
        if not match:
            raise ValueError("Unsupported archived datapoint signature")
        parts.append(match.groups())
    if not parts or parts[0][0] != "MET" or any(name == "MET" for name, _ in parts[1:]):
        raise ValueError("Exactly one leading DPS metric required")
    metric, declaration = declared(parts[0][1])
    if declaration["attributes"].get("{http://www.xbrl.org/2003/instance}periodType") != "instant":
        raise ValueError("Only declared instant metrics supported")
    checked = check_metric_value(tables, namespaces, metric["local_name"], atom)
    if not checked["value"]:
        raise ValueError("Fact violates archived DPM metric datatype/domain")
    # Bind the actual DPS namespace, not the differently cased MemberXBRLCode.
    # The local metric code is separately resolved uniquely by the DPM checker.
    dimensions = {row["DimensionXBRLCode"]: row for row in tables["mDimension"]}
    domains = {row["DomainID"]: row for row in tables["mDomain"]}
    members = {row["MemberXBRLCode"]: row for row in tables["mMember"]}
    result, omitted_defaults, consumed, seen = [], [], set(), set()
    for name, member in parts[1:]:
        if name in seen or name not in dimensions:
            raise ValueError("Duplicate or unknown DPS dimension")
        seen.add(name)
        dimension = dimensions[name]
        domain = domains.get(dimension["DomainID"])
        if domain is None:
            raise ValueError("Missing dimension domain")
        dimension_qname, _ = declared(name, reference=True)
        restriction = re.fullmatch(r"\*(\?)?\[([^;\[\]]+);([^;\[\]]+);([01])\]", member)
        if member.startswith("*") and member != "*" and restriction is None:
            raise ValueError("Unsupported open dimension restriction")
        if member == "*" or restriction is not None:
            if name not in open_dimensions:
                raise ValueError("Missing explicit open dimension: " + name)
            member = open_dimensions[name]
            consumed.add(name)
        elif name in open_dimensions:
            raise ValueError("Fixed DPS dimension cannot be overridden")
        if dimension["IsTypedDimension"] == 1:
            if restriction is not None:
                raise ValueError("Explicit hierarchy restriction on typed dimension")
            if domain.get("IsTypedDomain") != 1 or domain.get("DataType") != "String":
                raise ValueError("Unsupported typed dimension domain")
            if member is None:
                if domain.get("IsNillable") != 1:
                    raise ValueError("Typed nil forbidden by DPM domain")
            elif not isinstance(member, str):
                raise ValueError("Typed string dimension requires text")
            domain_qname, _ = declared(domain["DomainXBRLCode"])
            result.append({"dimension": dimension_qname, "domain": domain_qname, "text": member})
        elif dimension["IsTypedDimension"] == 0:
            if not isinstance(member, str) or member not in members:
                raise ValueError("Unknown explicit dimension member")
            if members[member]["DomainID"] != domain["DomainID"]:
                raise ValueError("Explicit member outside dimension domain")
            member_qname, _ = declared(member, reference=True)
            if restriction is not None:
                _, hierarchy_code, start_code, include = restriction.groups()
                hierarchies = [h for h in tables["mHierarchy"] if h["DomainID"] == domain["DomainID"]
                               and h["HierarchyCode"] == hierarchy_code]
                starts = [m for m in tables["mMember"] if m["DomainID"] == domain["DomainID"]
                          and m["MemberCode"] == start_code]
                if len(hierarchies) != 1 or len(starts) != 1:
                    raise ValueError("Ambiguous open-axis hierarchy or starting member")
                selection = {"ReferencedDomainID": domain["DomainID"],
                             "ReferencedHierarchyID": hierarchies[0]["HierarchyID"],
                             "HierarchyStartingMemberID": starts[0]["MemberID"],
                             "IsStartingMemberIncluded": int(include)}
                allowed, _ = _enumeration_members(tables, selection,
                                                  {m["MemberID"]: m for m in tables["mMember"]}, namespaces)
                if members[member]["MemberID"] not in allowed:
                    raise ValueError("Member outside allowed open-axis hierarchy")
            default_id = dimension.get("DefaultMemberID")
            is_default = (members[member]["MemberID"] == default_id if default_id is not None
                          else members[member].get("IsDefaultMember") == 1)
            if is_default:
                if restriction is None or restriction[1] != "?":
                    raise ValueError("Default omission not qualified by archived DPS")
                omitted_defaults.append({"dimension": dimension_qname, "member": member_qname,
                                         "dps_restriction": restriction[0]})
                continue
            result.append({"dimension": dimension_qname, "member": member_qname})
        else:
            raise ValueError("Explicit dimension kind required")
    if consumed != set(open_dimensions):
        raise ValueError("Unused or undeclared open dimension inputs")
    numeric = checked["data_type"] in ("Monetary", "Decimal", "Percent", "Integer")
    if numeric != (unit is not None):
        raise ValueError("Unit required exactly for numeric facts")
    fact = {"metric": metric, "atom": atom, "dimensions": result}
    if numeric:
        fact["unit"] = unit
    return {"fact": fact, "metric_check": checked, "cell_id": cell["CellID"],
            "business_code": cell["BusinessCode"], "schema_declaration": declaration,
            "omitted_explicit_defaults": omitted_defaults, "dps_hierarchy_restrictions_verified": True,
            "open_axis_hierarchies_verified": False, "row_key_constraints_verified": False,
            "dimensional_relationships_verified": False, "full_report_validated": False}
