"""Explicit context, finite inputs and reproducible reference-component outputs."""
from __future__ import annotations

import gzip
import hashlib
import inspect
import json
import math
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date
from functools import lru_cache, wraps
from importlib.resources import files
from numbers import Real
from typing import Any, Callable, Mapping


class CalculationError(ValueError):
    """Controlled failure with a machine-readable code and offending field."""

    def __init__(self, code: str, field: str, message: str):
        self.code, self.field = code, field
        super().__init__(f"{code}: {field}: {message}")


def require(condition: bool, field: str, message: str, code: str = "INVALID_INPUT") -> None:
    if not condition:
        raise CalculationError(code, field, message)


def number(value: Any, field: str, minimum: float | None = None,
           maximum: float | None = None) -> float:
    if value is None:
        raise CalculationError("MISSING_INPUT", field, "explicit value required")
    require(isinstance(value, Real) and not isinstance(value, bool), field, "finite numeric value required")
    value = float(value)
    require(math.isfinite(value), field, "NaN/Inf not allowed")
    require(minimum is None or value >= minimum, field, f"must be >= {minimum}")
    require(maximum is None or value <= maximum, field, f"must be <= {maximum}")
    return value


def exact_keys(values: Mapping, keys: list[str] | tuple[str, ...], field: str) -> None:
    require(isinstance(values, Mapping), field, "mapping required")
    missing, extra = set(keys) - set(values), set(values) - set(keys)
    require(not missing, field, f"missing keys: {sorted(missing)}", "MISSING_INPUT")
    require(not extra, field, f"unexpected keys: {sorted(str(k) for k in extra)}")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


_RESOURCE_BYTES: ContextVar[dict[str, bytes] | None] = ContextVar("solvency2_resource_bytes", default=None)


@contextmanager
def _resource_snapshot():
    """Pin verified resource bytes only for one public calculation, including nested calls."""
    if _RESOURCE_BYTES.get() is not None:
        yield
        return
    token = _RESOURCE_BYTES.set({})
    try:
        yield
    finally:
        _RESOURCE_BYTES.reset(token)


def _resource_bytes(root, name):
    snapshot = _RESOURCE_BYTES.get()
    if snapshot is None:
        return root.joinpath(name).read_bytes()
    if name not in snapshot:
        snapshot[name] = root.joinpath(name).read_bytes()
    return snapshot[name]


REPORTING_RESOURCES = frozenset(
    f"reporting_{version}_{part}"
    for version in ("2_8_2", "2_8_2_hotfix", "2_10_0")
    for part in ("catalog.json", "structure.json.gz", "cells.json.gz", "dictionary.json.gz", "rules.json.gz",
                 "xbrl_preconditions.json.gz", "validation_status.json.gz")
)


def load_resource(name: str) -> dict:
    require(name in REPORTING_RESOURCES or name in {"profile.json", "profile_2027.json", "rule_profiles.json", "reference_cases.json", "reference_portfolios.json", "manifest.json", "coverage.json", "rfr_monthly.json",
                     "catastrophe_matrices.json", "catastrophe_matrices_2027.json", "catastrophe_regions.json", "catastrophe_regions_2027.json", "catastrophe_weights.json", "catastrophe_weights_2027.json",
                     "catastrophe_zone_map.json", "catastrophe_postcode_groups.json",
                     "catastrophe_zone_map_2027.json", "catastrophe_postcode_groups_2027.json",
                     "catastrophe_geography_raw_2027.json", "catastrophe_administrative_2027.json",
                     "catastrophe_zone_links_2027.json",
                     "catastrophe_geography_raw.json",
                     "catastrophe_administrative.json",
                     "catastrophe_zone_links.json"},
            "resource", "unknown resource")
    root = files("solvency2._core").joinpath("resources")
    data = _resource_bytes(root, name)
    if name != "manifest.json":
        manifest = json.loads(_resource_bytes(root, "manifest.json"))
        require(hashlib.sha256(data).hexdigest() == manifest["sha256"][name],
                name, "resource hash mismatch", "RESOURCE_INTEGRITY")
    return json.loads(gzip.decompress(data) if name.endswith(".json.gz") else data)


