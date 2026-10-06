# Build and verify locally

The source distribution is self-contained. No generating system, source archive
or separate engine checkout is needed. Build tooling is not a runtime dependency.
Use already installed build tools or a trusted local wheel collection; the
commands below do not request downloads.

```sh
python -m build --no-isolation
python -m pytest -q
```

Build prerequisites: setuptools >=69, wheel and build. Tests require pytest >=8;
the complete inherited reference run additionally needs SciPy >=1.12 for its
optional numerical branches. Without SciPy those designated positive cases are
skipped, and the controlled missing-dependency behavior is checked separately.

Run the acceptance suite once after a substantive package change. During local
adapter development, use `python -m pytest tests/test_inputs.py -q` rather than
rerunning every unchanged reference case. Do not update independent expected
values merely to match current output.

## Independence and distribution boundary

The wheel must contain only the `solvency2` package/resources and distribution
metadata/license notices. The source archive adds these public docs, examples,
tests and build configuration. It must not contain an external engine tree,
regulatory PDF archive, private generation tools, credentials or working logs.
`GOLDEN_SOURCE.json` records original and distributed core hashes and the explicit
public-edition transformations. Formula mathematics and statutory parameter
tables are unchanged. Local market-input handling, demo provenance, market
fixtures and their documentation are adapted for this edition.

For an installation smoke, install the wheel in a fresh environment with
`pip install --no-index --no-deps ...`, change outside the source tree, unset
`PYTHONPATH`, and run the public examples. Rebuild a wheel from an extracted sdist
and check it in a second environment. The release checks also deny network
connections, make package resources read-only, and verify all resource hashes.

The tested environment and actual acceptance results are recorded in
[ACCEPTANCE.md](ACCEPTANCE.md). Python 3.10+ is the syntax/runtime floor; additional
OS/Python combinations are not claimed as tested without evidence.

## Publication is a separate step

No GitHub repository or PyPI release is created by these commands. Before public
release: confirm the repository owner/URLs, retain the supplied license notices
and repeat only checks affected by actual changes. Keep production market data,
customer inputs and credentials outside the repository and release artifacts.
The selected first version is 0.5.0 (0.5), project title Solvency 2, repository
`rds0001/solvency2-python`. PyPI publication remains a separate step.

## GitHub Actions

The workflow runs the complete public test suite on Ubuntu/Python 3.10 with the
optional numerical backend installed, builds wheel and sdist, then tests the
wheel in a separate dependency-free environment with network calls blocked by
the smoke test. CI setup installs development tools; library execution is offline.
Files are tracked as mode 100644 and scripts are invoked through Python, so no
executable bits or platform-specific chmod setup are required on checkout.
