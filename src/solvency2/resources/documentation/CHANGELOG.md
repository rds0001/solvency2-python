# Changelog

## 0.5.0 — first version

- Release 0.5 and project title Solvency 2; repository `rds0001/solvency2-python`.
- GitHub Actions tests, build and isolated offline installation smoke.
- PyPI distribution name `solvency2`; publication through the manually triggered
  GitHub workflow `publish.yml`, using PyPI Trusted Publishing without API tokens.
- Public-data edition: invented market demos, explicit local user-data inputs,
  runtime demo warnings and propagated demo labels. No historical market archive.
- Retained regulatory parameters and licensed reporting extracts with attribution,
  dated modification notices, derivative inventory and the full taxonomy license.

### Features inherited from the technically accepted 0.1.0.dev0 candidate

- Emitted the accepted core without formula changes: 399 calculations and all
  421 inherited public symbols, with domain-level imports.
- Bundled original parameters, matrices, 12,382 independent core reference
  cases, 227 integration portfolios and ten extra reporting reference datasets.
- Added explicit local CSV/JSON discount curves, annual-effective spot-rate
  conversion and best-estimate binding with input provenance.
- Added local JSON numeric scenario batches; preserved existing scalar/table/
  symmetric-matrix override audit and validation.
- Added English user guides, a linked function/reference-case catalogue,
  executable examples and standalone package acceptance checks.
- GPL-3.0-or-later; RiskDataScience GmbH.
