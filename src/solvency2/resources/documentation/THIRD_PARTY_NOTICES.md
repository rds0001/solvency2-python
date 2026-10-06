# Content, attribution and licenses

Edition: Solvency 2, version 0.5.0. Inventory date: 2026-10-06.
Original library code and invented demonstration data: copyright RiskDataScience
GmbH, GPL-3.0-or-later. The following separately attributed regulatory materials
retain their own reuse terms; they are not relicensed by the software license.

## EU regulatory formulas and numerical tables

Source: © European Union, [EUR-Lex](https://eur-lex.europa.eu/). Resource metadata
identifies the underlying Directive, Delegated Regulation and implementing
legislation, including article/annex anchors and source hashes.
[EUR-Lex reuse terms](https://eur-lex.europa.eu/content/legal-notice/legal-notice.html)
and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) apply to the EU-owned
material. Changes: selected numerical tables extracted into JSON, normalized
labels, formula implementation and separately labelled analyst scenarios.
These extracts are not official consolidated legislation. No EU emblem is used.
German official statutory references are identified by statute and provision;
see [section 5 UrhG](https://www.gesetze-im-internet.de/urhg/__5.html).

## EIOPA material

Source: EIOPA - European Insurance and Occupational Pensions Authority,
https://eiopa.europa.eu/.

This documentation and the regulatory extracts were prepared using material
downloaded from EIOPA's website. EIOPA does not endorse this publication and
accepts no liability for copyright or other intellectual-property infringements
or damages caused to third parties through it. EIOPA originals are available
free of charge from its website, including when this software is supplied
commercially. No EIOPA logo is included.

See [EIOPA's reuse notice](https://www.eiopa.europa.eu/legal-notice_en).
These attribution and non-endorsement statements accompany transformed material;
they do not describe a commercial relationship with EIOPA.

## Reporting extracts: EIOPA Taxonomy Licence Agreement

Copyright EIOPA. Source: the freely available
[supervisory reporting DPM and XBRL materials](https://www.eiopa.europa.eu/tools-and-data/supervisory-reporting-dpm-and-xbrl_en).
Bundled JSON/gzip resources are modified extracts, not official EIOPA release
files. Modification date: 2026-10-06. Changes: selection from database, workbook
and XML sources, normalized identifiers and JSON/gzip serialization.

The complete applicable Taxonomy Licence Agreement version 1.4 (07/10/2025) is
included in `LICENSES/EIOPA_DPM_TAXONOMY_LICENSE_1_4.txt` and wheel license metadata.
It permits redistribution and software embedding on its stated conditions.
Preserve the license, attribution and dated change notices when redistributing.
Its derivative-register, license-back and information-on-request provisions
continue to apply. `THIRD_PARTY_DATA_REGISTER.json` identifies the source archives,
changes and bundled derivatives by SHA-256; update it when modifying these data.
The software and separately licensed reporting data remain distinct components.

## Synthetic market examples and user inputs

The included market grids, dates and reference calculations are invented
demonstrations by RiskDataScience GmbH, licensed GPL-3.0-or-later. They do not
contain observed spot curves, provider credit tables or historical market
snapshots. Their independent arithmetic recipe is included in the data file.
`SYNTHETIC_DEMO` labels and runtime warnings identify calculations using them.

Users load their own production inputs from local files. The software performs
no downloads and grants no rights to third-party data supplied by users.
Keep such inputs outside the public source tree and distribute them only under
the applicable data-owner license. See [local input formats](docs/DATA.md).

SciPy is an optional, separately installed dependency; it is not vendored.
