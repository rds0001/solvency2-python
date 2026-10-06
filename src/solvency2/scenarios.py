"""Local numeric scenario batches; existing formula validation remains authoritative."""
from pathlib import Path
from typing import Mapping

from ._core import NumericOverride
from ._core.core import exact_keys, number, require
from .data import _read_local_json

__all__ = ["numeric_overrides_from_dict", "load_numeric_overrides_json"]


def numeric_overrides_from_dict(payload: Mapping) -> tuple[NumericOverride, ...]:
    """Parse schema_version=1 and an overrides list; apply with Context.overrides.

    Resource names and existing numeric paths are validated by the selected
    Context when used. Parsing is not regulatory qualification. Empty batches
    are allowed and mean the original, unmodified parameter set.
    """
    exact_keys(payload, ("schema_version", "overrides"), "scenario")
    require(type(payload["schema_version"]) is int and payload["schema_version"] == 1,
            "schema_version", "only schema version 1 is supported", "UNSUPPORTED_INPUT")
    require(isinstance(payload["overrides"], list), "overrides", "list required")
    entries = []
    for row in payload["overrides"]:
        exact_keys(row, ("resource", "path", "value", "reason"), "override")
        for name in ("resource", "reason"):
            require(isinstance(row[name], str) and bool(row[name].strip()), name, "nonempty string required")
        path = row["path"]
        require(isinstance(path, list) and bool(path)
                and all(isinstance(part, str) or type(part) is int for part in path),
                "path", "nonempty list of string keys/integer indices required")
        entries.append(NumericOverride(row["resource"], tuple(path), number(row["value"], "value"), row["reason"]))
    return tuple(entries)


def load_numeric_overrides_json(path: str | Path) -> tuple[NumericOverride, ...]:
    """Load an explicit local UTF-8 scenario file; never edit installed data."""
    return numeric_overrides_from_dict(_read_local_json(path))
