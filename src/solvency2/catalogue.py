"""Discover public functions and read bundled independent reporting references."""
import hashlib
from importlib.resources import files
import json

from ._core.core import require

__all__ = ["api_catalogue", "reference_datasets", "reference_dataset", "documentation"]


def _bytes(name):
    root = files("solvency2").joinpath("resources")
    manifest = json.loads(root.joinpath("manifest.json").read_bytes())["sha256"]
    require(isinstance(name, str) and name in manifest, "name", "unknown bundled dataset")
    data = root.joinpath(name).read_bytes()
    require(hashlib.sha256(data).hexdigest() == manifest[name], "resource", "hash mismatch", "RESOURCE_INTEGRITY")
    return data


def _read(name):
    return json.loads(_bytes(name))


def api_catalogue() -> dict:
    """Return fresh function names, domain paths, signatures and contracts."""
    return _read("api_catalogue.json")


def reference_datasets() -> list[str]:
    """Names of additional synthetic reporting datasets (no filesystem paths)."""
    root = files("solvency2").joinpath("resources")
    names = json.loads(root.joinpath("manifest.json").read_bytes())["sha256"]
    return sorted(name for name in names if name.startswith("reference_reporting"))


def reference_dataset(name: str) -> dict:
    """Read an explicitly named dataset, independent of the working directory."""
    require(isinstance(name, str) and name in reference_datasets(), "name", "unknown reference dataset")
    return _read(name)


def documentation(topic: str = "README") -> str:
    """Return bundled English Markdown without needing a browser or source tree.

    Topics: README, API, DATA, PARAMETERS, RECIPES, LIMITATIONS, DEVELOPMENT,
    ACCEPTANCE, DISCLAIMER, SECURITY, THIRD_PARTY_NOTICES, CHANGELOG.
    Names are case-sensitive.
    """
    require(isinstance(topic, str) and topic in {
        "README", "API", "DATA", "PARAMETERS", "RECIPES", "LIMITATIONS", "DEVELOPMENT",
        "DISCLAIMER", "SECURITY", "THIRD_PARTY_NOTICES", "CHANGELOG",
        "ACCEPTANCE",
    }, "topic", "unknown documentation topic")
    return _bytes("documentation/" + topic + ".md").decode("utf-8")