def profile_descriptor(profile_id: str) -> dict:
    """Resolve explicit reference-profile metadata; never choose a latest fallback."""
    profiles = load_resource("rule_profiles.json")["profiles"]
    require(isinstance(profile_id, str) and profile_id in profiles, "profile_id",
            "unknown rule profile", "UNSUPPORTED_RULESET")
    return profiles[profile_id]


def _profile_resource_allowed(name: str, descriptor: dict) -> None:
    allowed = descriptor["supported_resources"]
    require(allowed == "BASELINE_RESOURCES" or name in allowed, "resource",
            "resource not qualified for selected profile", "UNSUPPORTED_RULESET")


@lru_cache(maxsize=2)
def catastrophe_data(resource_name: str = "catastrophe_matrices.json") -> dict:
    """Verify the large immutable regulatory resource once per process."""
    return load_resource(resource_name)


@lru_cache(maxsize=1)
def catastrophe_region_data() -> dict:
    """Verify the immutable regional factor/correlation resource once per process."""
    return load_resource("catastrophe_regions.json")


@lru_cache(maxsize=1)
def catastrophe_weight_data() -> dict:
    """Verify sparse Annex X weights once; missing cells remain missing."""
    return load_resource("catastrophe_weights.json")


@lru_cache(maxsize=1)
def catastrophe_zone_links() -> dict:
    """Load checked links from Annex X ordinal to Annex XXII–XXVI axis."""
    return load_resource("catastrophe_zone_links.json")


@lru_cache(maxsize=1)
def catastrophe_postcode_groups() -> dict:
    """Verify Finnish and Danish grouped postcode zones once per process."""
    return load_resource("catastrophe_postcode_groups.json")


@lru_cache(maxsize=1)
def catastrophe_geography_raw() -> dict:
    """Keep conflicting published assignments visible without resolving them."""
    return load_resource("catastrophe_geography_raw.json")


@lru_cache(maxsize=1)
def catastrophe_administrative() -> dict:
    """Keep the Annex IX district spellings and evidence unchanged."""
    return load_resource("catastrophe_administrative.json")


@lru_cache(maxsize=2)
def _rfr_monthly_by_hash(resource_hash: str) -> dict:
    """Internal read-only view; the hash argument separates resource revisions."""
    return load_resource("rfr_monthly.json")


def rfr_monthly_reference() -> dict:
    return _rfr_monthly_by_hash(load_resource("manifest.json")["sha256"]["rfr_monthly.json"])


@dataclass(frozen=True)
class NumericOverride:
    """One explicit analyst scenario value; path addresses an existing numeric resource cell."""

    resource: str
    path: tuple[str | int, ...]
    value: float
    reason: str


def _override_kind(resource: str, path: tuple) -> str:
    if resource == "rfr_monthly.json" and len(path) in {8, 9}:
        if path[0] == "datasets" and path[2:4] == ("supplemental_ltas", "tables") and path[5] == "rows":
            if ((len(path) == 8 and path[7] == "value_percent")
                    or (len(path) == 9 and path[7] == "values_percent")):
                return "number"
    if resource == "rfr_monthly.json" and len(path) == 12:
        if (path[0] == "datasets" and path[2:4] == ("corporate_credit", "series")
                and path[5] == "sectors" and path[7] == "tables" and path[9] == "values"):
            return "number"
    if resource == "rfr_monthly.json" and len(path) == 8:
        if path[0] == "datasets" and path[2] == "series" and path[4] == "variants" and path[6] == "rates":
            return "number"
    if resource == "rfr_monthly.json" and len(path) == 9:
        if path[0] == "datasets" and path[2:4] == ("government_spreads", "tables") and path[5] == "rows" and path[7] == "values_percent":
            return "number"
    if resource == "profile.json":
        if len(path) == 3 and path[0] == "scalars" and path[2] == "value":
            return "number"
        if len(path) == 5 and path[0] == "matrices" and path[2] == "values":
            return "matrix"
        if len(path) == 5 and path[0] == "tables" and path[2] == "rows":
            return "number"
    if resource == "catastrophe_matrices.json" and len(path) == 5:
        if path[0] == "matrices" and path[2] == "values":
            return "matrix"
    if resource == "catastrophe_regions.json":
        if len(path) == 4 and path[0] == "perils" and path[2] == "factors":
            return "nonnegative"
        if len(path) == 6 and path[0] == "perils" and path[2:4] == ("matrix", "values"):
            return "matrix"
    if resource == "catastrophe_weights.json":
        if len(path) == 5 and path[0] == "tables" and path[2] == "weights":
            return "nonnegative"
        if len(path) == 3 and path[0] == "special_factors" and path[2] == "value":
            return "nonnegative"
    raise CalculationError("UNSUPPORTED_PARAMETER", "override.path", "numeric rule cell not supported")


