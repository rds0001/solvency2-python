# Scope, context and interpretation

## What is finalized

The local Python product packages the accepted calculation baseline, not a new
claim that every Solvency II obligation has been implemented or legally approved.
All inherited public capabilities remain reachable; known source conflicts,
external qualifications and unsupported branches remain visible. Future-dated
components present in the accepted 2027 profile are included, not invented for
later unreviewed legal changes.

The package contains individual formulas, quantitative/evidence checks,
parameters, correlations, dated reporting data and synthetic references. It does
not generate an insurer's actuarial projections, internal model, supervisory
decisions or corporate governance. Internal models must be developed and
qualified externally; the available interfaces consume explicitly declared
external results. No external model is supplied or approved by this package.

## Choose a rule profile explicitly

Call `rule_profiles()` to inspect the bundled descriptors and exclusions.

| Profile | Reference valuation dates | Earliest knowledge date |
|---|---|---|
| `EU-S2-DOCUMENTS-2024-2025-v0.1` | 2025-01-17 through 2027-01-29 | 2025-01-17 |
| `EU-S2-DOCUMENTS-2027-v0.1` | From 2027-01-30 | 2026-09-23 |

The absence of an end date is **not** a promise that future legal changes are
covered. Date ranges describe the packaged reference snapshots. A known-at date
after publication does not fetch later amendments. Only `mode='REFERENCE_ONLY'`
is supported; requesting a regulatory sign-off mode fails with `REVIEW_REQUIRED`.
Function-specific profile exclusions also apply. Currency uses an explicit
uppercase three-letter code; there is no automatic currency conversion.

## Results and errors

Calculation functions return `Result`:

| Field | Meaning |
|---|---|
| `value`, `unit` | Numeric output and currency or method-specific unit |
| `formula_id`, `sources` | Stable function and regulatory/method source identifiers |
| `context` | Requested date, knowledge cutoff, currency, rule profile and scenario |
| `input_hash`, `profile_hash` | SHA-256 fingerprints of canonical inputs and effective profile |
| `details` | Method-specific intermediate results, assumptions, selections and override audit |
| `status` | `REFERENCE_COMPONENT`, or `ANALYST_SCENARIO` with numeric overrides |

`to_dict()` produces an independent serializable record. This can contain your
inputs or sensitive derived details: **you** choose whether and where to persist
it. A hash is a reproducibility aid, not a digital signature or a legal approval.
No logging/export of user results occurs automatically.

Most calculation failures are `CalculationError` with `.code` and `.field`:
`MISSING_INPUT`, `INVALID_INPUT`, `UNSUPPORTED_RULESET`, `UNSUPPORTED_METHOD`,
`UNSUPPORTED_PARAMETER`, `REVIEW_REQUIRED`, `RESOURCE_INTEGRITY` and
`NUMERICAL_ERROR`, among others. Missing values are not zero. Pass genuinely zero
exposures explicitly. Python calling errors on non-calculation utilities may also
be ordinary `TypeError`/`ValueError`; do not catch all errors and replace them with
a numeric result.

Parameter/metadata lookups and reporting utilities return documented dictionaries,
not `Result`. Constructors and export helpers have their own return types.

## Composition is not full regulatory sign-off

`Engine` / `calculate` optionally compose existing formulas using explicit graph
nodes and `$ref` dependencies. This does not require, or constitute, a full
insurer model. Their retained `status='PARTIAL'` and
`regulatory_total_released=False` are intentional. `coverage()` retains the
baseline's `INCOMPLETE` regulatory coverage assessment even though the packaging
of that accepted scope is complete. Do not rename these statuses to PASS.

## Reporting boundary

Reporting versions `2.8.2`, `2.8.2-hotfix`, `2.10.0` are explicit **technical**
snapshots, separate from the calculation rule profile. The library supplies
catalogues, fact checks, supported expression/binding evaluation and bounded XML
generation. Unsupported selectors, joins and scope are not silently evaluated.
Some archived validation statuses remain ambiguous. No remote taxonomy resolution
occurs. An external XBRL validator or an entire supervisory taxonomy execution
environment is not bundled.

`full_report_validated`, `legal_applicability_verified`, `submission_ready` and
similar flags retain their original conservative meanings. XML well-formedness,
successful selected rules and current submission acceptance are different things.
This is not a complete reporting/submission service.

## Numerical and data boundary

Inputs must satisfy each method's units, signs, selection criteria and external
qualification declarations. Methods requiring SciPy fail explicitly if it is
absent; installing the base package does not silently substitute an approximation.
The base package is dependency-free, but not every optional numerical method is.
Matrices and geographic assignments with unresolved source issues retain their
guards. Numeric overrides do not remove those guards.

Users supply production market data. Bundled market examples are invented and
marked SYNTHETIC_DEMO, including their dependent workflow outputs; they are not
production inputs. No automatic "latest" selection, update search or market-data
fallback exists. User-supplied file/cell metadata identifies the user's source,
not official approval. See DATA.md for local import and THIRD_PARTY_NOTICES.md
for the licenses and attribution of the regulatory extracts actually included.
