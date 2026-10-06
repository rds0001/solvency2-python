"""2027 prudent deterministic valuation components, not projection/scenario models."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _evidence_inventory


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


def _eligibility(time_value_options, undertaking_scr, conditions, route,
                 scenario_reference, qualification_reference, context, approval_evidence=None):
    require(isinstance(route, str) and route in {"snc", "approved_non_snc"},
            "route", "explicit SNC or previously approved non-SNC route required", "UNSUPPORTED_METHOD")
    _reference(scenario_reference, "scenario_reference")
    _reference(qualification_reference, "qualification_reference")
    profile = effective_resource("profile.json", context)
    rows = [row for row in profile["tables"]["prudent_deterministic_conditions"]["rows"] if row[0] == route]
    exact_keys(conditions, [row[1] for row in rows], "conditions")
    for _, key, _ in rows:
        require(conditions[key] is not None, key, "qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")
    tv = number(time_value_options, "time_value_options", 0)
    scr = number(undertaking_scr, "undertaking_scr", 0)
    require(scr > 0, "undertaking_scr", "positive SCR required for time-value share", "REVIEW_REQUIRED")
    limit = number(scalar("prudent_deterministic_time_value_limit", context), "time_value_limit", 0)
    below = Fraction(str(tv)) < Fraction(str(limit)) * Fraction(str(scr))
    approval_ok, approval = True, {"status": "NOT_ASSESSED", "evidence_content_verified": False}
    if approval_evidence is not None:
        require(route == "approved_non_snc", "approval_evidence",
                "Article327f approval evidence is specific to the non-SNC route", "UNSUPPORTED_METHOD")
        approval_ok, approval = _evidence_inventory(approval_evidence,
            profile["tables"]["prudent_deterministic_approval_controls"], qualification_reference)
    try:
        share = float(Fraction(str(tv)) / Fraction(str(scr)))
    except OverflowError:
        share = None
    return below and all(conditions.values()) and approval_ok, {
        "route": route, "conditions": dict(conditions), "time_value_options": tv, "undertaking_scr": scr,
        "time_value_share": share, "time_value_share_representable": share is not None,
        "time_value_limit": limit, "strict_time_value_condition": below,
        "scenario_reference": scenario_reference, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "official_scenario_dataset_loaded": False,
        "projection_support": "EXTERNAL_INPUT_ONLY", "supervisory_approval_granted_by_engine": False,
        "approval_evidence": approval,
        "_sources": [row[2] for row in rows] + approval.get("_sources", []) + [context.profile_id + ":" + profile["sources"]["DR"]["sha256"]
                                                + ":articles-34a-327f"]}


@calculation("DIR:article-77:7-8", "DR:article-34a:1", "DR:article-327f:1", unit="indicator")
def prudent_deterministic_eligibility_2027(time_value_options: float, undertaking_scr: float,
                                          conditions: Mapping[str, bool], *, route: str,
                                          scenario_reference: str, qualification_reference: str,
                                          context: Context, approval_evidence: Mapping | None = None):
    """Strict5% time-value screen plus externally qualified route conditions.

    SNC requires written method intention; non-SNC requires existing approval
    and current conditions instead. This never grants supervisory approval or
    computes option time value from an invented scenario set.
    """
    eligible, details = _eligibility(time_value_options, undertaking_scr, conditions, route,
                                    scenario_reference, qualification_reference, context, approval_evidence)
    return int(eligible), {**details, "scope": "numeric_and_declared_condition_screen_only"}


@calculation("DIR:article-77:8", "DR:article-34a:2-3", "DR:article-327f:1", unit="currency")
def prudent_deterministic_best_estimate_2027(deterministic_best_estimate: float, time_value_options: float,
                                            undertaking_scr: float, conditions: Mapping[str, bool], *,
                                            route: str, scenario_reference: str, qualification_reference: str,
                                            alternative_loading: float | None = None,
                                            alternative_loading_demonstrated: bool | None = None,
                                            alternative_loading_reference: str | None = None, context: Context,
                                            approval_evidence: Mapping | None = None):
    """BE_det + loading*SCR, with default5% or externally demonstrated loading.

    The insurer supplies BE, SCR, scenario-based time value and the Article34a(3)
    SCR/LAC-TP treatment. No stress valuation or circular SCR solver is invented.
    Negative deterministic/net BE is preserved; no unsupported100% loading cap.
    """
    eligible, details = _eligibility(time_value_options, undertaking_scr, conditions, route,
                                    scenario_reference, qualification_reference, context, approval_evidence)
    require(eligible, "eligibility", "prudent deterministic conditions not satisfied", "UNSUPPORTED_METHOD")
    be = number(deterministic_best_estimate, "deterministic_best_estimate")
    default = number(scalar("prudent_deterministic_default_loading", context), "default_loading", 0)
    if alternative_loading is None:
        require(alternative_loading_demonstrated is None and alternative_loading_reference is None,
                "alternative_loading", "omit alternative evidence when using the default")
        loading = default
    else:
        require(alternative_loading_demonstrated is not None, "alternative_loading_demonstrated",
                "sufficient demonstration to supervisor unresolved", "REVIEW_REQUIRED")
        require(isinstance(alternative_loading_demonstrated, bool), "alternative_loading_demonstrated",
                "explicit boolean required")
        require(alternative_loading_demonstrated, "alternative_loading_demonstrated",
                "sufficient demonstration to supervisor required", "UNSUPPORTED_METHOD")
        _reference(alternative_loading_reference, "alternative_loading_reference")
        loading = number(alternative_loading, "alternative_loading", 0)
    addition = Fraction(str(loading)) * Fraction(str(details["undertaking_scr"]))
    value = Fraction(str(be)) + addition
    try:
        result, additive = float(value), float(addition)
    except OverflowError:
        require(False, "result", "valuation outside representable range", "REVIEW_REQUIRED")
    return result, {**details, "deterministic_best_estimate": be, "loading_rate": loading,
        "default_loading_rate": default, "stochastic_addition": additive,
        "alternative_loading_reference": alternative_loading_reference,
        "alternative_loading_basis": "EXTERNAL_UNVERIFIED" if alternative_loading is not None else "PROFILE_DEFAULT",
        "scr_lac_tp_treatment": "EXTERNALLY_QUALIFIED_ARTICLE34a3_NOT_COMPUTED",
        "scope": "prudent_best_estimate_arithmetic_not_projection_or_stress_model"}


@calculation("DR:article-327f:1:c", "DR:article-327f:2-3", unit="indicator")
def prudent_deterministic_non_snc_size_screen_2027(undertaking_type: str,
                                                  life_gross_technical_provisions: float,
                                                  total_gross_technical_provisions: float,
                                                  market_shares: Mapping[str, float | None], *,
                                                  size_exception_approved: bool,
                                                  classification_reference: str, context: Context):
    """Only Article327f size/market conditions, NOT supervisory approval.

    Use EUR inputs for the absolute threshold. Market shares require the proper
    home-state denominators: life gross TP versus nonlife gross written premiums.
    Pure nonlife undertakings do not automatically face the life-size cap;
    mixed undertakings do only at or above20% life gross TP. Any waiver is an
    explicit external supervisory finding under paragraph3, never inferred here.
    """
    _reference(classification_reference, "classification_reference")
    require(context.currency == "EUR", "currency", "EUR-qualified amounts required for size screen",
            "UNSUPPORTED_PARAMETER")
    require(isinstance(undertaking_type, str) and undertaking_type in {"life", "nonlife", "composite"},
            "undertaking_type", "explicit undertaking classification required", "UNSUPPORTED_PARAMETER")
    require(size_exception_approved is not None, "size_exception_approved", "exception status unresolved",
            "REVIEW_REQUIRED")
    require(isinstance(size_exception_approved, bool), "size_exception_approved", "explicit boolean required")
    life = number(life_gross_technical_provisions, "life_gross_technical_provisions", 0)
    total = number(total_gross_technical_provisions, "total_gross_technical_provisions", 0)
    require(life <= total, "life_gross_technical_provisions", "life subset cannot exceed total")
    exact_keys(market_shares, ("life", "nonlife"), "market_shares")
    relevant = {undertaking_type} if undertaking_type != "composite" else {"life", "nonlife"}
    shares = {}
    for key in ("life", "nonlife"):
        if key in relevant:
            shares[key] = number(market_shares[key], f"market_shares.{key}", 0, 1)
        else:
            require(market_shares[key] is None, f"market_shares.{key}", "unused market share must be None")
    life_limit = number(scalar("prudent_deterministic_life_tp_limit", context), "life_tp_limit", 0)
    market_limit = number(scalar("prudent_deterministic_market_share_limit", context), "market_share_limit", 0, 1)
    mixed_limit = number(scalar("prudent_deterministic_composite_life_share", context), "mixed_life_share", 0, 1)
    if undertaking_type == "composite":
        require(total > 0, "total_gross_technical_provisions", "positive denominator needed for mixed classification",
                "REVIEW_REQUIRED")
    applies = undertaking_type == "life" or (undertaking_type == "composite" and
        Fraction(str(life)) >= Fraction(str(mixed_limit)) * Fraction(str(total)))
    life_met = not applies or life <= life_limit
    market_met = all(value <= market_limit for value in shares.values())
    profile = effective_resource("profile.json", context)
    return int(size_exception_approved or (life_met and market_met)), {
        "undertaking_type": undertaking_type, "life_size_limit_applies": applies,
        "life_size_condition": life_met, "market_share_condition": market_met,
        "life_tp_limit_eur": life_limit, "market_share_limit": market_limit,
        "composite_life_share_threshold": mixed_limit, "size_exception_approved": size_exception_approved,
        "classification_reference": classification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "supervisory_approval_granted_by_engine": False, "scope": "article327f_size_conditions_only",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-327f"]}