def _cell(data: dict, path: tuple) -> tuple[dict | list, str | int, float]:
    node = data
    for part in path[:-1]:
        if isinstance(node, dict):
            require(isinstance(part, str) and part in node, "override.path", "unknown key",
                    "UNSUPPORTED_PARAMETER")
            node = node[part]
        else:
            require(isinstance(node, list) and isinstance(part, int) and not isinstance(part, bool)
                    and 0 <= part < len(node), "override.path", "unknown row", "UNSUPPORTED_PARAMETER")
            node = node[part]
    last = path[-1]
    if isinstance(node, dict):
        require(isinstance(last, str) and last in node, "override.path", "unknown cell",
                "UNSUPPORTED_PARAMETER")
    else:
        require(isinstance(node, list) and isinstance(last, int) and not isinstance(last, bool)
                and 0 <= last < len(node), "override.path", "unknown column", "UNSUPPORTED_PARAMETER")
    original = node[last]
    require(isinstance(original, Real) and not isinstance(original, bool), "override.path",
            "existing numeric cell required", "UNSUPPORTED_PARAMETER")
    return node, last, float(original)


@lru_cache(maxsize=32)
def _overlaid_resources(overrides: tuple[NumericOverride, ...], profile_resource: str = "profile.json",
                       resource_aliases: tuple[tuple[str, str], ...] = ()) -> tuple[dict, tuple[dict, ...]]:
    """Validate once and keep immutable packaged resources separate from effective scenario data."""
    data, audit = {}, []
    seen = set()
    for entry in overrides:
        require(isinstance(entry, NumericOverride), "overrides", "NumericOverride entries required")
        require(isinstance(entry.resource, str) and isinstance(entry.path, tuple), "overrides",
                "resource and tuple path required")
        require(isinstance(entry.reason, str) and bool(entry.reason.strip()), "override.reason",
                "nonempty explanation required")
        kind = _override_kind(entry.resource, entry.path)
        value = number(entry.value, "override.value", 0 if kind == "nonnegative" else None,
                       1 if kind == "matrix" else None)
        if kind == "matrix":
            require(value >= -1, "override.value", "correlation must be >= -1")
            require(isinstance(entry.path[-1], int) and not isinstance(entry.path[-1], bool)
                    and isinstance(entry.path[-2], int) and not isinstance(entry.path[-2], bool),
                    "override.path", "matrix indices must be integers")
            require(entry.path[-2] != entry.path[-1] or value == 1, "override.value",
                    "correlation diagonal must remain one")
        identifier = (entry.resource, entry.path[:-2], tuple(sorted(entry.path[-2:]))) if kind == "matrix" \
            else (entry.resource, entry.path)
        require(identifier not in seen, "override.path", "duplicate numeric override")
        seen.add(identifier)
        if entry.resource not in data:
            physical = profile_resource if entry.resource == "profile.json" else dict(resource_aliases).get(entry.resource, entry.resource)
            data[entry.resource] = load_resource(physical)
        target, key, original = _cell(data[entry.resource], entry.path)
        target[key] = value
        if kind == "matrix" and entry.path[-2] != entry.path[-1]:
            mirror = (*entry.path[:-2], entry.path[-1], entry.path[-2])
            mirror_target, mirror_key, mirror_original = _cell(data[entry.resource], mirror)
            require(mirror_original == original or mirror_original == value, "override.path",
                    "matrix cell conflicts with an earlier override")
            mirror_target[mirror_key] = value
        audit.append({"resource": entry.resource, "path": list(entry.path),
                      "original": original, "value": value, "reason": entry.reason})
    return data, tuple(audit)


