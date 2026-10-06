# Explicit local inputs

The primary interface accepts Python numbers, mappings and sequences. You may
read a database, spreadsheet or DataFrame in your own application and pass those
objects. No pandas or Excel dependency is imposed. Currency amounts are in the
declared currency (not implicitly thousands); ratios and annual-effective rates
are decimal numbers, e.g. `0.03`, not `3` for 3%. Some original archived tables
explicitly use percent units: preserve the unit specified by their API.

## Market tables: demo data and explicit local production inputs

`solvency2.rfr_monthly_data()` returns a fresh, entirely invented example archive
and its arithmetic recipe. It contains one illustrative date, `2025-01-31`, with
flat EUR/USD curves and toy credit grids. No historical market archive is bundled.
All five `rfr_archived_*` functions retain their names for API continuity and
accept an optional `market_data=` dictionary. Without it they use the demo only:
they emit a `UserWarning`, set `result.status` to `SYNTHETIC_DEMO` and include
that source marker and the actual dataset hash. Demo status survives numeric
overrides and propagates to dependent nodes in `Engine.run`.

For production use, read your own JSON file and pass its content explicitly:
The selected rule profile must support the called method; supplying a new date
does not extend that profile's regulatory applicability.

```python
import json
from pathlib import Path
import solvency2 as s2

context = s2.Context("2025-01-31", "2025-02-03", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
market_data = json.loads(Path("/your/private/market-data.json").read_text(encoding="utf-8"))
result = s2.rfr_archived_spot_rate(
    "EUR", 1, "no_va", qualification_reference="your-validated-input-record",
    context=context, market_data=market_data,
)
```

Do not relabel demo values as production data. Construct your own archive with
`schema_version: 1`, `status: "USER_SUPPLIED"` and a `datasets` mapping keyed by
exact ISO as-of dates. Each dataset has `data_kind: "USER_SUPPLIED"`, your
`source_id`, actual `retrieved_at` and `archive_sha256` (hash of your source file).
Members use your file names and SHA-256 hashes; sheet/cell fields identify your
own import coordinates, which may be JSON coordinates rather than spreadsheets.
No field confers EIOPA origin or approval. The chosen dataset must have been
available by `context.known_at`. The full supplied mapping participates in the
input hash; `market_dataset_hash` fingerprints the selected dataset itself.

The returned `rfr_monthly_data()` structure is the inspectable schema template.
Only the table family used by a call must be present:

| Family | Required numerical content and units |
|---|---|
| Spot | `maturities`, `rate_row_offset`, `unit`, `blocked_series`, and `series[id]` with currency metadata, column, label and `variants[no_va/with_va]`; each variant has sheet, rates in decimals, and `raw_metadata.VA` |
| Government | `government_spreads.tables[ltas/fundamental_spread]` with sheet, maturities, columns and `rows[country].values_percent` / `source_row`; divide percentages by 100 |
| Corporate | `corporate_credit` with `blocked_series` and `series[currency].sectors[financial/non_financial].tables[metric]`; grids have 30 tenor rows, 7 CQS columns (0..6), columns, row_offset and unit; PD is a probability, PD/FS/downgrade spreads are percentages |
| Supplemental LTAS | `supplemental_ltas.tables[corporate_ltas/basic_rfr_ltas]` with 30 columns and per-series rows of `values_percent`; `specific_ltas` rows instead have `value_percent` and `cell`, without a tenor axis |

Each family carries `member` and `member_sha256`; spot fields are directly in
the dataset. Selected values are validated and existing currency, tenor,
qualification and blocked-series guards remain active. There is no interpolation,
currency conversion, date rolling or fallback if supplied data lack an item.
Incomplete table shapes fail explicitly. The baseline-resource hash always
identifies the bundled demo file, not the user source; use the dataset/input
hashes for supplied data. Historical result keys such as `published_value` name
the selected source cell, not an assertion that EIOPA published it.

For a sensitivity, edit a private copy of your mapping and keep its source trail.
Do not combine supplied tables with `rfr_monthly.json` numeric overrides, which
address the bundled demo only. Other regulatory parameter overrides still work.
For ordinary discounting, the smaller `DiscountCurve` JSON/CSV formats below are
usually sufficient. Direct scalar formula calls cannot track where a bare number
came from: retain the originating Result alongside your calculations, or use
the workflow for automatic demo-label propagation.

## Discount factors: JSON

`load_discount_curve_json(path)` reads exactly this UTF-8 schema:

