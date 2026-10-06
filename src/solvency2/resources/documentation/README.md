# Solvency 2

A granular, offline Solvency II calculation toolkit by **RiskDataScience GmbH**.
First version: **0.5.0** (0.5 release).
Repository: [rds0001/solvency2-python](https://github.com/rds0001/solvency2-python).
Use individual formulas in scripts and notebooks, supply your own data, inspect
parameters and correlations, and retain the source and scenario trail of each
calculation. A complete insurer model or workflow is not required.

The package contains the accepted calculation baseline: **399 calculations,
421 inherited public symbols, 12,382 fixed core reference cases and 227
integration portfolios**, plus additional reporting references. It preserves
the baseline's explicit limitations. This is **not** regulatory certification,
an internal model, an automatic filing service, or a claim of complete coverage
of every legal requirement. See [scope and limitations](docs/LIMITATIONS.md).

**Market-data edition: synthetic examples only.** No historical provider market
archive is bundled. Demo lookups issue a warning and return `SYNTHETIC_DEMO`;
their downstream workflow results retain that label. Supply your own local data
for production calculations. Regulatory parameters and correlations are retained.

## Install locally

Python 3.10 or later is required; Python 3.10 is the tested release environment.
This is a local candidate, not a claim of availability on PyPI. Install the
wheel supplied in `dist/` (substitute its actual filename):

```sh
python -m pip install --no-index --no-deps dist/solvency2_python-0.5.0-py3-none-any.whl
```

The base runtime has **no third-party dependencies**. Only designated numerical
methods need SciPy (`optimization` / `statistics` extras); install it separately
from a trusted local wheel collection. Installation is distinct from execution:
the library does not download data, contact providers, check for updates or send
telemetry. It needs neither an external engine installation nor R.

## One calculation

```python
from solvency2 import Context
from solvency2.capital import intangible_risk

context = Context(
    as_of="2025-01-17", known_at="2026-09-23", currency="EUR",
    profile_id="EU-S2-DOCUMENTS-2024-2025-v0.1",
)
result = intangible_risk(100, context=context)
assert result.value == 80
print(result.unit, result.sources, result.status)
audit_record = result.to_dict()
```

The `80` is a capital charge in EUR, not a valuation of the original asset.
Dates and the rule profile are explicit. `known_at` expresses your chosen
information cutoff, not the current clock time. `REFERENCE_COMPONENT` means a
qualified software component result, **not** supervisory approval.

## Your own curve, including dates outside the bundled archive

```python
from solvency2 import Context
from solvency2.data import DiscountCurve, best_estimate_with_curve

context = Context("2028-12-31", "2028-12-31", "EUR", "EU-S2-DOCUMENTS-2027-v0.1")
curve = DiscountCurve(
    curve_id="synthetic-example", as_of=context.as_of, currency="EUR",
    curve_kind="base", source_reference="SYNTHETIC: not market data",
    points=(("2029-12-31", 0.95),),
)
result = best_estimate_with_curve(
    {"2029-12-31": {"expected_inflows": 0, "expected_outflows": 100}},
    curve=curve, runoff_complete=True, cashflow_reference="SYNTHETIC: complete toy runoff",
    context=context,
)
assert result.value == 95
assert result.details["user_curve"]["input_hash"] == curve.input_hash
```

Load the same factors with `load_discount_curve_json(path)` or
`load_discount_curve_csv(path, ...)`. Explicit annual-effective spot rates and
year fractions are also supported. There is no automatic interpolation or
fallback to an archived curve. Read [input formats](docs/DATA.md).

## Change a parameter without editing installed files

```python
from dataclasses import replace
from solvency2 import Context, NumericOverride, intangible_risk, parameter

base = Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
original = parameter("scalars/intangible", context=base)
scenario = replace(base, overrides=(NumericOverride(
    "profile.json", ("scalars", "intangible", "value"), 0.70, "Synthetic sensitivity",
),))
changed = intangible_risk(100, context=scenario)
assert changed.value == 70 and changed.status == "ANALYST_SCENARIO"
assert intangible_risk(100, context=base).value == 80
```

Matrix entries, supported table cells and JSON scenario batches follow the
same principle. Read [parameter overrides](docs/PARAMETERS.md) for paths,
automatic matrix symmetry, validation and audit details.

## Find the right function

| Analyst task | Public modules |
|---|---|
| Valuation, cashflows, best estimate, risk margin | `valuation`, `provisions`, `rates`, `reinsurance` |
| SCR shocks and aggregation | `market`, `counterparty`, `life`, `health`, `nonlife`, `capital` |
| Capital resources and MCR | `own_funds`, `mcr` |
| Group calculations, model inputs and governance evidence | `groups`, `models`, `governance` |
| Reporting components and reconciliation | `reporting`, `audit` |
| Context, numeric parameters and synthetic data | `context`, `parameters`, `reference`, `catalogue` |
| Local curves and scenario batches | `data`, `scenarios` |
| Optional composition of existing formulas | `workflow` |

All inherited functions are also available directly from `solvency2`.
The [function reference](docs/API.md) contains signatures, method descriptions
and fixed reference examples. `solvency2.catalogue.api_catalogue()` supplies the
same navigation as structured data. [Recipes](docs/RECIPES.md) show how to combine
components; executable scripts and local files are in [examples](examples/).
Installed-wheel users can read the guides entirely offline with
`from solvency2.catalogue import documentation; print(documentation("DATA"))`.
Use `documentation("API")` for the full function reference.

## Reference data and reproducibility

```python
import solvency2 as s2
from solvency2.catalogue import reference_datasets, reference_dataset

cases = s2.reference_cases()["cases"]
portfolios = s2.reference_portfolios()["portfolios"]
extra = reference_dataset(reference_datasets()[0])
# Explicitly write a new directory you own; existing directories are rejected:
# s2.export_resources("my-reference-export")
```

Reference expected values are independently specified arithmetic fixtures, not
outputs generated to match the implementation. The demonstration market grids
are invented from simple constants, not transformations of observed data.
Regulatory parameter tables are **not synthetic**. Select profiles and reporting
versions deliberately. Users qualify their own inputs for the selected purpose.

## Documentation and local development

- [Context, results, errors and limitations](docs/LIMITATIONS.md)
- [Local inputs and units](docs/DATA.md)
- [Scenarios and parameter changes](docs/PARAMETERS.md)
- [Practical recipes and reference replay](docs/RECIPES.md)
- [Full function reference](docs/API.md)
- [Build and acceptance instructions](docs/DEVELOPMENT.md)
- [Completed local acceptance](docs/ACCEPTANCE.md)
- [Third-party data notices](THIRD_PARTY_NOTICES.md)

License: **GPL-3.0-or-later**, see [LICENSE](LICENSE) and [NOTICE](NOTICE).
Author/contact: RiskDataScience GmbH, **riskdatascience@web.de**.
See [third-party attributions and data licenses](THIRD_PARTY_NOTICES.md) for the
EU regulatory material and EIOPA reporting extracts. Market examples and original
library code are by RiskDataScience GmbH. Warranty terms are in LICENSE.