def effective_resource(name: str, context: Context) -> dict:
    """Internal effective data for a validated run; never mutates source resources."""
    descriptor = profile_descriptor(context.profile_id)
    _profile_resource_allowed(name, descriptor)
    aliases = tuple(sorted(descriptor.get("resource_aliases", {}).items()))
    if context.overrides:
        overlaid = _overlaid_resources(context.overrides, descriptor["resource"], aliases)[0]
        if name in overlaid:
            return overlaid[name]
    if name == "profile.json":
        return load_resource(descriptor["resource"])
    physical = dict(aliases).get(name, name)
    if name == "catastrophe_matrices.json":
        return catastrophe_data(physical)
    if physical != name:
        return load_resource(physical)
    cached = {"rfr_monthly.json": rfr_monthly_reference,
              "catastrophe_regions.json": catastrophe_region_data,
              "catastrophe_weights.json": catastrophe_weight_data,
              "catastrophe_postcode_groups.json": catastrophe_postcode_groups,
              "catastrophe_geography_raw.json": catastrophe_geography_raw,
              "catastrophe_administrative.json": catastrophe_administrative,
              "catastrophe_zone_links.json": catastrophe_zone_links}
    return cached[name]() if name in cached else load_resource(name)


def override_audit(context: Context) -> list[dict]:
    if not context.overrides:
        return []
    descriptor = profile_descriptor(context.profile_id)
    aliases = tuple(sorted(descriptor.get("resource_aliases", {}).items()))
    return deepcopy(_overlaid_resources(context.overrides, descriptor["resource"], aliases)[1])


@dataclass(frozen=True)
class Context:
    """Snapshot reference context; deliberately not a regulatory sign-off."""

    as_of: str
    known_at: str
    currency: str
    profile_id: str
    mode: str = "REFERENCE_ONLY"
    overrides: tuple[NumericOverride, ...] = ()

    def validate(self) -> dict:
        try:
            as_of, known_at = date.fromisoformat(self.as_of), date.fromisoformat(self.known_at)
        except (TypeError, ValueError):
            raise CalculationError("INVALID_INPUT", "dates", "ISO dates required") from None
        require(isinstance(self.currency, str) and len(self.currency) == 3
                and self.currency.isascii() and self.currency.isalpha() and self.currency.isupper(),
                "currency", "explicit three-letter uppercase currency required")
        descriptor = profile_descriptor(self.profile_id)
        profile = load_resource(descriptor["resource"])
        require(self.profile_id == profile["profile_id"], "profile_id", "profile catalogue/resource mismatch", "RESOURCE_INTEGRITY")
        require(self.mode == "REFERENCE_ONLY", "mode", "legal applicability review pending", "REVIEW_REQUIRED")
        until = descriptor["reference_until_exclusive"]
        require(as_of >= date.fromisoformat(descriptor["reference_from"])
                and (until is None or as_of < date.fromisoformat(until)),
                "as_of", "outside this document snapshot's reference range", "UNSUPPORTED_RULESET")
        require(known_at >= date.fromisoformat(descriptor["knowledge_not_before"]), "known_at", "documents not available at requested knowledge date",
                "UNSUPPORTED_RULESET")
        require(isinstance(self.overrides, tuple), "overrides", "tuple of NumericOverride entries required")
        if self.overrides:
            for entry in self.overrides:
                require(isinstance(entry, NumericOverride), "overrides", "NumericOverride entries required")
                require(isinstance(entry.resource, str) and isinstance(entry.path, tuple)
                        and all((isinstance(part, str) or isinstance(part, int) and not isinstance(part, bool))
                                for part in entry.path)
                        and isinstance(entry.reason, str), "overrides", "invalid override structure")
                number(entry.value, "override.value")
                _profile_resource_allowed(entry.resource, descriptor)
            _overlaid_resources(self.overrides, descriptor["resource"],
                               tuple(sorted(descriptor.get("resource_aliases", {}).items())))
        return profile


