"""Explicit technical reporting versions, independent of regulatory contexts.

These accessors expose archived definitions, not a reporting obligation or a
validation result. They do not fetch files, execute source expressions, infer
legal applicability, or mutate official values. Returned data are fresh copies.
"""
from .core import REPORTING_RESOURCES, _resource_snapshot, load_resource, require


_VERSIONS = {"2.8.2": "2_8_2", "2.8.2-hotfix": "2_8_2_hotfix", "2.10.0": "2_10_0"}
_CATEGORIES = {"structure", "cells", "dictionary", "rules"}


def _reporting_validation_metadata(*, technical_version):
    """Load the exact workbook snapshot separately from DPM enabled flags."""
    with _resource_snapshot():
        catalog = reporting_catalog(technical_version=technical_version)
        descriptor = catalog.get("validation_status_resource")
        require(isinstance(descriptor, dict), "technical_version", "workbook evidence unavailable", "RESOURCE_INTEGRITY")
        name = f"reporting_{_VERSIONS[technical_version]}_validation_status.json.gz"
        require(descriptor["resource"] == name and name in REPORTING_RESOURCES,
                "technical_version", "workbook resource binding mismatch", "RESOURCE_INTEGRITY")
        manifest = load_resource("manifest.json")
        require(manifest["sha256"].get(name) == descriptor["sha256"],
                "technical_version", "workbook evidence hash mismatch", "RESOURCE_INTEGRITY")
        data = load_resource(name)
        require(data["technical_version"] == technical_version and data["source"] == descriptor["source"]
                and data["snapshot_date"] == descriptor["snapshot_date"] and data["sheet"] == descriptor["sheet"],
                "technical_version", "workbook source/version/sheet/date mismatch", "RESOURCE_INTEGRITY")
        return data


def _reporting_namespace_bindings(*, technical_version):
    """Return explicit archive-derived bindings from the hash-checked catalog."""
    catalog = reporting_catalog(technical_version=technical_version)
    bindings = catalog.get("xbrl_namespace_bindings")
    require(isinstance(bindings, dict) and bool(bindings)
            and all(isinstance(key, str) and isinstance(value, str) and bool(value) for key, value in bindings.items()),
            "technical_version", "missing or invalid archived QName namespace map", "RESOURCE_INTEGRITY")
    return bindings


def _reporting_xbrl_preconditions(*, technical_version):
    """Load separate XBRL evidence without confusing its source with the DPM."""
    with _resource_snapshot():
        catalog = reporting_catalog(technical_version=technical_version)
        descriptor = catalog.get("xbrl_preconditions_resource")
        require(isinstance(descriptor, dict), "technical_version", "XBRL evidence unavailable", "RESOURCE_INTEGRITY")
        name = f"reporting_{_VERSIONS[technical_version]}_xbrl_preconditions.json.gz"
        require(descriptor["resource"] == name and name in REPORTING_RESOURCES,
                "technical_version", "XBRL resource binding mismatch", "RESOURCE_INTEGRITY")
        manifest = load_resource("manifest.json")
        require(manifest["sha256"].get(name) == descriptor["sha256"],
                "technical_version", "XBRL evidence hash mismatch", "RESOURCE_INTEGRITY")
        data = load_resource(name)
        require(data["technical_version"] == technical_version
                and data["source_id"] == descriptor["source_id"]
                and data["archive_sha256"] == descriptor["archive_sha256"],
                "technical_version", "XBRL evidence source/version mismatch", "RESOURCE_INTEGRITY")
        return data


def reporting_catalog(*, technical_version: str) -> dict:
    """Return module/template/table navigation for one explicit archived release.

    Baseline and hotfix share schema URIs, so neither an URI nor a date uniquely
    selects a version. Module inclusion does not prove an insurer must file it.
    No Context is accepted: technical and regulatory applicability are distinct.
    """
    require(isinstance(technical_version, str) and technical_version in _VERSIONS,
            "technical_version", "choose 2.8.2, 2.8.2-hotfix or 2.10.0 explicitly", "UNSUPPORTED_PARAMETER")
    data = load_resource(f"reporting_{_VERSIONS[technical_version]}_catalog.json")
    require(data["technical_version"] == technical_version, "technical_version",
            "catalog version mismatch", "RESOURCE_INTEGRITY")
    return data


