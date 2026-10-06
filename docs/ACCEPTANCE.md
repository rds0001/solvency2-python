# Local acceptance — public-data edition

Version: solvency2-python 0.5.0, import `solvency2`.
This edition retains the accepted calculation baseline and statutory parameters.
Its market examples are independently invented; no historical provider market
archive is included. No GitHub or PyPI publication is performed by local checks.

## Scope and change-focused verification

The package has 399 calculations, 421 inherited public exports, 11 input/discovery
helpers, 12,382 independent core reference cases, 227 integration portfolios and
ten additional reporting reference datasets.

The accepted predecessor had already passed its full calculation/reporting
reference run. Unchanged cases have not been rerun merely for packaging.
The following focused checks were performed on the public-data edition:

| Check | Result |
|---|---|
| Market-input/demo/provenance tests, local-input tests and package contracts | 81 passed; initial run 11.69 seconds |
| RFR-related references and all 227 integration portfolios | 412 passed, 73.57 seconds |
| Unchanged reference cases omitted from that focused run | 12,197 deselected, not failures or newly claimed passes |
| Syntax/static checks on the new market interface, its tests and private preparation tools | Passed |
| All original statutory and reporting numerical resources | Byte-identical to the accepted predecessor |
| Changed core files | Only market lookup IO, calculation demo status and workflow demo propagation |
| Full public API | All 399 calculations and inherited exports retained |

The market-specific tests are also rerun after final input-error normalization
to verify the preserved machine-readable error codes. Expected demo warnings
are intentional and tested. Fixtures are independent arithmetic specifications,
not recomputed expected outputs from the implementation.

Test environment: Python 3.10 on Linux, pytest 9.0.2 and SciPy 1.12.0.
Python 3.10 is the tested runtime; other OS/Python combinations are not represented
as tested. Original source hashes, emitted hashes and explicit edition changes
are recorded in `GOLDEN_SOURCE.json`.

## Build and independent installation record

The local `dist/LOCAL_ACCEPTANCE.json` file records the final wheel and sdist
sizes/hashes and the observed distribution check result. A PASS record covers:

- wheel rebuilt from the sdist with byte-identical payload;
- two independent installations outside the source tree, with no dependencies;
- offline smoke checks with network connections and installation writes denied;
- verification of every bundled resource/document hash and API import;
- synthetic-data warning/status and explicit absence of optional SciPy;
- package boundaries excluding private generation tools and regulatory originals.

The base runtime needs no third-party package. SciPy is separately required for
the documented optional numerical methods; its absence produces a controlled
error rather than a substituted calculation.

The software's existing regulatory scope flags and applicability guards remain
unchanged. Technical acceptance is a software result, not supervisory approval.
