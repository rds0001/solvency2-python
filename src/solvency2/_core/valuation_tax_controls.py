"""Optional tax recognition evidence and attributed group-exclusion arithmetic."""

import math
from collections.abc import Mapping

from .core import exact_keys, number, require


def tax_controls(asset, liability, exclusions, level, conditions, documents):
    details = {"recognition_conditions_status": "NOT_ASSESSED",
               "recognition_documents_status": "NOT_ASSESSED", "participation_exclusions_status": "NOT_ASSESSED"}
    sources = []
    if conditions is not None:
        fields = ("profits_probable_in_usable_periods", "past_profitability_not_sole_evidence",
                  "long_horizon_uncertainty_considered", "carry_limits_considered",
                  "no_double_counting_of_used_reversals", "projections_consistent_with_tp_and_balance_sheet")
        exact_keys(conditions, fields, "recognition_conditions")
        require(all(value is True for value in conditions.values()), "recognition_conditions",
                "all externally assessed recognition conditions must be established", "REVIEW_REQUIRED")
        details.update(recognition_conditions_status="DECLARED_CONDITIONS_CHECKED",
                       recognition_conditions=dict(conditions))
        sources.append("VALUATION_GUIDANCE:guideline-9:1.28-1.29")
    if documents is not None:
        fields = ("source_records", "recognition_principles", "amounts_and_assumptions_by_type",
                  "timing_profit_support", "recognised_and_unrecognised_expiry_schedule")
        exact_keys(documents, fields, "recognition_documents")
        require(all(isinstance(value, str) and bool(value.strip()) for value in documents.values()),
                "recognition_documents", "explicit external document references required", "MISSING_INPUT")
        details.update(recognition_documents_status="REFERENCES_PRESENT_CONTENT_UNVERIFIED",
                       recognition_documents=dict(documents))
        sources.append("VALUATION_GUIDANCE:guideline-10:1.30")
    if exclusions is None:
        require(level is None, "valuation_level", "omit unused level without explicit exclusion mapping")
        return asset, liability, details, sources
    require(isinstance(exclusions, Mapping), "excluded_participations", "explicit mapping required")
    require(isinstance(level, str) and level in {"solo", "group"}, "valuation_level", "solo or group required")
    rows = {}
    for key, row in exclusions.items():
        require(isinstance(key, str) and bool(key.strip()), "participation_id", "nonempty disjoint participation ID required")
        exact_keys(row, ("basis", "deferred_tax_assets", "deferred_tax_liabilities",
                         "supervisory_reference", "attribution_reference"), key)
        require(isinstance(row["basis"], str) and row["basis"] in {"a", "b", "c"}, key + ".basis", "Article214(2)a/b/c required")
        for name in ("supervisory_reference", "attribution_reference"):
            require(isinstance(row[name], str) and bool(row[name].strip()), key + "." + name,
                    "qualified supervisory decision and same-scope tax attribution required", "MISSING_INPUT")
        rows[key] = {**row, "deferred_tax_assets": number(row["deferred_tax_assets"], key + ".deferred_tax_assets", 0),
                     "deferred_tax_liabilities": number(row["deferred_tax_liabilities"], key + ".deferred_tax_liabilities", 0),
                     "excluded_at_selected_level": row["basis"] == "a" or level == "group"}
    totals = {field: math.fsum(row[field] for row in rows.values())
              for field in ("deferred_tax_assets", "deferred_tax_liabilities")}
    require(totals["deferred_tax_assets"] <= asset and totals["deferred_tax_liabilities"] <= liability,
            "excluded_participations", "disjoint attributed amounts exceed the supplied gross balances")
    excluded = {field: math.fsum(row[field] for row in rows.values() if row["excluded_at_selected_level"])
                for field in totals}
    details.update(participation_exclusions_status="ATTRIBUTED_EXCLUSIONS_APPLIED",
                   valuation_level=level, participation_attributions=rows,
                   excluded_deferred_tax_assets=excluded["deferred_tax_assets"],
                   excluded_deferred_tax_liabilities=excluded["deferred_tax_liabilities"])
    sources.append("VALUATION_GUIDANCE:guideline-11:1.31")
    return asset - excluded["deferred_tax_assets"], liability - excluded["deferred_tax_liabilities"], details, sources
