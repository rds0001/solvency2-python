"""Standalone stdlib-only smoke for an installed wheel, outside the source tree.

Usage: python -I -B installed_smoke.py EXPECTED_VENV_PREFIX EXAMPLES_DIRECTORY
This script intentionally uses no pytest or original engine imports.
"""
import hashlib
import importlib
from importlib import metadata
from importlib.resources import files
import json
from pathlib import Path
import runpy
import sys


def main():
    prefix = Path(sys.argv[1]).resolve()
    examples = Path(sys.argv[2]).resolve()

    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto"}:
            raise AssertionError("Network access attempted: " + event)
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
            mode, flags = args[1:]
            if path.is_relative_to(prefix) and ((mode and any(c in mode for c in "wax+")) or flags & 3):
                raise AssertionError("Write inside installed environment: " + str(path))

    sys.addaudithook(audit)
    import solvency2 as s2
    from solvency2.catalogue import api_catalogue, documentation, reference_dataset, reference_datasets

    installed = Path(s2.__file__).resolve()
    assert installed.is_relative_to(prefix), installed
    assert "solvency2_engine" not in sys.modules
    assert metadata.version("solvency2") == s2.__version__ == "0.5.0"
    package_metadata = metadata.metadata("solvency2")
    assert package_metadata["License"] == "GPL-3.0-or-later"
    assert "RiskDataScience GmbH" in package_metadata["Author-email"]
    assert "riskdatascience@web.de" in package_metadata["Author-email"]
    assert any(str(p).endswith("EIOPA_DPM_TAXONOMY_LICENSE_1_4.txt")
               for p in metadata.files("solvency2"))
    rights = json.loads(files("solvency2").joinpath("resources/third_party_data_register.json").read_bytes())
    assert rights["market_data"]["kind"] == "SYNTHETIC_DEMO"
    assert rights["market_data"]["observed_market_data_included"] is False
    assert not [r for r in metadata.requires("solvency2") or [] if "extra ==" not in r]
    assert len(s2.__all__) == 421
    catalogue = api_catalogue()
    assert catalogue["calculations"] == 399 and len(catalogue["functions"]) == 432
    for row in catalogue["functions"]:
        obj = getattr(importlib.import_module(row["module"]), row["name"])
        if row["name"] in s2.__all__:
            assert obj is getattr(s2, row["name"])
    for anchor in ("solvency2", "solvency2._core"):
        resource = files(anchor).joinpath("resources")
        hashes = json.loads(resource.joinpath("manifest.json").read_bytes())["sha256"]
        for name, expected in hashes.items():
            assert hashlib.sha256(resource.joinpath(name).read_bytes()).hexdigest() == expected, name
    assert "discount_curve_from_spot_rates" in documentation("API")
    assert "Discount factors" in documentation("DATA")
    assert "public-data edition" in documentation("ACCEPTANCE")
    assert len(s2.reference_cases()["cases"]) == 12382
    assert len(s2.reference_portfolios()["portfolios"]) == 227
    import warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        demo = s2.rfr_archived_spot_rate("EUR", 1, "no_va", qualification_reference="SYNTHETIC",
            context=s2.Context("2025-01-31", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1"))
        assert demo.value == .05 and demo.status == "SYNTHETIC_DEMO"
        assert caught and "SYNTHETIC_DEMO" in str(caught[0].message)
    for name in reference_datasets():
        assert reference_dataset(name)
    for name in ("local_inputs.py", "parameters.py"):
        runpy.run_path(str(examples / name), run_name="__main__")
    base = s2.Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
    assert s2.basic_scr({"market": 0, "default": 0, "life": 3, "health": 0, "nonlife": 4},
                        intangible_charge=80, context=base).value == 85
    assert s2.mcr_combined(4.2, 100, 0, context=base).value == 25
    outcome = s2.reporting_bound_rule_check(
        "BV1053-1", {"v1": {"value": 1005, "decimals": 0},
                     "v2": {"values": [{"value": n, "decimals": 0} for n in (100, 200, 300, 400)]}},
        technical_version="2.10.0", binding_reference="SYNTHETIC")
    assert outcome["value"] is True and outcome["full_report_validated"] is False
    # Base installations must not acquire numerical backends implicitly.
    assert importlib.util.find_spec("scipy") is None
    try:
        s2.usp_lognormal_fit(losses=[60, 120, 100, 190, 250], volumes=[80, 100, 140, 200, 300],
                             method="premium", qualification_reference="SYNTHETIC", context=base)
    except s2.CalculationError as error:
        assert error.code == "REVIEW_REQUIRED" and error.field == "optimizer"
    else:
        raise AssertionError("Missing optional dependency was not reported")
    print(json.dumps({"installed_smoke": "PASS", "version": s2.__version__, "exports": len(s2.__all__),
                      "network": "connections denied", "runtime_dependencies": "none",
                      "installation": str(installed), "resource_writes": "denied"}))


if __name__ == "__main__":
    main()
