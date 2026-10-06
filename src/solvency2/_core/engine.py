"""Dependency-aware component execution and explicit incomplete-coverage reporting."""
from __future__ import annotations

import copy
from dataclasses import asdict
from pathlib import Path

from .core import (CALCULATIONS, CalculationError, Context, effective_resource, fingerprint,
                   load_resource, override_audit, profile_descriptor, require)

DOMAINS = ("S2-CTX", "S2-VAL", "S2-TP", "S2-RFR", "S2-RI", "S2-MKT", "S2-DEF", "S2-LIFE",
           "S2-HEALTH", "S2-NL", "S2-SCR", "S2-OF", "S2-MCR", "S2-MODEL", "S2-GROUP",
           "S2-ORSA", "S2-REPORT", "S2-AUDIT")


def coverage() -> dict:
    """Return machine-readable achieved scope and remaining limitations."""
    return load_resource("coverage.json")


def reference_cases() -> dict:
    """Return a fresh copy of bundled synthetic cases and independent derivations."""
    return load_resource("reference_cases.json")


def reference_portfolios() -> dict:
    """Return executable synthetic integration DAGs with independent expected values.

    These partial reference portfolios retain explicit external valuation assumptions;
    their baseline expectations do not certify analyst-overridden scenarios.
    """
    return load_resource("reference_portfolios.json")


def rfr_monthly_data() -> dict:
    """Return a fresh synthetic market-data demo and the local-input schema.

    No observed market values are bundled. Dates and coordinates are illustrative.
    Production callers pass their own tables through the explicit market_data
    keyword of the five rfr_archived_* functions, or use solvency2.data curves.
    """
    return load_resource("rfr_monthly.json")


def rule_profiles() -> dict:
    """Return explicit profile intervals and supported scope, not legal approval."""
    return load_resource("rule_profiles.json")


