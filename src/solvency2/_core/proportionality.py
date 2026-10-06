"""Declared simplification conditions, never a substitute for actuarial assessment."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar


def _facts(conditions, keys, reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external substantive assessment reference required", "MISSING_INPUT")
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        require(conditions[key] is not None, key, "qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")


@calculation("DR:article-88:1-2", unit="indicator")
def simplification_proportionality_conditions(conditions: Mapping[str, bool], *,
                                             simplified_scr_higher: bool | None = None,
                                             qualification_reference: str, context: Context):
    """Screen declared assessments and the higher-SCR exception to material error.

    Do not create a quantitative materiality threshold. A comparison with the
    standard calculation is only requested where the exception is invoked;
    the result records supplied facts, not a substantive adequacy conclusion.
    """
    _facts(conditions, ("risk_assessed", "error_assessed", "decision_relevant_error"), qualification_reference)
    relevant = conditions["decision_relevant_error"]
    if relevant:
        require(simplified_scr_higher is not None, "simplified_scr_higher", "comparison unresolved", "REVIEW_REQUIRED")
        require(isinstance(simplified_scr_higher, bool), "simplified_scr_higher", "explicit boolean required")
    else:
        require(simplified_scr_higher is None, "simplified_scr_higher", "unused exception comparison; omit")
    value = conditions["risk_assessed"] and conditions["error_assessed"] and (not relevant or simplified_scr_higher)
    return int(value), {"conditions": dict(conditions), "simplified_scr_higher": simplified_scr_higher,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "declared_DR88_conditions_not_materiality_model_or_approval"}


@calculation("DR:article-105a", unit="indicator")
def unrated_bond_simplification_conditions(rated_share: float, conditions: Mapping[str, bool], *,
                                          qualification_reference: str, context: Context):
    """Check the inclusive rated-portfolio share and qualified bond facts.

    The portfolio denominator excludes Article180(2-16) positions. Classification
    against the referenced reporting definitions and liability cover is external;
    a missing rating field is never treated as evidence of an unrated bond.
    """
    keys = ("article88_satisfied", "outside_article180_2_16", "unrated",
            "fixed_redemption_regular_interest", "not_structured_or_collateralised",
            "not_covering_excluded_liabilities")
    _facts(conditions, keys, qualification_reference)
    share = number(rated_share, "rated_share", 0, 1)
    threshold = number(scalar("unrated_bond_simplification_rated_share", context), "rated_share_threshold", 0, 1)
    enough_rated = Fraction(str(share)) >= Fraction(str(threshold))
    return int(enough_rated and all(conditions.values())), {"conditions": dict(conditions),
        "rated_share": share, "rated_share_threshold": threshold, "rated_share_condition": enough_rated,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "DR105a_conditions_not_automatic_quality_assignment"}
