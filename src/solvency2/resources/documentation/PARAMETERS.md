# Parameters and transparent analyst scenarios

Do not edit `site-packages` or replace resource manifests. Use the public
`parameter` lookup and immutable, per-context `NumericOverride` entries.
No global defaults are changed. User cashflows/curves are normal inputs,
not regulatory parameter overrides.

## Inspect, change, restore

```python
from dataclasses import replace
from solvency2 import Context, NumericOverride, parameter, intangible_risk, aggregate_risk

base = Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
original = parameter("scalars/intangible", context=base)
assert original["value"] == 0.8
scenario = replace(base, overrides=(NumericOverride(
    "profile.json", ("scalars", "intangible", "value"), 0.7, "Synthetic sensitivity",
),))
result = intangible_risk(100, context=scenario)
assert result.value == 70
assert result.status == "ANALYST_SCENARIO"
assert result.details["analyst_overrides"][0]["original"] == 0.8
assert intangible_risk(100, context=base).value == 80
assert parameter("scalars/intangible", context=base) == original
```

The effective lookup carries its source, profile hash and override audit.
The result contains original/effective values and the reason, with the additional
`ANALYST_OVERRIDE` source. Return to the original simply by using `base` or
`replace(scenario, overrides=())`.

## Correlation matrices

```python
matrix = parameter("matrices/health_nslt", context=base)
assert matrix["labels"] == ["premium_reserve", "lapse"]
assert aggregate_risk({"premium_reserve": 3, "lapse": 4}, "health_nslt", context=base).value == 5
correlated = replace(base, overrides=(NumericOverride(
    "profile.json", ("matrices", "health_nslt", "values", 0, 1), 0.5,
    "Synthetic positive-correlation sensitivity",
),))
effective = parameter("matrices/health_nslt", context=correlated)
assert effective["values"][0][1] == effective["values"][1][0] == 0.5
value = aggregate_risk({"premium_reserve": 3, "lapse": 4}, "health_nslt", context=correlated).value
assert abs(value - 37 ** 0.5) < 1e-12
```

**Supply only one cell of a symmetric pair**: the original implementation mirrors
it automatically and rejects duplicate pair overrides. Diagonal entries must
remain 1 and correlations stay in [-1, 1]. Existing calculation checks remain
active; an arbitrary changed matrix is not thereby regulator-approved. Matrix
labels and dimensions cannot be replaced through numeric overrides.

## Load a batch from a local JSON file

```json
{
  "schema_version": 1,
  "overrides": [{
    "resource": "profile.json",
    "path": ["scalars", "intangible", "value"],
    "value": 0.7,
    "reason": "Synthetic sensitivity"
  }]
}
```

```python
from solvency2.scenarios import load_numeric_overrides_json, numeric_overrides_from_dict
scenario = replace(base, overrides=load_numeric_overrides_json("my-scenario.json"))
scenario.validate()  # resolves allowed paths against this rule profile
```

Use `numeric_overrides_from_dict(payload)` for in-memory batches. Parsing checks
the schema, finite numbers and field types. Applying/validating the context checks
that the path names an existing supported numeric cell. Duplicate paths, unknown
cells or unsupported metadata changes fail. An empty list restores defaults.

## Supported paths and limits

| Logical resource | Numeric path shape |
|---|---|
| `profile.json` | `['scalars', name, 'value']` |
| `profile.json` | `['matrices', name, 'values', row_index, column_index]` |
| `profile.json` | `['tables', name, 'rows', row_key_or_index, column_key_or_index]` |
| `catastrophe_matrices.json` | `['matrices', matrix_id, 'values', row, column]` |
| `catastrophe_regions.json` | `['perils', peril, 'factors', region]` or `['perils', peril, 'matrix', 'values', row, column]` |
| `catastrophe_weights.json` | `['tables', peril, 'weights', zone, column]` or `['special_factors', name, 'value']` |

Actual keys and index types must match the exported data. `export_resources`
provides an inspectable copy of the profile and tables; changing that copy alone
does not change the installed library. Selected numeric demo market cells also
support overrides and remain labelled SYNTHETIC_DEMO; use explicit external
curves or the market_data keyword for your own market inputs (see DATA.md).
Source metadata, geography assignments, formula definitions and unqualified
source conflicts are not generally overridable.

Logical `profile.json` and supported catastrophe resource aliases are resolved
by the selected rule profile (including the 2027 profile). Do not invent a new
profile or use the physical `profile_2027.json` name as an override workaround.
Changing a numeric assumption cannot unblock an unresolved source restriction,
approve an internal model, or establish a new legal regime. Those require a
deliberate supported extension, not a parameter file.
