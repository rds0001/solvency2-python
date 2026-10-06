"""Historical Article171a qualification; no insurer ALM or volatility model."""
from .core import exact_keys, number, require, scalar
from .loss_given_default import _known_flag


def baseline_long_term_qualification(inputs, context):
    """Check declared conditions and source thresholds, never certify evidence.

    Average holding duration is externally qualified: the regulation provides
    no weighting algorithm here. Exact equality at five years remains review,
    since the archived text explicitly specifies greater-than and less-than.
    Re-entry months are elapsed calendar months supplied with the assessment;
    no conversion to thirty-day months or automatic supervisory notification.
    """
    require(context.profile_id == "EU-S2-DOCUMENTS-2024-2025-v0.1", "classification.route",
            "historical171a conditions cannot be reused for future105a", "UNSUPPORTED_METHOD")
    conditions = ("subset_and_individual_holding_periods_identified", "assigned_to_identified_best_estimate",
                  "assignment_maintained_for_obligation_lifetime", "separately_managed_and_organised",
                  "not_used_for_other_losses", "only_part_of_total_technical_provisions",
                  "eea_listing_or_unlisted_eea_domicile", "solvency_liquidity_alm_under_stress",
                  "policies_demonstrate_intention_and_capacity")
    fields = (*conditions, "average_holding_years", "no_disposal_until_holding_exceeds_threshold",
              "forced_sale_avoidance_years", "assessment_level", "qualified_article168_6_a_d_fund",
              "previous_condition_breach", "months_since_breach")
    exact_keys(inputs, fields, "classification.inputs")
    flags = {key: _known_flag(inputs[key], key) for key in conditions}
    require(all(flags.values()), "classification", "declared historical171a conditions not met",
            "REVIEW_REQUIRED")
    holding = number(inputs["average_holding_years"], "average_holding_years", 0)
    minimum = number(scalar("long_term_equity_holding_years", context), "holding_threshold", 0)
    require(holding != minimum, "average_holding_years", "exact threshold equality unresolved in source",
            "REVIEW_REQUIRED")
    if holding < minimum:
        require(_known_flag(inputs["no_disposal_until_holding_exceeds_threshold"], "no_disposal_commitment"),
                "no_disposal_commitment", "commitment required until average holding exceeds threshold",
                "REVIEW_REQUIRED")
    else:
        require(inputs["no_disposal_until_holding_exceeds_threshold"] is None,
                "no_disposal_commitment", "not needed above threshold; use None")
    horizon = number(inputs["forced_sale_avoidance_years"], "forced_sale_avoidance_years", 0)
    required_horizon = number(scalar("long_term_equity_forced_sale_years", context), "avoidance_threshold", 0)
    require(horizon >= required_horizon, "forced_sale_avoidance_years", "insufficient declared horizon",
            "REVIEW_REQUIRED")
    level = inputs["assessment_level"]
    require(level in ("investment", "fund"), "assessment_level", "investment or fund required")
    if level == "fund":
        require(_known_flag(inputs["qualified_article168_6_a_d_fund"], "fund_qualification"),
                "fund_qualification", "fund-level shortcut requires168(6)a-d qualification", "REVIEW_REQUIRED")
    else:
        require(inputs["qualified_article168_6_a_d_fund"] is None, "fund_qualification",
                "not needed for investment-level assessment; use None")
    breach = _known_flag(inputs["previous_condition_breach"], "previous_condition_breach")
    exclusion = number(scalar("long_term_equity_reentry_months", context), "reentry_threshold", 0)
    if breach:
        elapsed = number(inputs["months_since_breach"], "months_since_breach", 0)
        require(elapsed >= exclusion, "months_since_breach", "undertaking-wide exclusion still applies",
                "REVIEW_REQUIRED")
    else:
        require(inputs["months_since_breach"] is None, "months_since_breach", "no breach; use None")
    return {"holding_threshold_years": minimum, "forced_sale_horizon_years": required_horizon,
            "reentry_exclusion_months": exclusion, "assessment_level": level,
            "voluntary_return_permitted": False, "breach_requires_immediate_notification": True,
            "supervisory_notification_performed": False, "material_evidence_verified": False,
            "scope": "currently_compliant_declared_subset_not_breach_management_workflow"}
