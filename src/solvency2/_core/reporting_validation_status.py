"""Archived workbook decisions only; never a present-day supervisory clearance.

One rule code can identify several workbook rows, including distinct XBRL and
non-XBRL checks. Preserve ambiguity rather than silently choosing the last row.
Dates describe the archived snapshot, not a reconstructed activation history.
"""
from copy import deepcopy
from datetime import date
import re


def reporting_validation_status(validation_code, *, technical_version, module):
    """Return one archived module/rule status, not a regulatory filing decision.

    No date-based automatic taxonomy selection, internet lookup, insurer model,
    or submission occurs. Read source snapshot dates and REVIEW_REQUIRED states.
    """
    from solvency2._core.core import CalculationError, _resource_snapshot, fingerprint
    from solvency2._core.reporting_catalog import _reporting_validation_metadata

    with _resource_snapshot():
        metadata = _reporting_validation_metadata(technical_version=technical_version)
        try:
            result = assess_archived_rule(metadata, validation_code, module)
        except (TypeError, ValueError) as error:
            raise CalculationError("INVALID_INPUT", "validation_status", str(error)) from error
        result["input_hash"] = fingerprint({"validation_code": validation_code, "module": module,
                                             "technical_version": technical_version})
        return result


def module_severities(text):
    """Parse the workbook's explicit ERROR/WARNING and module declarations."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Missing module/severity declaration")
    parts = text.split("|")
    if not parts[-1].strip():
        parts.pop()
    output = {}
    for part in parts:
        match = re.fullmatch(r"\s*(ERROR|WARNING)\s*-\s*([a-z][a-z0-9]*)\s*", part)
        if match is None or match[2] in output:
            raise ValueError("Unknown or duplicate module/severity declaration")
        output[match[2]] = match[1]
    return output


def _date(value):
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise ValueError("Explicit ISO calendar date required")
    return date.fromisoformat(value)


def _activation(row, snapshot_date):
    """Return a conservative snapshot decision and a machine-readable reason."""
    flag = row.get("Deactivated")
    full = row.get("Full or partial deactivation")
    off, on = row.get("Deactivated on"), row.get("Reactivated on")
    if flag not in ("yes", "no"):
        return None, "UNKNOWN_DEACTIVATION_FLAG"
    if full not in (None, "", "Full"):
        return None, "PARTIAL_OR_UNKNOWN_DEACTIVATION_SCOPE"
    try:
        off = _date(off) if off is not None else None
        on = _date(on) if on is not None else None
    except ValueError:
        return None, "INVALID_STATUS_DATE"
    if any(value is not None and value > snapshot_date for value in (off, on)):
        return None, "STATUS_DATE_AFTER_SNAPSHOT"
    if flag == "yes":
        if full != "Full" or off is None or on is not None:
            return None, "INCONSISTENT_DEACTIVATION_EVIDENCE"
        return False, "FULLY_DEACTIVATED_IN_SNAPSHOT"
    if on is not None:
        if off is None or on <= off:
            return None, "INCONSISTENT_REACTIVATION_EVIDENCE"
        return True, "REACTIVATED_IN_SNAPSHOT"
    if off is not None or full not in (None, ""):
        return None, "INCONSISTENT_ACTIVE_EVIDENCE"
    return True, "ACTIVE_IN_SNAPSHOT"


def assess_archived_rule(metadata, validation_code, module):
    """Identify module-specific workbook rows without discarding other rows.

    Investigation is not deactivation. Non-XBRL checks are not automatically
    inactive. Unknown, partial or conflicting evidence yields no Boolean release.
    """
    if not isinstance(validation_code, str) or not validation_code:
        raise ValueError("Exact rule code required")
    if not isinstance(module, str) or re.fullmatch(r"[a-z][a-z0-9]*", module) is None:
        raise ValueError("Exact archived module code required")
    snapshot = _date(metadata["snapshot_date"])
    entries, relevant, malformed = [], [], False
    for entry in metadata["rows"]:
        row = entry["values"]
        if row.get("Rule code") != validation_code:
            continue
        item = deepcopy(entry)
        try:
            severities = module_severities(row.get("Severity and modules"))
        except ValueError:
            severities = {}
            malformed = True
        item["module_severities"] = severities
        item["active_in_snapshot"], item["activation_reason"] = _activation(row, snapshot)
        entries.append(item)
        if module in severities:
            relevant.append(item)
    active, severity, implementation = None, None, None
    if malformed:
        reason = "UNQUALIFIED_MODULE_DECLARATION"
    elif not entries:
        reason = "RULE_NOT_LISTED"
    elif not relevant:
        reason = "RULE_NOT_LISTED_FOR_MODULE"
    elif len(relevant) != 1:
        reason = "AMBIGUOUS_WORKBOOK_ROWS"
    else:
        selected = relevant[0]
        severity = selected["module_severities"][module]
        included = selected["values"].get("Include in XBRL")
        if included not in ("yes", "no"):
            reason = "UNKNOWN_IMPLEMENTATION_CHANNEL"
        else:
            implementation = "XBRL_ASSERTION" if included == "yes" else "OTHER_REQUIRED_CHECK"
            active, reason = selected["active_in_snapshot"], selected["activation_reason"]
    comparison = metadata.get("related_snapshot_comparison", {})
    conflicts = [change for change in comparison.get("changes", []) if change["validation_code"] == validation_code]
    if conflicts:
        # Keep each source row's own activation result, but never turn the
        # disagreement into an automatic cross-snapshot release.
        active, reason = None, "RELATED_SNAPSHOT_CONFLICT"
    return {"status": "ARCHIVED_RULE_STATUS_COMPONENT" if active is not None else "REVIEW_REQUIRED",
            "technical_version": metadata["technical_version"], "validation_code": validation_code,
            "module": module, "snapshot_date": metadata["snapshot_date"],
            "source": deepcopy(metadata["source"]), "sheet": metadata["sheet"],
            "active_in_snapshot": active, "reason": reason, "severity": severity,
            "implementation_channel": implementation, "entries": entries,
            "related_snapshot_conflicts": deepcopy(conflicts),
            "related_snapshot_source": deepcopy(comparison.get("source")),
            "current_deactivations_checked": False, "legal_applicability_verified": False,
            "activation_history_reconstructed": False, "full_report_validated": False}
