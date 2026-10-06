"""Shared declared AnnexXX section-order check; never reads or certifies a report."""
from .core import require
from .evidence import _reference


def report_structure_check(profile, report_kind, sections, reference):
    if sections is None:
        require(reference is None, "structure_reference", "reference without declared sections is unused")
        return True, {"status": "NOT_ASSESSED", "actual_report_verified": False}, []
    _reference(reference, "structure_reference")
    require(isinstance(sections, list) and all(isinstance(key, str) and key.strip() for key in sections),
            "structure_sections", "ordered list of nonempty normative section identifiers required")
    rows = [row for row in profile["tables"]["report_structure"]["rows"] if row[0] == report_kind]
    require(bool(rows), "report_kind", "no AnnexXX structure for this report kind", "UNSUPPORTED_PARAMETER")
    expected = [row[1] for row in rows]
    require(len(expected) == len(set(expected)), "report_structure", "unique prescribed identifiers required",
            "REVIEW_REQUIRED")
    matches = sections == expected
    seen, duplicates = set(), []
    for key in sections:
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return matches, {"status": "MATCH" if matches else "MISMATCH", "report_kind": report_kind,
        "declared_sections": list(sections), "expected_sections": expected,
        "missing_sections": [key for key in expected if key not in seen],
        "unexpected_sections": list(dict.fromkeys(key for key in sections if key not in expected)),
        "duplicate_sections": duplicates, "exact_order_matches": matches,
        "structure_reference": reference, "actual_report_verified": False,
        "titles_or_contents_verified": False}, [row[4] for row in rows]
