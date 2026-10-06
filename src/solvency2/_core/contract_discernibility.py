"""Guidelines6A/6B evidence joins; materiality and actuarial valuations stay external."""
import math
from typing import Mapping

from .contracts import _reference
from .core import exact_keys, number, require


def _true(value, field):
    require(type(value) is bool, field, "known boolean required", "REVIEW_REQUIRED")
    require(value, field, "assessment requirement not met", "REVIEW_REQUIRED")


def assess_discernibility(data, boundary):
    """Return copied boundary facts plus audited assessments; no input mutation.

    No universally prescribed relative-difference denominator or significance
    threshold exists here. Keep the comparison and analyst's decision explicit.
    """
    if data is None:
        return dict(boundary), {"status": "NOT_ASSESSED"}, []
    fields = {"cover": "discernible_uncertain_event_cover", "guarantee": "discernible_financial_guarantee"}
    require(isinstance(data, Mapping) and bool(data), "discernibility", "nonempty assessment mapping required")
    require(set(data) <= set(fields), "discernibility", "only cover/guarantee assessments supported")
    resolved, audit, sources = dict(boundary), {}, []
    for kind, row in data.items():
        exact_keys(row, ("linked_to_future_premiums", "discernible_advantage", "method",
                        "all_potential_cashflows_considered", "comparison", "assessment_reference"), kind)
        _reference(row["assessment_reference"], kind + ".assessment_reference")
        linked = row["linked_to_future_premiums"]
        require(type(linked) is bool, kind + ".linked_to_future_premiums", "known boolean required", "REVIEW_REQUIRED")
        difference = None
        if not linked:
            # The necessary condition already fails; do not require a pointless
            # valuation or treat absent comparison data as an implicit pass.
            discernible = False
            comparison_status = "NOT_REQUIRED_NO_PREMIUM_LINK"
        else:
            _true(row["all_potential_cashflows_considered"], kind + ".all_potential_cashflows_considered")
            require(type(row["discernible_advantage"]) is bool, kind + ".discernible_advantage",
                    "explicit analyst economic-advantage decision required", "REVIEW_REQUIRED")
            method, comparison = row["method"], row["comparison"]
            require(method in ("qualitative", "quantitative"), kind + ".method", "explicit comparison method required")
            if method == "qualitative":
                exact_keys(comparison, ("reference", "risk_timing_amount_considered"), kind + ".comparison")
                _true(comparison["risk_timing_amount_considered"], kind + ".risk_timing_amount_considered")
            else:
                keys = ("reference", "with_feature_present_value", "without_feature_present_value",
                        "relative_difference_assessed", "without_feature_cashflows_qualified")
                keys += (("relevant_scenarios_considered",) if kind == "cover" else
                         ("guaranteed_benefits_and_option_time_value_considered", "market_return_dependent",
                          "baseline_rfr_without_va_ma"))
                exact_keys(comparison, keys, kind + ".comparison")
                for key in ("relative_difference_assessed", "without_feature_cashflows_qualified"):
                    _true(comparison[key], kind + "." + key)
                with_value = number(comparison["with_feature_present_value"], kind + ".with_feature_present_value")
                without_value = number(comparison["without_feature_present_value"], kind + ".without_feature_present_value")
                difference = with_value - without_value
                require(math.isfinite(difference), kind + ".present_value_difference", "finite difference required")
                require(difference != 0 or not row["discernible_advantage"], kind + ".discernible_advantage",
                        "zero quantitative difference cannot support discernible advantage", "REVIEW_REQUIRED")
                if kind == "cover":
                    _true(comparison["relevant_scenarios_considered"], kind + ".relevant_scenarios_considered")
                else:
                    _true(comparison["guaranteed_benefits_and_option_time_value_considered"], kind + ".option_time_value")
                    require(type(comparison["market_return_dependent"]) is bool, kind + ".market_return_dependent",
                            "known boolean required", "REVIEW_REQUIRED")
                    if comparison["market_return_dependent"]:
                        _true(comparison["baseline_rfr_without_va_ma"], kind + ".baseline_rfr_without_va_ma")
            _reference(comparison["reference"], kind + ".comparison.reference")
            discernible = row["discernible_advantage"]
            comparison_status = "EXTERNAL_UNVERIFIED"
        original = boundary[fields[kind]]
        require(original is None or original is discernible, kind,
                "explicit boundary fact contradicts supplied assessment", "REVIEW_REQUIRED")
        resolved[fields[kind]] = discernible
        audit[kind] = {"assessment": dict(row), "derived_discernible": discernible,
                       "supplied_boundary_fact": original, "comparison_status": comparison_status,
                       "present_value_difference": difference, "materiality_threshold_invented": False}
        sources.append("CB_GUIDANCE:guideline-6A" if kind == "guarantee" else "CB_GUIDANCE:guideline-6B")
    return resolved, audit, sources