@dataclass(frozen=True)
class Result:
    value: float
    unit: str
    formula_id: str
    sources: tuple[str, ...]
    context: Context
    input_hash: str
    profile_hash: str
    details: dict
    status: str = "REFERENCE_COMPONENT"

    def to_dict(self) -> dict:
        return asdict(self)


CALCULATIONS: dict[str, Callable] = {}


def calculation(*sources: str, unit: str = "currency") -> Callable:
    """Bind validated context, provenance and full input fingerprints at API boundary."""
    def decorate(function: Callable) -> Callable:
        signature = inspect.signature(function)

        def invoke(*args, **kwargs) -> Result:
            try:
                bound = signature.bind(*args, **kwargs)
            except TypeError as exc:
                raise CalculationError("INVALID_INPUT", function.__name__, str(exc)) from None
            bound.apply_defaults()
            context = bound.arguments.get("context")
            require(isinstance(context, Context), "context", "Context required", "MISSING_INPUT")
            profile = context.validate()
            descriptor = profile_descriptor(context.profile_id)
            allowed = descriptor["supported_calculations"]
            require((allowed == "ALL_IMPLEMENTED_BASELINE" or function.__name__ in allowed)
                    and function.__name__ not in descriptor.get("excluded_calculations", []),
                    function.__name__, "calculation not implemented for selected profile", "UNSUPPORTED_RULESET")
            try:
                value, details = function(*args, **kwargs)
                value = number(value, "result")
                if unit in ("zone_ordinal", "region_ordinal"):
                    # Preserve typed lookup output for direct DAG composition
                    # with APIs whose index input deliberately rejects floats.
                    require(value.is_integer() and value > 0, "result", "positive integer geographic ordinal required")
                    value = int(value)
                inputs = {k: v for k, v in bound.arguments.items() if k != "context"}
                input_hash = fingerprint({"formula": function.__name__, "inputs": inputs,
                                          "context": asdict(context)})
            except (OverflowError, ZeroDivisionError) as exc:
                raise CalculationError("NUMERICAL_ERROR", function.__name__, str(exc)) from None
            result_sources = tuple(dict.fromkeys((*sources, *details.pop("_sources", []))))
            audit = override_audit(context)
            if audit:
                details = {**details, "analyst_overrides": audit}
                result_sources = (*result_sources, "ANALYST_OVERRIDE")
            profile_hash = fingerprint({"profile": profile, "overrides": audit}) if audit else fingerprint(profile)
            status = "ANALYST_SCENARIO" if audit else "REFERENCE_COMPONENT"
            if details.get("market_data_kind") == "SYNTHETIC_DEMO":
                status = "SYNTHETIC_DEMO"
                result_sources = (*result_sources, "SYNTHETIC_DEMO")
            return Result(value, context.currency if unit == "currency" else unit,
                          function.__name__, result_sources, context, input_hash,
                          profile_hash, details, status)

        @wraps(function)
        def wrapped(*args, **kwargs) -> Result:
            with _resource_snapshot():
                return invoke(*args, **kwargs)

        CALCULATIONS[function.__name__] = wrapped
        return wrapped
    return decorate


