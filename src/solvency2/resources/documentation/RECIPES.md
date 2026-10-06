# Small, composable workflows

Use direct domain functions when one result is sufficient. The optional graph
runner is useful when you want an explicit dependency record, not a prerequisite.
All examples are synthetic, not complete insurer valuations.

## Cashflows and technical provisions

Start with `examples/local_inputs.py`: identical CSV/JSON factors produce the
same best estimate as an in-memory curve. Risk margin requires a separately
qualified projected SCR runoff and basic-rate inputs; a BE cashflow is not an SCR
projection. Find `risk_margin` and `technical_provisions_sum` in the API reference.
Each function's example is a fixed input/expected-result pair, including the
runoff-completeness declaration. Do not imply completeness for a truncated series.

## Aggregate known charges

```python
from solvency2 import Context, aggregate_risk, basic_scr

context = Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
health = aggregate_risk({"premium_reserve": 3, "lapse": 4}, "health_nslt", context=context)
assert health.value == 5
assert abs(sum(health.details["euler_contributions"].values()) - 5) < 1e-12
# All other components are EXPLICITLY zero in this toy portfolio.
bscr = basic_scr({"market": 0, "default": 0, "life": 3, "health": 0, "nonlife": 4},
                 intangible_charge=80, context=context)
assert bscr.value == 85
```

Use labels, not an assumed row order. A charge already containing diversification
cannot automatically be used as a raw exposure. Selecting shocks and revaluing
assets/liabilities are separate operations; follow each method's contract.

## Own funds and MCR

`own_funds_scr_allocation` and `own_funds_mcr_allocation` apply existing eligibility
limits to explicitly qualified tier amounts. They do not infer classification
from a security name. `mcr_nonlife`/`mcr_life` feed `mcr_linear`, then
`mcr_combined`. For example:

```python
from solvency2 import mcr_combined
assert mcr_combined(linear=4.2, scr=100, absolute_floor=0, context=context).value == 25
```

The zero absolute floor is an explicit synthetic test assumption, **not** a
regulatory floor recommendation. The complete fixed portfolio examples include
the upstream segment/tier inputs, including signed intermediate components.

## Replay any independent calculation example

Every one of the 399 calculation functions has bundled cases. Select by function
and inspect the complete input before calling it:

```python
from dataclasses import replace
import math
import solvency2 as s2

base = s2.Context("2025-01-17", "2026-09-23", "EUR", "EU-S2-DOCUMENTS-2024-2025-v0.1")
case = next(c for c in s2.reference_cases()["cases"]
            if c["function"] == "group_consolidated_best_estimate" and "expected" in c)
result = getattr(s2, case["function"])(**case["kwargs"], context=replace(base, **case.get("context", {})))
assert math.isclose(result.value, case["expected"], rel_tol=1e-12,
                    abs_tol=case.get("absolute_tolerance", 1e-12))
```

Cases contain IDs, original derivations and expected outputs or error codes.
They are not recalibrated from this library's outputs. The API catalogue lists
case IDs for each function. Some complicated inputs are intentionally supplied
by a case ID rather than repeated as pages of nested data.

## Compose a whole reference portfolio

```python
portfolio = s2.reference_portfolios()["portfolios"][0]
run = s2.Engine().run(portfolio["nodes"], context=s2.Context(**portfolio["context"]))
for name, expected in portfolio["expected_values"].items():
    assert math.isclose(run["results"][name]["value"], expected, rel_tol=1e-12,
                        abs_tol=portfolio.get("absolute_tolerances", {}).get(name, 1e-12))
assert run["regulatory_total_released"] is False
```

The 227 portfolios exercise existing dependency chains. They are integration
references, not evidence that a real insurer's inputs are complete.

## Inspect reporting data and a bounded expression

```python
from solvency2.reporting import reporting_catalog, reporting_bound_rule_check
catalog = reporting_catalog(technical_version="2.10.0")
result = reporting_bound_rule_check(
    "BV1053-1",
    {"v1": {"value": 1005, "decimals": 0},
     "v2": {"values": [{"value": n, "decimals": 0} for n in (100, 200, 300, 400)]}},
    technical_version="2.10.0", binding_reference="SYNTHETIC: resolved entity, period and unit",
)
assert result["value"] is True
assert result["full_report_validated"] is False
```

The supplied bindings are already resolved by the user. A true expression is
neither a complete filing check nor evidence of current legal applicability.
`catalogue.reference_datasets()` lists additional reporting cases and portfolios;
`reference_dataset(name)` returns a fresh decoded local copy. Export one explicitly
with standard `json.dump` if required. The original `export_resources` exports
the calculation bundle; reporting catalogues are accessed separately through
their versioned APIs. No function fetches a taxonomy or current validation list.
