"""Deterministic XML writer for explicitly bound facts, not a report validator.

No taxonomy lookup, inferred defaults, rounding, files or network. The caller
must establish metric/domain membership and filing applicability beforehand.
Expanded QNames avoid guesses about inconsistent source prefix spellings.
"""
from fractions import Fraction
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from .reporting_arithmetic import ReportingNumber
from .reporting_bound_rule import _fact
from .reporting_values import ReportingDate, ReportingQName


NS = {
    "xbrli": "http://www.xbrl.org/2003/instance",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrldi": "http://xbrl.org/2006/xbrldi",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "find": "http://www.eurofiling.info/xbrl/ext/filing-indicators",
}


def _text(value):
    if not isinstance(value, str) or any(
        not (c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF
             or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF)
        for c in value
    ):
        raise ValueError("XML 1.0 text required")
    return value


def _qname(value):
    if not isinstance(value, dict) or set(value) != {"namespace", "local_name"}:
        raise ValueError("Expanded QName required")
    result = ReportingQName(**value)
    if not result.namespace:
        raise ValueError("Nonempty QName namespace required")
    _text(result.namespace)
    return result.namespace, result.local_name


def _decimal(value):
    """Render a terminating rational exactly, without Decimal context rounding."""
    value = Fraction(value)
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("Nonterminating decimal cannot be emitted without rounding")
    scale = max(twos, fives)
    if scale > 4000:
        raise ValueError("TECHNICAL_LIMIT: XML decimal scale")
    numerator = abs(value.numerator) * 2 ** (scale - twos) * 5 ** (scale - fives)
    digits = str(numerator).rjust(scale + 1, "0")
    lexical = digits if not scale else digits[:-scale] + "." + digits[-scale:]
    return ("-" if value < 0 else "") + lexical


