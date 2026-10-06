"""Archived filing precision parameters with explicit, audited analyst values.

This checks declared decimals, never changes fact values or assumes a generic
precision for Decimal items. SHOULD text constraints produce warnings only.
"""
from copy import deepcopy

from .core import NumericOverride, fingerprint
from .reporting_arithmetic import rational


def filing_policy(catalog, overrides):
    """Resolve only known numeric filing parameters; do not mutate resources."""
    original = catalog["filing_parameters"]
    policy = deepcopy(original)
    version = catalog["technical_version"].replace(".", "_").replace("-", "_")
    resource = "reporting_" + version + "_catalog.json"
    if not isinstance(overrides, (list, tuple)):
        raise ValueError("Explicit NumericOverride list/tuple required")
    audit, seen = [], set()
    for override in overrides:
        if (not isinstance(override, NumericOverride) or override.resource != resource
                or not isinstance(override.path, tuple) or len(override.path) != 4
                or override.path[:2] != ("filing_parameters", "parameters") or override.path[-1] != "value"
                or not isinstance(override.path[2], str) or override.path[2] not in policy["parameters"]
                or not isinstance(override.reason, str) or not override.reason.strip()):
            raise ValueError("Known filing parameter path and explicit override reason required")
        key = override.path[2]
        if key in seen:
            raise ValueError("Duplicate filing parameter override")
        seen.add(key)
        if isinstance(override.value, bool) or not isinstance(override.value, (int, float)):
            raise ValueError("Finite JSON numeric override required")
        value = rational(override.value)
        definition = policy["parameters"][key]
        kind = definition["kind"]
        if "integer" in kind and value.denominator != 1:
            raise ValueError("Integral filing parameter required")
        if "nonnegative" in kind and value < 0:
            raise ValueError("Nonnegative filing parameter required")
        audit.append({"resource": resource, "path": list(override.path), "original_value": definition["value"],
                      "value": override.value, "reason": override.reason, "rule": definition["rule"],
                      "source_id": policy["source_id"]})
        definition["value"] = override.value
    p = {key: rational(row["value"]) for key, row in policy["parameters"].items()}
    if not 0 < p["monetary_low_threshold"] < p["monetary_medium_threshold"] < p["monetary_high_threshold"]:
        raise ValueError("Strictly increasing positive monetary bands required")
    return policy, audit, fingerprint({"policy": policy, "overrides": audit})


def check_instance_precision(mapped, *, policy):
    """Check only express numeric/text filing restrictions, not appropriateness."""
    p = {key: rational(row["value"]) for key, row in policy["parameters"].items()}
    findings = []
    for row in mapped:
        dtype, atom = row["metric_check"]["data_type"], row["fact"]["atom"]
        base = {"business_code": row["business_code"], "source_id": policy["source_id"]}
        if dtype == "String":
            text = atom["text"]
            if len(text) > p["string_maximum_length"]:
                findings.append({**base, "status": "WARNING", "rule": "S.2.22", "reason": "TEXT_LENGTH_EXCEEDS_SHOULD_LIMIT"})
            if text != text.strip():
                findings.append({**base, "status": "WARNING", "rule": "S.2.21",
                                 "reason": "QUALIFY_MEANINGFUL_LEADING_OR_TRAILING_WHITESPACE"})
            continue
        if dtype not in ("Monetary", "Decimal", "Integer", "Percent"):
            continue
        decimals = atom["decimals"]
        result = {**base, "status": "PASS", "declared_decimals": decimals}
        if dtype == "Decimal":
            result.update(rule="S.2.18(e)", status="REVIEW_REQUIRED", reason="APPROPRIATE_DECIMAL_PRECISION_EXTERNAL")
        elif dtype == "Integer":
            required = p["integer_decimals"]
            result.update(rule="S.2.18(d)", required_decimals=int(required))
            if decimals != "INF" and decimals != required:
                result.update(status="FAIL", reason="INTEGER_DECIMALS_NOT_ALLOWED")
        else:
            if dtype == "Percent":
                minimum, rule = p["percent_minimum_decimals"], "S.2.18(e)"
            else:
                family = ".".join(row["business_code"].lstrip("{").split(",")[0].split(".")[:3])
                rule = "S.2.18(c)"
                if family in policy["precision_templates"]:
                    minimum = p["monetary_special_decimals"]
                else:
                    magnitude = abs(rational(atom["value"]))
                    minimum = p["monetary_small_decimals"]
                    for band in ("high", "medium", "low"):
                        if magnitude >= p["monetary_" + band + "_threshold"]:
                            minimum = p["monetary_" + band + "_decimals"]
                            break
            result.update(rule=rule, minimum_decimals=int(minimum))
            if decimals != "INF" and decimals < minimum:
                result.update(status="FAIL", reason="DECLARED_PRECISION_BELOW_MINIMUM")
        findings.append(result)
    return {"findings": findings, "values_rounded_or_scaled": False,
            "original_measurement_accuracy_verified": False, "full_report_validated": False}
