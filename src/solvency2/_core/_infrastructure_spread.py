"""Connect declared 164a/b screens to 180; never infer substantive eligibility."""
from collections.abc import Mapping

from .core import exact_keys, require


def qualify_infrastructure_spread(qualification, category, credit_quality_step, context):
    exact_keys(qualification, ("screen_inputs", "in_matching_adjustment_portfolio",
                              "exposure_credit_quality_step"), "qualification")
    inputs = qualification["screen_inputs"]
    require(isinstance(inputs, Mapping) and "context" not in inputs,
            "screen_inputs", "screen inputs without a separate context required")
    ma = qualification["in_matching_adjustment_portfolio"]
    require(ma is not None, "in_matching_adjustment_portfolio", "MA scope unknown", "REVIEW_REQUIRED")
    require(isinstance(ma, bool), "in_matching_adjustment_portfolio", "explicit boolean required")
    cqs = qualification["exposure_credit_quality_step"]
    require(cqs is None or (isinstance(cqs, str) and cqs in {str(i) for i in range(7)}),
            "exposure_credit_quality_step", "explicit assigned CQS0..6 or known absence required")
    rated = not category.endswith("_unrated")
    if rated:
        require(cqs == credit_quality_step, "exposure_credit_quality_step",
                "assigned exposure CQS must agree with the selected rated table", "REVIEW_REQUIRED")
    require(not (ma and cqs in {"0", "1", "2"}), "qualification",
            "MA portfolio together with assigned CQS0..2 excludes the infrastructure table",
            "UNSUPPORTED_METHOD")
    if category.startswith("infrastructure_corporate"):
        from .infrastructure_corporate import infrastructure_corporate_eligibility_screen as screen
        require(inputs.get("instrument") == "debt" and inputs.get("rating_available") is rated,
                "screen_inputs", "corporate debt and company rating availability must match route",
                "REVIEW_REQUIRED")
        # Company rating in 164b is not silently identified with exposure rating in 180(15)d.
        source = "DR:article-180:15-16"
    else:
        from .infrastructure_project import infrastructure_project_eligibility_screen as screen
        require(inputs.get("investment_kind") == ("rated_debt" if rated else "unrated_debt"),
                "screen_inputs", "project debt rating availability must match route", "REVIEW_REQUIRED")
        if not rated:
            require(cqs is None, "exposure_credit_quality_step",
                    "unrated project exposure cannot also have an assigned ECAI CQS", "REVIEW_REQUIRED")
        source = "DR:article-180:12-13"
    result = screen(**inputs, context=context)
    require(result.value == 1, "qualification", "declared infrastructure prerequisites not met",
            "UNSUPPORTED_METHOD")
    return {"status": "DECLARED_PREREQUISITES_CHECKED_NOT_LEGAL_APPROVAL",
            "in_matching_adjustment_portfolio": ma, "exposure_credit_quality_step": cqs,
            "screen": result.details, "substantive_eligibility_verified": False}, [source, *result.sources]
