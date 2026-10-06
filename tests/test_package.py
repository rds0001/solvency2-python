"""Distribution-facing contracts; no dependency on the original source tree."""
import ast
from dataclasses import replace
import hashlib
import importlib
from importlib.resources import files
import json
from pathlib import Path
import runpy
import socket

import pytest
import solvency2 as s2
from solvency2.catalogue import api_catalogue, documentation, reference_dataset, reference_datasets

ROOT = Path(__file__).resolve().parents[1]


def test_export_catalogue_and_documentation():
    catalog = api_catalogue()
    inherited = {r["name"]: r for r in catalog["functions"] if r["kind"] != "adapter_or_discovery"}
    assert set(inherited) == set(s2.__all__) and len(inherited) == 421
    assert catalog["calculations"] == 399
    cases = {c["id"]: c for c in s2.reference_cases()["cases"]}
    docs = (ROOT / "docs/API.md").read_text()
    for row in catalog["functions"]:
        obj = getattr(importlib.import_module(row["module"]), row["name"])
        assert callable(obj)
        assert "### " + row["name"] + "\n" in docs
        if row["name"] in inherited:
            assert obj is getattr(s2, row["name"])
        if row["kind"] == "calculation":
            assert row["reference_case_ids"] and row["example_case_id"] in cases
            assert all(cases[c]["function"] == row["name"] for c in row["reference_case_ids"])
    catalog["functions"].clear()
    assert len(api_catalogue()["functions"]) == 432


def test_emitted_core_and_resources_match_manifests():
    origin = json.loads((ROOT / "GOLDEN_SOURCE.json").read_text())
    core = files("solvency2._core")
    assert origin["source_public_exports"] == s2.__all__
    for name, expected in origin["emitted_core_code_sha256"].items():
        assert hashlib.sha256(core.joinpath(name).read_bytes()).hexdigest() == expected
    for anchor in ("solvency2", "solvency2._core"):
        root = files(anchor).joinpath("resources")
        manifest = json.loads(root.joinpath("manifest.json").read_bytes())
        for name, expected in manifest["sha256"].items():
            assert hashlib.sha256(root.joinpath(name).read_bytes()).hexdigest() == expected


def test_extra_references_are_local_and_fresh():
    names = reference_datasets()
    assert len(names) == 10
    for name in names:
        original = reference_dataset(name)
        assert original
        original.clear()
        assert reference_dataset(name)
    with pytest.raises(s2.CalculationError):
        reference_dataset("../../LICENSE")


def test_installed_documentation_matches_public_sources():
    for topic in ("README", "API", "DATA", "PARAMETERS", "RECIPES", "LIMITATIONS", "DEVELOPMENT",
                  "DISCLAIMER", "SECURITY", "THIRD_PARTY_NOTICES", "CHANGELOG", "ACCEPTANCE"):
        path = ROOT / (topic + ".md")
        if not path.exists():
            path = ROOT / "docs" / (topic + ".md")
        assert documentation(topic) == path.read_text()
    with pytest.raises(s2.CalculationError):
        documentation("../../private")


def test_optional_numerical_backend_fails_explicitly(monkeypatch):
    import builtins
    original = builtins.__import__

    def no_scipy(name, *args, **kwargs):
        if name == "scipy" or name.startswith("scipy."):
            raise ImportError("synthetic unavailable optional backend")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_scipy)
    base = s2.Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
    with pytest.raises(s2.CalculationError, match="REVIEW_REQUIRED"):
        s2.usp_lognormal_fit(losses=[60, 120, 100, 190, 250], volumes=[80, 100, 140, 200, 300],
                             method="premium", qualification_reference="SYNTHETIC", context=base)


def test_examples_with_connections_denied(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access attempted")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    for name in ("local_inputs.py", "parameters.py"):
        runpy.run_path(str(ROOT / "examples" / name), run_name="__main__")


def test_readme_and_recipes_python_snippets():
    import re
    for name in ("README.md", "docs/RECIPES.md"):
        namespace = {}
        for snippet in re.findall(r"```python\n(.*?)```", (ROOT / name).read_text(), flags=re.S):
            # The README has only in-memory examples; no file export is executed.
            exec(compile(snippet, name, "exec"), namespace)


def test_matrix_override_and_context_guards():
    base = s2.Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
    entry = s2.NumericOverride("profile.json", ("matrices", "health_nslt", "values", 0, 1), .5, "SYNTHETIC")
    scenario = replace(base, overrides=(entry,))
    values = {"premium_reserve": 3, "lapse": 4}
    assert s2.aggregate_risk(values, "health_nslt", context=scenario).value == pytest.approx(37**.5)
    assert s2.aggregate_risk(values, "health_nslt", context=base).value == 5
    with pytest.raises(s2.CalculationError):
        replace(base, overrides=(entry, replace(entry, path=("matrices", "health_nslt", "values", 1, 0)))).validate()
    for changes in ({"mode": "REGULATORY"}, {"profile_id": "latest"}, {"as_of": "2027-01-30"}):
        with pytest.raises(s2.CalculationError):
            s2.intangible_risk(1, context=replace(base, **changes))


def test_source_has_no_network_clients_or_external_engine_imports():
    root = Path(s2.__file__).parent
    forbidden = {"requests", "httpx", "http", "socket", "ftplib", "subprocess", "solvency2_engine"}
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports = [node.module or ""] if node.level == 0 else []
            else:
                continue
            assert not any(name.split(".")[0] in forbidden or name.startswith("urllib.request") for name in imports), path


def test_exported_reference_copy(tmp_path):
    destination = tmp_path / "explicit-export"
    manifest = s2.export_resources(destination)
    for name, expected in manifest["sha256"].items():
        assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == expected
    assert json.loads((destination / "reference_cases.json").read_text()) == s2.reference_cases()
    with pytest.raises(s2.CalculationError):
        s2.export_resources(destination)