def reporting_data(category: str, *, technical_version: str) -> dict:
    """Load one hash-verified detail category, preserving raw DPM column names.

    Categories: structure, cells, dictionary, rules. Only the requested category
    is decompressed. The rules category contains definitions and module/table
    associations; IsEnabled/IncludeInXBRL are preserved, not interpreted as an
    execution result or a current supervisory deactivation check.
    """
    require(isinstance(category, str) and category in _CATEGORIES, "category",
            "choose structure, cells, dictionary or rules", "UNSUPPORTED_PARAMETER")
    with _resource_snapshot():
        catalog = reporting_catalog(technical_version=technical_version)
        descriptor = catalog["detail_resources"][category]
        expected = f"reporting_{_VERSIONS[technical_version]}_{category}.json.gz"
        require(descriptor["resource"] == expected and expected in REPORTING_RESOURCES,
                "category", "detail resource binding mismatch", "RESOURCE_INTEGRITY")
        manifest = load_resource("manifest.json")
        require(manifest["sha256"].get(expected) == descriptor["sha256"],
                "category", "catalog/detail hash mismatch", "RESOURCE_INTEGRITY")
        data = load_resource(expected)
        require(data["technical_version"] == technical_version and data["source"] == catalog["source"],
                "category", "detail version/source mismatch", "RESOURCE_INTEGRITY")
        require(sorted(data["tables"]) == descriptor["tables"],
                "category", "detail table inventory mismatch", "RESOURCE_INTEGRITY")
        return data


def reporting_table(table_code: str, *, technical_version: str) -> dict:
    """Return one table's cell/axis definitions without expanding open axes.

    Source IDs are local to the explicit technical release. Shaded cells,
    abstract headers, optional keys and hierarchy restrictions retain their
    original meanings and flags; they are never converted into zero inputs.
    This is a definition lookup, not a fact validator or a filing requirement.
    """
    with _resource_snapshot():
        catalog = reporting_catalog(technical_version=technical_version)
        require(isinstance(table_code, str) and table_code in catalog["tables"],
                "table_code", "unknown table in selected technical version", "UNSUPPORTED_PARAMETER")
        structure = reporting_data("structure", technical_version=technical_version)["tables"]
        definitions = [row for row in structure["mTable"] if row["TableCode"] == table_code]
        require(len(definitions) == 1, "table_code", "ambiguous table definition", "RESOURCE_INTEGRITY")
        definition = definitions[0]
        detail = reporting_data("cells", technical_version=technical_version)["tables"]
        cells = [row for row in detail["mTableCell"] if row["TableID"] == definition["TableID"]]
        cell_ids = {row["CellID"] for row in cells}
        axes = [row for row in detail["mTableAxis"] if row["TableID"] == definition["TableID"]]
        axis_ids = {row["AxisID"] for row in axes}
        ordinates = [row for row in detail["mAxisOrdinate"] if row["AxisID"] in axis_ids]
        ordinate_ids = {row["OrdinateID"] for row in ordinates}
        positions = [row for row in detail["mCellPosition"] if row["CellID"] in cell_ids]
        require(all(row["OrdinateID"] in ordinate_ids for row in positions),
                "table_code", "cell position outside selected axes", "RESOURCE_INTEGRITY")
        return {"technical_version": technical_version, "source": catalog["source"],
                "status": "REFERENCE_ONLY", "legal_applicability_verified": False,
                "validation_rules_executed": False, "open_axes_expanded": False,
                "table": definition, "cells": cells, "table_axes": axes,
                "axes": [row for row in detail["mAxis"] if row["AxisID"] in axis_ids],
                "ordinates": ordinates, "cell_positions": positions,
                "categorisations": [row for row in detail["mOrdinateCategorisation"]
                                    if row["OrdinateID"] in ordinate_ids],
                "open_axis_restrictions": [row for row in detail["mOpenAxisValueRestriction"]
                                           if row["AxisID"] in axis_ids]}