```json
{
  "schema_version": 1,
  "curve_id": "synthetic-example",
  "as_of": "2028-12-31",
  "currency": "EUR",
  "curve_kind": "base",
  "source_reference": "SYNTHETIC: not market data",
  "value_type": "discount_factor",
  "unit": "dimensionless",
  "points": [{"date": "2029-12-31", "discount_factor": 0.95}]
}
```

Use `DiscountCurve.from_dict(payload)` for identical in-memory validation.
`curve.to_dict()` returns a fresh JSON-serializable copy. Curve instances keep
defensively copied, sorted, immutable points. `curve.factor(date)` performs an
exact lookup. Duplicate dates/JSON keys, unknown fields, NaN/Inf, zero/negative
factors, dates before `as_of`, or a valuation-date factor other than 1 fail.
Factors greater than 1 are valid (including negative-rate cases).

Curve kinds: `base`, `va`, `ma`, `stress`, `custom`. This is explicit user metadata,
not legal qualification. No VA or MA is added by the adapter. Currency must match
the calculation context; dates use canonical `YYYY-MM-DD` strings.

## Discount factors: CSV

`load_discount_curve_csv(path, *, curve_id, as_of, currency, curve_kind,
source_reference)` reads two columns (either order), UTF-8, comma separator,
decimal point. Metadata is mandatory and is not inferred from a filename.

```csv
date,discount_factor
2029-12-31,0.95
```

```python
from solvency2.data import load_discount_curve_csv
curve = load_discount_curve_csv(
    "my-curve.csv", curve_id="my-curve", as_of="2028-12-31", currency="EUR",
    curve_kind="base", source_reference="My independently qualified source",
)
```

JSON and CSV loaders accept `str` or `pathlib.Path` local paths, not URLs.
They do not follow remote document references or resolve XML entities. As with
ordinary file reads, the caller controls permissions, symlinks and network-mounted
filesystems; offline execution assumes the selected files are locally available.

## Explicit spot rates

`discount_curve_from_spot_rates(points, *, curve_id, curve_kind,
source_reference, time_basis_reference, context)` converts through the existing
`rfr_spot_discount_factor` formula: `DF = (1 + rate) ** (-time_years)`.
The only accepted convention is **annual-effective decimal zero-coupon rates**.
Convert other conventions explicitly outside this helper.

```python
from solvency2 import Context
from solvency2.data import discount_curve_from_spot_rates

context = Context("2028-12-31", "2028-12-31", "EUR", "EU-S2-DOCUMENTS-2027-v0.1")
curve = discount_curve_from_spot_rates(
    {"2029-12-31": {"annual_effective_rate": -0.01, "time_years": 1.0}},
    curve_id="synthetic-negative-rate", curve_kind="base",
    source_reference="SYNTHETIC", time_basis_reference="Explicit annual anniversary: 1 year",
    context=context,
)
assert curve.factor("2029-12-31") > 1
```

Year fractions are caller-supplied, nonnegative and strictly increasing with
dates; zero is allowed exactly at the valuation date. Rates must exceed -1.
No day-count basis is guessed. The original rates, year fractions and convention
are fingerprinted into the curve provenance. A JSON file containing these point
mappings can be read by your own `json.load` and passed unchanged.

## Best estimate and provenance

`best_estimate_with_curve(cashflows, *, curve, runoff_complete,
cashflow_reference, context)` accepts each payment date mapped to
`expected_inflows` and `expected_outflows`. Both amounts are nonnegative; the
result is the **signed** sum of `(outflows - inflows) * discount_factor`.
`runoff_complete=True` declares your projection complete; it is not a projection
produced or independently verified by the library. No missing payment date gets
zero or an interpolated factor. Cashflows/curve/context dates and currencies must
be compatible. See the runnable `examples/local_inputs.py`.

The curve hash covers all supplied factors and metadata, not the local path or
row order. It is included in the calculation's input fingerprint.
`result.details['user_curve']` contains metadata, the hash and
`qualification_status='EXTERNAL_UNVERIFIED'`. The full source file/path is not
logged. Changing any curve value or source reference changes its hash. Unused
curve points are deliberately part of the input snapshot.

Expected controlled failures include `MISSING_INPUT`, `INVALID_INPUT`,
`UNSUPPORTED_INPUT`, `INPUT_IO_ERROR`, and the original context/profile errors.
Catch `solvency2.CalculationError` and inspect `.code` and `.field`.