def export_resources(destination: str | Path, *, context: Context | None = None) -> dict:
    """Export verified resources or a marked analyst scenario to a new directory."""
    import json
    destination = Path(destination)
    require(not destination.exists(), "destination", "must be a new directory")
    if context is not None:
        context.validate()
    names = ("profile.json", "reference_cases.json", "reference_portfolios.json", "coverage.json", "rfr_monthly.json", "catastrophe_matrices.json",
                 "catastrophe_regions.json", "catastrophe_weights.json",
                 "catastrophe_zone_map.json", "catastrophe_postcode_groups.json",
                 "catastrophe_geography_raw.json",
                 "catastrophe_administrative.json",
                 "catastrophe_zone_links.json")
    descriptor = profile_descriptor(context.profile_id) if context is not None else None
    if descriptor is not None and descriptor["supported_resources"] != "BASELINE_RESOURCES":
        # No historical category tables or curves silently accompany a future run.
        names = tuple(name for name in names if name in descriptor["supported_resources"])
    contents = {name: (effective_resource(name, context) if context is not None else load_resource(name)) for name in names}
    contents["rule_profiles.json"] = load_resource("rule_profiles.json")
    if context is not None:
        # A context export contains one effective profile under its logical name.
        # Never leave catalogue links to profiles absent from this export.
        exported_descriptor = copy.deepcopy(descriptor)
        exported_descriptor["resource"] = "profile.json"
        # Effective resources are exported under logical names, not package aliases.
        if "resource_aliases" in exported_descriptor:
            exported_descriptor["resource_aliases"] = {}
        contents["rule_profiles.json"]["profiles"] = {context.profile_id: exported_descriptor}
    if context is None:
        # Export every declared physical profile resource, without maintaining
        # a second hard-coded future catalogue that can leave dangling aliases.
        for profile_scope in contents["rule_profiles.json"]["profiles"].values():
            for physical in (profile_scope["resource"], *profile_scope.get("resource_aliases", {}).values()):
                if physical not in contents:
                    contents[physical] = load_resource(physical)
    else:
        baseline_id = load_resource("profile.json")["profile_id"]
        cases = reference_cases()
        cases["cases"] = [case for case in cases["cases"]
                          if case.get("context", {}).get("profile_id", baseline_id) == context.profile_id]
        contents["reference_cases.json"] = cases
        portfolios = reference_portfolios()
        portfolios["portfolios"] = [portfolio for portfolio in portfolios["portfolios"]
                                    if portfolio["context"]["profile_id"] == context.profile_id]
        contents["reference_portfolios.json"] = portfolios
        contents["export_context.json"] = {"context": asdict(context), "profile_scope": exported_descriptor,
                                           "status": "PARTIAL_REFERENCE_ONLY"}
    if context is not None and context.overrides:
        contents["analyst_overrides.json"] = {
            "status": "ANALYST_SCENARIO_NOT_REGULATORY_APPROVAL",
            "context": asdict(context), "overrides": override_audit(context),
            "reference_cases_status": "BASELINE_ONLY", "reference_portfolios_status": "BASELINE_ONLY"}
    destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name, content in contents.items():
        compact = name.startswith("catastrophe_") or name == "rfr_monthly.json"
        data = (json.dumps(content, ensure_ascii=False,
                           indent=None if compact else 2,
                           separators=(",", ":") if compact else None)
                + "\n").encode()
        import hashlib
        hashes[name] = hashlib.sha256(data).hexdigest()
        with (destination / name).open("xb") as stream:
            stream.write(data)
    with (destination / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump({"sha256": hashes}, stream, indent=2)
    return {"files": list(hashes), "sha256": hashes}


class Engine:
    """Execute a DAG of documented atomic APIs; reuse identical nodes within an instance."""

    def __init__(self):
        self._cache: dict[str, dict] = {}

    def run(self, nodes: dict, *, context: Context) -> dict:
        profile = context.validate()
        require(isinstance(nodes, dict), "nodes", "mapping required")
        require(all(isinstance(k, str) and k for k in nodes), "nodes", "nonempty string IDs required")
        outputs, visiting, order, hits = {}, set(), [], []

        def references(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    yield value["$ref"]
                else:
                    for child in value.values():
                        yield from references(child)
            elif isinstance(value, list):
                for child in value:
                    yield from references(child)

        def resolve(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    require(set(value) == {"$ref"} and isinstance(value["$ref"], str), "$ref", "node ID required")
                    # Only values can feed formulas; all provenance stays in node outputs.
                    return evaluate(value["$ref"])["value"]
                return {k: resolve(v) for k, v in value.items()}
            if isinstance(value, list):
                return [resolve(v) for v in value]
            return value

        def evaluate(node_id):
            if node_id in outputs:
                return outputs[node_id]
            require(node_id in nodes, node_id, "missing dependency", "MISSING_INPUT")
            require(node_id not in visiting, node_id, "cyclic dependency", "DEPENDENCY_CYCLE")
            visiting.add(node_id)
            node = nodes[node_id]
            require(isinstance(node, dict) and set(node) == {"function", "inputs"}, node_id,
                    "function and inputs required")
            name = node["function"]
            require(isinstance(name, str) and name in CALCULATIONS, node_id, "unknown formula", "UNSUPPORTED_METHOD")
            require(isinstance(node["inputs"], dict) and "context" not in node["inputs"], node_id,
                    "input mapping without context override required")
            inputs = resolve(node["inputs"])
            try:
                manifest = load_resource("manifest.json")
                key = fingerprint({"function": name, "inputs": inputs, "context": asdict(context),
                                   "profile": fingerprint(profile), "code": manifest["code_sha256"],
                                   "resources": manifest["sha256"]})
            except (ValueError, TypeError):
                raise CalculationError("INVALID_INPUT", node_id, "finite JSON-compatible inputs required") from None
            if key in self._cache:
                result = copy.deepcopy(self._cache[key])
                hits.append(node_id)
            else:
                result = CALCULATIONS[name](**inputs, context=context).to_dict()
                self._cache[key] = copy.deepcopy(result)
            # Propagate demo provenance after cache lookup: identical numeric
            # values can have different origins in different DAG executions.
            demo_dependencies = sorted({ref for ref in references(node["inputs"])
                                        if outputs[ref]["status"] == "SYNTHETIC_DEMO"})
            if demo_dependencies:
                result["status"] = "SYNTHETIC_DEMO"
                result["details"] = {**result["details"], "synthetic_demo_dependencies": demo_dependencies}
                result["sources"] = tuple(dict.fromkeys((*result["sources"], "SYNTHETIC_DEMO")))
            outputs[node_id] = result
            visiting.remove(node_id)
            order.append(node_id)
            return result

        for node_id in nodes:
            evaluate(node_id)
        return {"status": "PARTIAL", "results": outputs, "execution_order": order, "cache_hits": hits,
                "regulatory_total_released": False, "coverage": coverage(), "context": asdict(context),
                "profile_scope": profile_descriptor(context.profile_id)}


def calculate(nodes: dict, *, context: Context) -> dict:
    """Run atomic dependency nodes; pending full scope is always reported as PARTIAL."""
    return Engine().run(nodes, context=context)