def write_instance(*, schema_uri, entity, instant, indicators, facts, namespaces):
    """Return UTF-8 XML bytes for bound atomic facts.

    Each fact has metric (expanded QName), atom (existing reporting atom),
    dimensions (optional list), and unit (expanded QName for numeric atoms).
    A dimension is {dimension, member} or {dimension, domain, text}; text=None
    represents a typed nil member, never a nil business fact. Units are simple
    measures; unsupported compound units are not guessed. Lexical namespace
    aliases are explicit and unique, so QName text is also deterministic.
    """
    _text(schema_uri)
    parsed = urlsplit(schema_uri)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.fragment:
        raise ValueError("Absolute module schema URI required")
    if not isinstance(entity, dict) or set(entity) != {"scheme", "identifier"}:
        raise ValueError("Explicit entity scheme and identifier required")
    if not all(_text(value).strip() for value in entity.values()):
        raise ValueError("Nonempty entity scheme and identifier required")
    ReportingDate(instant)
    if not isinstance(indicators, dict) or not indicators or any(
        not isinstance(key, str) or not key.strip() or type(value) is not bool
        for key, value in indicators.items()
    ):
        raise ValueError("Explicit unique Boolean filing indicators required")
    if not isinstance(namespaces, dict):
        raise ValueError("Explicit namespace bindings required")
    bindings = dict(NS)
    for prefix, uri in namespaces.items():
        if (not isinstance(prefix, str) or re.fullmatch(r"[A-Za-z_][A-Za-z_0-9.-]*", prefix) is None
                or prefix.lower().startswith("xml") or not isinstance(uri, str)
                or not uri or any(c.isspace() for c in uri)
                or (prefix in bindings and bindings[prefix] != uri)):
            raise ValueError("Invalid or conflicting namespace binding")
        bindings[prefix] = _text(uri)
    if len(set(bindings.values())) != len(bindings):
        raise ValueError("One explicit canonical prefix per namespace required")
    reverse = {uri: prefix for prefix, uri in bindings.items()}
    used = {"xbrli", "link", "xlink", "find"}

    def lexical(qname):
        uri, local = qname
        if uri not in reverse:
            raise ValueError("Missing source-bound namespace prefix")
        used.add(reverse[uri])
        return reverse[uri] + ":" + local

    if not isinstance(facts, list) or not facts:
        raise ValueError("Nonempty bound fact list required")
    prepared, identities, contexts, units = [], set(), {()}, set()
    for fact in facts:
        if not isinstance(fact, dict) or not {"metric", "atom"} <= set(fact) or set(fact) - {
            "metric", "atom", "dimensions", "unit"
        }:
            raise ValueError("Explicit supported bound fact fields required")
        metric = _qname(fact["metric"])
        lexical(metric)
        dimensions, dimension_ids = [], set()
        if not isinstance(fact.get("dimensions", []), list):
            raise ValueError("Dimension list required")
        for dim in fact.get("dimensions", []):
            if not isinstance(dim, dict) or set(dim) not in (
                {"dimension", "member"}, {"dimension", "domain", "text"}
            ):
                raise ValueError("Explicit or typed dimension required")
            name = _qname(dim["dimension"])
            lexical(name)
            if name in dimension_ids:
                raise ValueError("Duplicate dimension")
            dimension_ids.add(name)
            if "member" in dim:
                member = _qname(dim["member"])
                lexical(member)
                dimensions.append((name, "explicit", member, ""))
            else:
                domain = _qname(dim["domain"])
                lexical(domain)
                text = dim["text"]
                if text is not None:
                    _text(text)
                else:
                    used.add("xsi")
                dimensions.append((name, "typed_nil" if text is None else "typed", domain, text or ""))
        dimensions = tuple(sorted(dimensions))
        if dimensions:
            used.add("xbrldi")
        contexts.add(dimensions)
        atom = _fact(fact["atom"])
        unit, decimals = None, None
        if isinstance(atom, ReportingNumber):
            unit = _qname(fact.get("unit"))
            lexical(unit)
            units.add(unit)
            decimals = str(fact["atom"]["decimals"])
            value = _decimal(atom.value)
        else:
            if "unit" in fact:
                raise ValueError("Nonnumeric facts must not have units")
            if atom is None:
                raise ValueError("Nil/absent business facts cannot be emitted")
            if isinstance(atom, ReportingQName):
                value = lexical((atom.namespace, atom.local_name))
            elif isinstance(atom, ReportingDate):
                value = atom.lexical
            elif type(atom) is bool:
                value = "true" if atom else "false"
            elif type(atom) is str:
                value = _text(atom)
            else:
                raise ValueError("Unsupported atomic value")
        identity = (metric, dimensions, unit)
        if identity in identities:
            raise ValueError("Duplicate business fact aspects")
        identities.add(identity)
        prepared.append((metric, dimensions, unit, decimals, value))
    context_ids = {key: "c" + str(i) for i, key in enumerate(sorted(contexts))}
    unit_ids = {key: "u" + str(i) for i, key in enumerate(sorted(units))}
    root = ET.Element("xbrli:xbrl", {"xmlns:" + p: bindings[p] for p in sorted(used)})
    ET.SubElement(root, "link:schemaRef", {"xlink:type": "simple", "xlink:href": schema_uri})
    for dimensions, identifier in context_ids.items():
        context = ET.SubElement(root, "xbrli:context", {"id": identifier})
        ent = ET.SubElement(context, "xbrli:entity")
        ET.SubElement(ent, "xbrli:identifier", {"scheme": entity["scheme"]}).text = entity["identifier"]
        period = ET.SubElement(context, "xbrli:period")
        ET.SubElement(period, "xbrli:instant").text = instant
        if dimensions:
            scenario = ET.SubElement(context, "xbrli:scenario")
            for name, kind, member, value in dimensions:
                tag = "explicitMember" if kind == "explicit" else "typedMember"
                node = ET.SubElement(scenario, "xbrldi:" + tag, {"dimension": lexical(name)})
                if kind == "explicit":
                    node.text = lexical(member)
                else:
                    leaf = ET.SubElement(node, lexical(member))
                    if kind == "typed_nil":
                        leaf.set("xsi:nil", "true")
                    else:
                        leaf.text = value
    for unit, identifier in unit_ids.items():
        node = ET.SubElement(root, "xbrli:unit", {"id": identifier})
        ET.SubElement(node, "xbrli:measure").text = lexical(unit)
    filing = ET.SubElement(root, "find:fIndicators")
    for template, filed in sorted(indicators.items()):
        ET.SubElement(filing, "find:filingIndicator", {
            "contextRef": context_ids[()], "find:filed": "true" if filed else "false"
        }).text = _text(template)
    for metric, dimensions, unit, decimals, value in sorted(prepared, key=lambda row: repr(row[:3])):
        attributes = {"contextRef": context_ids[dimensions]}
        if unit is not None:
            attributes.update(unitRef=unit_ids[unit], decimals=decimals)
        ET.SubElement(root, lexical(metric), attributes).text = value
    output = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(output)  # XML well-formedness only; no schema/Formula claim.
    return output
