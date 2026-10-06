"""Strict filing-indicator Boolean expressions, not XPath.

Source: SRC0431 original pp. 36–42 and archived *-find-prec.xml. This
component says whether an archived filing precondition holds, not whether a
rule is legally applicable, currently activated, or satisfied by reported facts.
Unknown indicators are errors, rather than silently meaning not reported.
"""
import re


def reporting_rule_precondition(validation_code: str, indicators: dict, *, technical_version: str, module: str) -> dict:
    """Check only an archived module's filing-indicator condition.

    Supply explicit Boolean declarations for all referenced template indicators.
    True means this one technical condition holds, not that the rule is legally
    applicable, currently active or numerically satisfied. No filing is created.
    """
    from .core import CalculationError, _resource_snapshot, fingerprint
    from .reporting_catalog import _reporting_xbrl_preconditions

    with _resource_snapshot():
        metadata = _reporting_xbrl_preconditions(technical_version=technical_version)
        try:
            result = check_module_precondition(metadata, module, validation_code, indicators)
        except ValueError as error:
            raise CalculationError("UNSUPPORTED_METHOD", "precondition", str(error)) from error
        result["input_hash"] = fingerprint({"validation_code": validation_code, "indicators": indicators,
                                            "technical_version": technical_version, "module": module})
        return result


TOKEN = re.compile(r"\s*(\$find:t[A-Z][A-Z0-9]*(?:\.[0-9]+)+|and\b|or\b|[()])")


def evaluate_precondition(expression, indicators):
    """Evaluate only parentheses, and/or and explicit Boolean indicator values.

    Parse both sides even when a Boolean short circuit would suffice. This
    prevents unsupported syntax or missing declarations from being hidden.
    Limits are operational safeguards, not regulatory numeric parameters.
    """
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 100000:
        raise ValueError("Unsupported filing precondition")
    if not isinstance(indicators, dict) or any(
        not isinstance(key, str) or type(value) is not bool
        for key, value in indicators.items()
    ):
        raise ValueError("Explicit Boolean filing indicators required")
    tokens = []
    position = 0
    expression = expression.strip()
    while position < len(expression):
        match = TOKEN.match(expression, position)
        if match is None:
            raise ValueError("Unsupported filing precondition syntax")
        tokens.append(match[1])
        position = match.end()
        if len(tokens) > 20000:
            raise ValueError("Filing precondition too large")
    cursor = 0

    def atom(depth):
        nonlocal cursor
        if depth > 100 or cursor >= len(tokens):
            raise ValueError("Invalid filing precondition nesting")
        token = tokens[cursor]
        cursor += 1
        if token == "(":
            value = disjunction(depth + 1)
            if cursor >= len(tokens) or tokens[cursor] != ")":
                raise ValueError("Unclosed filing precondition")
            cursor += 1
            return value
        if not token.startswith("$find:t"):
            raise ValueError("Expected filing indicator")
        code = token[len("$find:t"):]
        if code not in indicators:
            raise ValueError("Missing filing indicator: " + code)
        return indicators[code]

    def conjunction(depth):
        nonlocal cursor
        result = atom(depth)
        while cursor < len(tokens) and tokens[cursor] == "and":
            cursor += 1
            right = atom(depth)
            result = result and right
        return result

    def disjunction(depth):
        nonlocal cursor
        result = conjunction(depth)
        while cursor < len(tokens) and tokens[cursor] == "or":
            cursor += 1
            right = conjunction(depth)
            result = result or right
        return result

    result = disjunction(0)
    if cursor != len(tokens):
        raise ValueError("Unexpected filing precondition suffix")
    return result


def check_module_precondition(metadata, module, validation_code, indicators):
    """Check one archived module link, not rule or legal applicability.

    The caller provides a verified, explicitly versioned metadata snapshot.
    No precondition link is not interpreted as either disabled or unconditional.
    Multiple links and dated assertions require a separate qualified resolver.
    """
    if not isinstance(module, str) or module not in metadata["modules"]:
        raise ValueError("Unknown archived reporting module")
    if not isinstance(validation_code, str) or not validation_code:
        raise ValueError("Exact validation code required")
    fragment = "s2md_" + validation_code
    definition = metadata["modules"][module]
    selected = [record for record in definition["preconditions"]
                if metadata["assertions"][record["assertion_key"]]["fragment"] == fragment]
    if len(selected) != 1:
        raise ValueError("No unique archived module precondition")
    record = selected[0]
    assertion = metadata["assertions"][record["assertion_key"]]
    if assertion["kind"] != "{http://xbrl.org/2008/assertion/value}valueAssertion":
        raise ValueError("Existence assertion preconditions require separate handling")
    if any(key.split("}")[-1] in {"fromDate", "toDate"} for key in assertion["attributes"]):
        raise ValueError("Dated assertion requires explicit applicability resolver")
    return {"precondition_met": evaluate_precondition(record["expression"], indicators),
            "technical_version": metadata["technical_version"], "module": module,
            "validation_code": validation_code, "expression": record["expression"],
            "archive_sha256": metadata["archive_sha256"],
            "module_preconditions_sha256": definition["sha256"],
            "assertion_sha256": assertion["sha256"],
            "status": "ARCHIVED_FILING_PRECONDITION_ONLY",
            "legal_applicability_verified": False, "current_deactivations_checked": False,
            "full_report_validated": False}