def parameter(parameter_id: str, *, context: Context) -> dict:
    """Return a scalar, labelled matrix or table, including source and profile."""
    base_profile = context.validate()
    profile = effective_resource("profile.json", context)
    audit = override_audit(context)
    metadata = {"analyst_overrides": audit} if audit else {}
    profile_hash = fingerprint({"profile": base_profile, "overrides": audit}) if audit else fingerprint(base_profile)
    category, separator, key = parameter_id.partition("/")
    require(bool(separator) and category in {"scalars", "matrices", "tables", "catastrophe",
                                              "catastrophe_region", "catastrophe_weights",
                                              "catastrophe_links", "catastrophe_geography",
                                              "catastrophe_geography_raw",
                                              "catastrophe_administrative"},
            "parameter_id", "use scalars/name, matrices/name, tables/name, "
            "catastrophe/peril/region, catastrophe_region/peril or "
                            "catastrophe_weights/peril/zone_ordinal, catastrophe_links/peril/region "
                            "catastrophe_geography/region/zone_ordinal or "
                            "catastrophe_geography_raw/FR-or-SI or "
                            "catastrophe_administrative/region/zone_ordinal")
    if category == "catastrophe":
        data = effective_resource("catastrophe_matrices.json", context)
        blocked = data.get("blocked_matrices", {}).get(key)
        require(blocked is None, "parameter_id", f"{key}: source matrix requires review: {blocked}", "REVIEW_REQUIRED")
        require(key in data["matrices"], "parameter_id", "parameter not implemented", "UNSUPPORTED_PARAMETER")
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, "source_sha256": data["source"]["pdf_sha256"],
                **deepcopy(data["matrices"][key]), **metadata}
    if category == "catastrophe_region":
        data = effective_resource("catastrophe_regions.json", context)
        require(key in data["perils"], "parameter_id", "parameter not implemented", "UNSUPPORTED_PARAMETER")
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, "source_sha256": data["source"]["pdf_sha256"],
                **deepcopy(data["perils"][key]), **metadata}
    if category == "catastrophe_weights":
        peril, slash, ordinal = key.partition("/")
        data = effective_resource("catastrophe_weights.json", context)
        require(bool(slash) and peril in data["tables"] and ordinal in data["tables"][peril]["weights"],
                "parameter_id", "parameter not implemented", "UNSUPPORTED_PARAMETER")
        table = data["tables"][peril]
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, "source_sha256": data["source"]["pdf_sha256"],
                "weights": deepcopy(table["weights"][ordinal]),
                "evidence": deepcopy(table["evidence"][ordinal]), "source": table["source"],
                "blocked_regions": {code: reason for cell, reason in data["blocked_cells"].items()
                                    for code in table["weights"][ordinal]
                                    if cell == f"{peril}/{code}/{ordinal}"}, **metadata}
    if category == "catastrophe_links":
        links = effective_resource("catastrophe_zone_links.json", context)["links"]
        require(key in links, "parameter_id", "parameter not implemented", "UNSUPPORTED_PARAMETER")
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, **deepcopy(links[key]), **metadata}
    if category == "catastrophe_geography":
        region, slash, ordinal = key.partition("/")
        data = effective_resource("catastrophe_postcode_groups.json", context)
        require(bool(slash) and region in data["regions"]
                and ordinal in data["regions"][region]["zones"],
                "parameter_id", "postcode group not implemented", "UNSUPPORTED_PARAMETER")
        group = data["regions"][region]
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, "source_sha256": data["source"]["pdf_sha256"],
                "region": region, "zone_ordinal": ordinal, "prefix_length": group["prefix_length"],
                "source": group["source"], **deepcopy(group["zones"][ordinal]), **metadata}
    if category == "catastrophe_geography_raw":
        data = effective_resource("catastrophe_geography_raw.json", context)
        require(key in data["regions"], "parameter_id", "raw geography not implemented",
                "UNSUPPORTED_PARAMETER")
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, "source_sha256": data["source"]["pdf_sha256"],
                **deepcopy(data["regions"][key]), **metadata}
    if category == "catastrophe_administrative":
        region, slash, ordinal = key.partition("/")
        data = effective_resource("catastrophe_administrative.json", context)
        require(bool(slash) and region in data["mapping"] and ordinal in data["mapping"][region],
                "parameter_id", "administrative district not implemented", "UNSUPPORTED_PARAMETER")
        return {"parameter_id": parameter_id, "profile_id": context.profile_id,
                "profile_hash": profile_hash, "source_sha256": data["source"]["pdf_sha256"],
                "region": region, "zone_ordinal": ordinal,
                **deepcopy(data["mapping"][region][ordinal]), **metadata}
    require(key in profile[category], "parameter_id", "parameter not implemented", "UNSUPPORTED_PARAMETER")
    return {"parameter_id": parameter_id, "profile_id": context.profile_id,
            "profile_hash": profile_hash, **deepcopy(profile[category][key]), **metadata}


def scalar(key: str, context: Context | None = None) -> float:
    data = effective_resource("profile.json", context) if context is not None else load_resource("profile.json")
    return data["scalars"][key]["value"]
