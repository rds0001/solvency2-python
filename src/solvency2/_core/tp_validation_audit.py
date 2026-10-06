"""Formal TP-validation/documentation evidence, never actuarial adequacy certification."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory, _reference


@calculation("DR:article-264", "DR:article-265", unit="indicator")
def technical_provision_validation_evidence_check(evidence: Mapping[str, dict],
                                                  conditions: Mapping[str, bool],
                                                  declared_interval_years: float, *,
                                                  assessment_reference: str,
                                                  scope_reference: str, context: Context):
    """Inventory validation and documentation references for an externally qualified scope.

    The declared interval is not a calendar or proof of actual completion.
    Scope must identify all homogeneous groups and applicable segregated parts;
    references alone do not prove completeness, adequacy, or expert review.
    """
    _reference(scope_reference, "scope_reference")
    keys = ("inadequacy_indications", "significant_management_action_impact",
            "matching_adjustment_used", "nonlife_obligations_present", "data_use_changed")
    exact_keys(conditions, keys, "conditions")
    facts = {key: _declared_bool(conditions[key], "conditions." + key) for key in keys}
    interval = number(declared_interval_years, "declared_interval_years", 0)
    require(interval > 0, "declared_interval_years", "strictly positive declared interval required")
    maximum = number(scalar("tp_validation_max_interval_years", context), "tp_validation_max_interval_years", 0)
    require(maximum > 0, "tp_validation_max_interval_years", "positive maximum required", "REVIEW_REQUIRED")
    table = effective_resource("profile.json", context)["tables"]["tp_validation_audit_controls"]
    selected = [row[:3] for row in table["rows"] if row[3] == "always" or facts[row[3]]]
    complete, details = _evidence_inventory(evidence, {"rows": selected}, assessment_reference)
    return int(bool(complete) and interval <= maximum), {
        **details, "conditions": facts, "scope_reference": scope_reference,
        "inactive_controls": [row[0] for row in table["rows"] if row[3] != "always" and not facts[row[3]]],
        "declared_interval_years": interval, "maximum_interval_years": maximum,
        "declared_interval_satisfied": interval <= maximum,
        "evidence_inventory_complete": bool(complete),
        "event_triggered_validation_required": facts["inadequacy_indications"],
        "actual_completion_or_timeliness_verified": False,
        "partition_completeness_verified": False, "qualified_expert_review_performed": False,
        "actuarial_adequacy_certified": False, "technical_provision_value_calculated": False,
        "scope": "declared_TP_validation_documentation_inventory_and_interval_not_audit_opinion"}
