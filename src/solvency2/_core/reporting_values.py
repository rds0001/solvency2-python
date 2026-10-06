"""Explicit nonnumeric reporting atoms, not XML Schema datatype validation.

Qualified names compare their namespace URI and local name, never an alias.
The supported local-name syntax covers archived EIOPA codes; other lexical
forms fail explicitly. Domain membership/filing admissibility remain separate.
"""
from dataclasses import dataclass
from datetime import date as calendar_date
import operator
import re


_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9.-]*")


@dataclass(frozen=True)
class ReportingDate:
    """Timezone-free Gregorian date, restricted to the explicit YYYY-MM-DD form.

    Extended/negative years and timezone-bearing XML dates remain unsupported.
    This atom does not determine a reporting period or an implicit timezone.
    """
    lexical: str

    def __post_init__(self):
        if not isinstance(self.lexical, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", self.lexical) is None:
            raise ValueError("Explicit timezone-free YYYY-MM-DD date required")
        calendar_date.fromisoformat(self.lexical)


@dataclass(frozen=True)
class ReportingQName:
    namespace: str
    local_name: str

    def __post_init__(self):
        if not isinstance(self.namespace, str) or len(self.namespace) > 10000 or any(c.isspace() for c in self.namespace):
            raise ValueError("Explicit namespace URI required")
        if not isinstance(self.local_name, str) or len(self.local_name) > 1000 or _NAME.fullmatch(self.local_name) is None:
            raise ValueError("Supported explicit QName local name required")


def expand_qname(lexical, namespaces):
    """Expand an archived literal; Default is the source's unqualified token.

    The caller must supply source-bound namespace bindings. No URI is guessed
    from a prefix, directory name, country code, or the current network state.
    """
    if lexical == "Default":
        return ReportingQName("", "Default")
    if not isinstance(lexical, str) or lexical.count(":") != 1 or not isinstance(namespaces, dict):
        raise ValueError("Explicit prefixed QName and namespace bindings required")
    prefix, local = lexical.split(":")
    if _NAME.fullmatch(prefix) is None or prefix not in namespaces or not namespaces[prefix]:
        raise ValueError("Unknown QName prefix: " + prefix)
    return ReportingQName(namespaces[prefix], local)


def compare_atomic(operation, left, right):
    """Exact typed comparison; calendar order only for two explicit date atoms."""
    if type(left) is ReportingDate and type(right) is ReportingDate:
        comparisons = {"=": operator.eq, "!=": operator.ne, "<": operator.lt,
                       "<=": operator.le, ">": operator.gt, ">=": operator.ge}
        if operation not in comparisons:
            raise ValueError("Unsupported calendar date operation")
        return comparisons[operation](left.lexical, right.lexical)
    if operation not in ("=", "!=") or type(left) is not type(right) or type(left) not in (str, bool, ReportingQName):
        raise ValueError("Unsupported typed atomic comparison")
    equal = left == right
    return equal if operation == "=" else not equal
