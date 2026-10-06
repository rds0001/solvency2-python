"""Article144 health-module scope of an externally classified AnnexI obligation."""
from .core import Context, calculation, effective_resource, require
from .loss_given_default import _reference


@calculation("DR:article-113:c", "DR:article-144:4", unit="indicator")
def health_module_scope(lob: str, module: str, *, classification_reference: str, context: Context):
    """Look up a qualified LOB, not the contract's economic classification.

    Both NSLT and SLT health obligations enter the health catastrophe scope.
    This does not qualify any individual accident/pandemic scenario or amount.
    Zero means outside this module's LOB scope, never zero insurer capital.
    """
    _reference(classification_reference, "classification_reference")
    require(isinstance(module, str) and module in ("health", "health_nslt", "health_slt", "health_cat"),
            "module", "explicit health module/submodule required", "UNSUPPORTED_METHOD")
    tables = effective_resource("profile.json", context)["tables"]
    catalogue = {row[0]: row for row in tables["technical_provision_lobs"]["rows"]}
    require(isinstance(lob, str) and lob in catalogue, "lob", "canonical AnnexI LOB string required",
            "UNSUPPORTED_PARAMETER")
    rows = tables["health_module_scope"]["rows"]
    mapping = {row[0]: row for row in rows}
    require(len(mapping) == len(rows) and all(key in catalogue for key in mapping),
            "health_module_scope", "unique known LOB entries required", "RESOURCE_INTEGRITY")
    require(all(row[1] in ("health_nslt", "health_slt") for row in rows),
            "health_module_scope", "unknown health submodule", "RESOURCE_INTEGRITY")
    primary = mapping[lob][1] if lob in mapping else None
    applicable = ["health", primary, "health_cat"] if primary else []
    sources = [catalogue[lob][4]]
    if primary:
        sources.append(mapping[lob][2])
    return int(module in applicable), {
        "lob": lob, "lob_label_de": catalogue[lob][2], "module": module,
        "primary_health_submodule": primary, "applicable_health_modules": applicable,
        "classification_reference": classification_reference, "classification_status": "EXTERNAL_UNVERIFIED",
        "contract_classification_verified": False, "catastrophe_subscenario_qualified": False,
        "capital_charge_computed": False, "scope": "health_module_scope_of_qualified_AnnexI_LOB_only",
        "_sources": sources}
