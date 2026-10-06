# Solvency 2

A granular, offline Solvency II calculation toolkit by **RiskDataScience GmbH**.
First version: **0.5.0** (0.5 release).
Repository: [rds0001/solvency2-python](https://github.com/rds0001/solvency2-python).
Use individual formulas in scripts and notebooks, supply your own data, inspect
parameters and correlations, and retain the source and scenario trail of each
calculation. A complete insurer model or workflow is not required.

## What this makes easier

Solvency II work involves more than producing a single capital number. Analysts
need reusable calculations, regulatory tables, controlled assumptions and a way
to explain how each result was obtained. This library brings those building
blocks together in one Python toolkit:

- **Calculate just what you need.** Call a single shock, valuation, aggregation,
  own-funds or MCR function without setting up an application or insurer model.
- **Use regulatory tables without transcribing them yourself.** Inspect included
  parameters, labelled correlation matrices and supported catastrophe tables,
  with their source references and explicit rule profiles.
- **Work with your own data and assumptions.** Load local curves and supply
  cashflows, exposures or credit inputs. Change supported parameters and matrix
  entries per scenario, without modifying installed files or global defaults.
- **Explain and reproduce a result.** Calculations return the value, units,
  formula identifier, sources, context, input hashes and applicable override
  records—not just an unexplained number.
- **Start from runnable examples.** Explore 12,382 fixed reference cases and 227
  integration portfolios, then adapt the documented inputs to your own work.
- **Connect related tasks.** Use components for technical provisions, market and
  underwriting risks, counterparty risk, capital resources, groups and reporting
  in the same toolkit. Compose selected functions into a dependency workflow
  when useful; direct function calls remain the primary interface.

The scope is **399 calculation functions across 21 domain modules**, plus local
input, scenario and discovery helpers. Explicit baseline and 2027 rule profiles
support version-aware work within their documented method coverage. Reporting
resources and checks complement the calculation APIs; they are not an automatic
filing service. All user documentation is also available from an installed wheel.

For actuarial analysts, risk teams, researchers and developers, the practical
benefit is less repeated formula/table plumbing and a shared, inspectable basis
for notebooks, sensitivity analyses, validation and internal tools. The runtime
is fully offline: no provider account, hosted engine or telemetry is required.
Source code is GPL-3.0-or-later; data attributions are documented separately.

## Included scope

The package contains the accepted calculation baseline: **399 calculations,
421 inherited public symbols, 12,382 fixed core reference cases and 227
integration portfolios**, plus additional reporting references. It preserves
the baseline's explicit limitations. This is **not** regulatory certification,
an internal model, an automatic filing service, or a claim of complete coverage
of every legal requirement. See [scope and limitations](https://github.com/rds0001/solvency2-python/blob/main/docs/LIMITATIONS.md).

**Market-data edition: synthetic examples only.** No historical provider market
archive is bundled. Demo lookups issue a warning and return `SYNTHETIC_DEMO`;
their downstream workflow results retain that label. Supply your own local data
for production calculations. Regulatory parameters and correlations are retained.

## Installation

Python 3.10 or later is required; Python 3.10 is the tested release environment.
PyPI package name: **solvency2**. For a published release:

```sh
python -m pip install solvency2
```

The import is also `solvency2`; the GitHub repository remains `solvency2-python`.
Alternatively install from a checkout (pip obtains build tooling if needed):

```sh
git clone https://github.com/rds0001/solvency2-python.git
cd solvency2-python
python -m pip install .
```

For an offline installation, first build or obtain the wheel as described in
[local build instructions](https://github.com/rds0001/solvency2-python/blob/main/docs/DEVELOPMENT.md), then install it without an index:

```sh
python -m pip install --no-index --no-deps dist/solvency2-0.5.0-py3-none-any.whl
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
fallback to an archived curve. Read [input formats](https://github.com/rds0001/solvency2-python/blob/main/docs/DATA.md).

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
same principle. Read [parameter overrides](https://github.com/rds0001/solvency2-python/blob/main/docs/PARAMETERS.md) for paths,
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
The [function reference](https://github.com/rds0001/solvency2-python/blob/main/docs/API.md) contains signatures, method descriptions
and fixed reference examples. `solvency2.catalogue.api_catalogue()` supplies the
same navigation as structured data. [Recipes](https://github.com/rds0001/solvency2-python/blob/main/docs/RECIPES.md) show how to combine
components; executable scripts and local files are in [examples](https://github.com/rds0001/solvency2-python/tree/main/examples/).
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

- [Context, results, errors and limitations](https://github.com/rds0001/solvency2-python/blob/main/docs/LIMITATIONS.md)
- [Local inputs and units](https://github.com/rds0001/solvency2-python/blob/main/docs/DATA.md)
- [Scenarios and parameter changes](https://github.com/rds0001/solvency2-python/blob/main/docs/PARAMETERS.md)
- [Practical recipes and reference replay](https://github.com/rds0001/solvency2-python/blob/main/docs/RECIPES.md)
- [Full function reference](https://github.com/rds0001/solvency2-python/blob/main/docs/API.md)
- [Build and acceptance instructions](https://github.com/rds0001/solvency2-python/blob/main/docs/DEVELOPMENT.md)
- [Completed local acceptance](https://github.com/rds0001/solvency2-python/blob/main/docs/ACCEPTANCE.md)
- [Third-party data notices](https://github.com/rds0001/solvency2-python/blob/main/THIRD_PARTY_NOTICES.md)

License: **GPL-3.0-or-later**, see [LICENSE](https://github.com/rds0001/solvency2-python/blob/main/LICENSE) and [NOTICE](https://github.com/rds0001/solvency2-python/blob/main/NOTICE).
Author/contact: RiskDataScience GmbH, **riskdatascience@web.de**.
See [third-party attributions and data licenses](https://github.com/rds0001/solvency2-python/blob/main/THIRD_PARTY_NOTICES.md) for the
EU regulatory material and EIOPA reporting extracts. Market examples and original
library code are by RiskDataScience GmbH. Warranty terms are in LICENSE.
