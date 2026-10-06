"""Premium/reserve capital from explicit selected segment volumes."""
import math
from typing import Mapping

from .aggregation import quadratic
from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _forced_geography_segments(profile, risk_type):
    """Keep the2027 removal of nonlife segment12 local to its source profile."""
    return profile["methods"]["geographic_forced_segments"][risk_type]


@calculation("DR:annex-III:1-8", "DR:article-116:7", "DR:article-147:7", unit="ratio")
def premium_reserve_diversification(*, risk_type: str, segment: str, method: str,
                                   uses_usp: bool, regional_volumes: Mapping[str, dict] | None = None,
                                   context: Context):
    """Geographic factor from already classified volumes, including mandatory exceptions.

    Regional maxima/floors must be calculated regionally: their sum need not
    equal the separately calculated segment volume used by the risk function.
    This function does not classify countries or validate USP authorisation.
    """
    require(risk_type in ("nonlife", "health_nslt"), "risk_type", "unknown underwriting type")
    segments = tuple(str(i) for i in range(1, 13 if risk_type == "nonlife" else 5))
    require(segment in segments, "segment", "segment outside the selected annex")
    require(isinstance(uses_usp, bool), "uses_usp", "explicit boolean required")
    require(method in ("default", "calculated"), "method", "explicit default or calculated required")
    default = number(scalar("geography_default", context), "geography_default", 0, 1)
    require(default > 0, "geography_default", "positive factor required")
    forced = segment in _forced_geography_segments(effective_resource("profile.json", context), risk_type)
    if method == "default":
        require(regional_volumes is None, "regional_volumes", "not used by default method")
        return default, {"method": method, "risk_type": risk_type, "segment": segment,
                         "uses_usp": uses_usp, "selection_reason": "explicit_default"}
    require(regional_volumes is not None, "regional_volumes", "all 18 regions required", "MISSING_INPUT")
    labels = tuple(str(i) for i in range(1, 19))
    exact_keys(regional_volumes, labels, "regional_volumes")
    # Scale individual inputs before adding them, avoiding overflow even when
    # two individually finite regional volumes would sum beyond float range.
    volumes = {}
    for region in labels:
        row = regional_volumes[region]
        exact_keys(row, ("premium_volume", "reserve_volume"), region)
        volumes[region] = (number(row["premium_volume"], f"{region}.premium_volume", 0),
                           number(row["reserve_volume"], f"{region}.reserve_volume", 0))
    detail = {"method": method, "risk_type": risk_type, "segment": segment,
              "uses_usp": uses_usp, "scope": "externally_classified_regional_volumes"}
    if forced or uses_usp:
        return default, {**detail, "selection_reason": "mandatory_segment" if forced else "usp"}
    scale = max(value for pair in volumes.values() for value in pair)
    require(scale > 0, "regional_volumes", "zero/zero ratio: select default explicitly if appropriate",
            "REVIEW_REQUIRED")
    totals = {key: p / scale + r / scale for key, (p, r) in volumes.items()}
    total = math.fsum(totals.values())
    shares = {key: value / total for key, value in totals.items()}
    return math.fsum(value * value for value in shares.values()), {
        **detail, "selection_reason": "regional_concentration", "regional_shares": shares}


@calculation("DR:article-116:3", "DR:article-116:4", "DR:article-116:5")
def nonlife_premium_volume(expected_next_year: float, earned_last_year: float,
                           existing_future_pv: float, future_short_pv: float,
                           future_long_pv: float, *, method: str,
                           cap_evidence: Mapping[str, str] | None = None, context: Context):
    """Article 116 premium volume from externally selected net premium cashflows.

    Future short contracts exclude premiums earned in their first twelve months
    after recognition; future long contracts use premiums beyond the next twelve
    months from valuation. The supplied long-contract PV is still unweighted.
    Evidence references record, but cannot substantively verify, paragraph 4.
    """
    return _premium_volume(expected_next_year, earned_last_year, existing_future_pv,
                           future_short_pv, future_long_pv, method, cap_evidence,
                           "nonlife_future_long_premium_weight", context)


@calculation("DR:article-147:3", "DR:article-147:4", "DR:article-147:5")
def health_premium_volume(expected_next_year: float, earned_last_year: float,
                          existing_future_pv: float, future_short_pv: float,
                          future_long_pv: float, *, method: str,
                          cap_evidence: Mapping[str, str] | None = None, context: Context):
    """Health-NSLT net premium volume; cohort/time selection and evidence are external."""
    return _premium_volume(expected_next_year, earned_last_year, existing_future_pv,
                           future_short_pv, future_long_pv, method, cap_evidence,
                           "health_future_long_premium_weight", context)


def _premium_volume(expected_next_year, earned_last_year, existing_future_pv,
                    future_short_pv, future_long_pv, method, cap_evidence, factor_key, context):
    """Shared Article 116/147 arithmetic; public wrappers retain distinct sources/weights."""
    expected = number(expected_next_year, "expected_next_year")
    previous = number(earned_last_year, "earned_last_year")
    existing = number(existing_future_pv, "existing_future_pv")
    short = number(future_short_pv, "future_short_pv")
    long = number(future_long_pv, "future_long_pv")
    require(method in ("standard", "management_cap"), "method", "unknown premium-volume method")
    if method == "management_cap":
        require(cap_evidence is not None, "cap_evidence", "three condition references required",
                "MISSING_INPUT")
        exact_keys(cap_evidence, ("board_decision", "controls", "supervisory_notification"),
                   "cap_evidence")
        for key, reference in cap_evidence.items():
            require(isinstance(reference, str) and bool(reference.strip()),
                    f"cap_evidence.{key}", "nonempty external evidence reference required")
        first_year = expected
    else:
        require(cap_evidence is None, "cap_evidence", "not used by standard method")
        first_year = max(expected, previous)
    factor = number(scalar(factor_key, context), factor_key, 0, 1)
    future = short + factor * long
    volume = first_year + existing + future
    # Paragraph 6 prescribes a reserve floor, but paragraph 3 does not prescribe
    # a premium floor. Do not invent one to fit the downstream nonnegative API.
    require(volume >= 0, "premium_volume", "negative total requires separate interpretation",
            "REVIEW_REQUIRED")
    return volume, {"first_year_component": first_year, "existing_future_pv": existing,
                    "future_short_pv": short, "future_long_pv": long,
                    "future_long_weight": factor, "future_premium_component": future,
                    "method": method, "cap_evidence": dict(cap_evidence) if cap_evidence else None,
                    "scope": "externally_selected_net_cashflows_and_evidence"}


@calculation("DR:article-116:6")
def nonlife_reserve_volume(claims_best_estimate: float, eligible_recoverables: float, *,
                           context: Context):
    """Net claims BE; eligible recoverables must exclude208(2) finite/similar RI."""
    return _reserve_volume(claims_best_estimate, eligible_recoverables)


@calculation("DR:article-147:6")
def health_reserve_volume(claims_best_estimate: float, eligible_recoverables: float, *,
                          context: Context):
    """Health-NSLT claims volume; recoverables exclude208(2) finite/similar RI."""
    return _reserve_volume(claims_best_estimate, eligible_recoverables)


def _reserve_volume(claims_best_estimate, eligible_recoverables):
    gross = number(claims_best_estimate, "claims_best_estimate")
    recoverables = number(eligible_recoverables, "eligible_recoverables")
    net = gross - recoverables
    return max(net, 0), {"claims_best_estimate": gross, "eligible_recoverables": recoverables,
                         "article208_finite_or_similar_recoverables": "EXCLUDED_BY_INPUT_CONTRACT",
                         "net_before_floor": net, "floor_applied": net < 0,
                         "scope": "claims_only_and_externally_qualified_recoverables"}


@calculation("DR:article-115", "DR:article-116:2", "DR:article-117", "DR:annex-II", "DR:annex-IV")
def premium_reserve_risk(segments: Mapping[str, dict], *, premium_nonproportional_cover: Mapping | None = None,
                         reserve_adjustments: Mapping | None = None, adjustment_reference: str | None = None,
                         uses_usp: bool | None = None, context: Context):
    """Nonlife sigma aggregation with explicit2027 reinsurance/USP qualification.

    Future premium80% factors require a declared existing nonproportional cover
    in segments1/4/5. Reserve factors are supplied separately; no absence of ADC
    is inferred from missing input. Historical callers keep the original API.
    """
    profile = effective_resource("profile.json", context)
    future = profile.get("methods", {}).get("nonlife_reinsurance_adjustment") == "CONDITIONAL_NP_AND_ADC_2027"
    if future:
        require(uses_usp is not None, "uses_usp", "explicit variant required", "MISSING_INPUT")
        require(isinstance(uses_usp, bool), "uses_usp", "boolean required")
        require(not uses_usp, "uses_usp", "use premium_reserve_parameterised_risk with qualified effective USP sigmas", "UNSUPPORTED_METHOD")
        labels = tuple(str(i) for i in range(1, 13))
        require(premium_nonproportional_cover is not None, "premium_nonproportional_cover",
                "all twelve premium cover flags required", "MISSING_INPUT")
        require(reserve_adjustments is not None, "reserve_adjustments",
                "all twelve qualified reserve factors required", "MISSING_INPUT")
        exact_keys(premium_nonproportional_cover, labels, "premium_nonproportional_cover")
        exact_keys(reserve_adjustments, labels, "reserve_adjustments")
        require(isinstance(adjustment_reference, str) and bool(adjustment_reference.strip()),
                "adjustment_reference", "external reinsurance qualification required", "MISSING_INPUT")
        reduced = number(scalar("nonprop_adjustment", context), "nonprop_adjustment", 0, 1)
        default = number(scalar("nonlife_nonprop_default", context), "nonlife_nonprop_default", 0, 1)
        premium_factors, reserve_factors = {}, {}
        for key in labels:
            covered = premium_nonproportional_cover[key]
            require(isinstance(covered, bool), f"premium_nonproportional_cover.{key}", "boolean required")
            premium_factors[key] = reduced if covered and key in {"1", "4", "5"} else default
            reserve_factors[key] = number(reserve_adjustments[key], f"reserve_adjustments.{key}", 0)
        value, details = _premium_reserve_risk(segments, "nonlife", context, reserve_factors, premium_factors)
        return value, {**details, "premium_nonproportional_cover": dict(premium_nonproportional_cover),
                       "premium_adjustments": premium_factors, "reserve_adjustments": reserve_factors,
                       "adjustment_reference": adjustment_reference, "adjustment_status": "EXTERNAL_UNVERIFIED"}
    require(premium_nonproportional_cover is None and reserve_adjustments is None
            and adjustment_reference is None and uses_usp is None, "reinsurance_adjustments",
            "these arguments require the2027 profile", "UNSUPPORTED_METHOD")
    return _premium_reserve_risk(segments, "nonlife", context)


@calculation("DR:article-146", "DR:article-147:2", "DR:article-148", "DR:annex-XIV", "DR:annex-XV")
def health_premium_reserve_risk(segments: Mapping[str, dict], *, uses_usp: bool,
                                uses_hres: bool, reserve_adjustments: Mapping | None = None,
                                adjustment_reference: str | None = None, context: Context):
    """Four-segment standard selector; USP/HRES are deliberately not substituted.

    Use premium_reserve_parameterised_risk for already qualified effective
    USP/HRES sigmas. This automatic standard selector does not choose them.

    The2027 profile requires all four externally qualified reserve factors,
    including explicit ones for segments without a qualifying ADC adjustment.
    Historical calculations reject these future-only inputs.
    """
    require(isinstance(uses_usp, bool), "uses_usp", "explicit boolean required")
    require(isinstance(uses_hres, bool), "uses_hres", "explicit boolean required")
    require(not uses_usp, "uses_usp", "use premium_reserve_parameterised_risk with qualified effective USP sigmas", "UNSUPPORTED_METHOD")
    require(not uses_hres, "uses_hres", "use premium_reserve_parameterised_risk with qualified effective HRES sigmas", "UNSUPPORTED_METHOD")
    future = effective_resource("profile.json", context).get("methods", {}).get(
        "health_reserve_adjustment") == "ADC_2027"
    if future:
        require(reserve_adjustments is not None, "reserve_adjustments",
                "all four qualified reserve factors required", "MISSING_INPUT")
        exact_keys(reserve_adjustments, ("1", "2", "3", "4"), "reserve_adjustments")
        require(isinstance(adjustment_reference, str) and bool(adjustment_reference.strip()),
                "adjustment_reference", "external reserve-factor qualification required", "MISSING_INPUT")
        factors = {key: number(value, f"reserve_adjustments.{key}", 0)
                   for key, value in reserve_adjustments.items()}
        value, details = _premium_reserve_risk(segments, "health", context, factors)
        return value, {**details, "reserve_adjustments": factors,
                       "adjustment_reference": adjustment_reference,
                       "adjustment_status": "EXTERNAL_UNVERIFIED"}
    require(reserve_adjustments is None and adjustment_reference is None, "reserve_adjustments",
            "reserve adjustments require the2027 profile", "UNSUPPORTED_METHOD")
    return _premium_reserve_risk(segments, "health", context)


def _premium_reserve_risk(segments, risk_type, context, reserve_adjustments=None, premium_adjustments=None):
    """Shared aggregation, with regulatory segment sets and factors kept separate."""
    profile = effective_resource("profile.json", context)
    table_id = f"{risk_type}_segments"
    health = risk_type == "health"
    rows = profile["tables"][table_id]["rows"]
    exact_keys(segments, [row[0] for row in rows], "segments")
    amounts, detail = {}, {}
    for key, sigma_premium, sigma_reserve in rows:
        sigma_premium = number(sigma_premium, f"{key}.sigma_premium", 0)
        sigma_reserve = number(sigma_reserve, f"{key}.sigma_reserve", 0)
        if reserve_adjustments is not None:
            sigma_reserve *= reserve_adjustments[key]
        row = segments[key]
        exact_keys(row, ["premium_volume", "reserve_volume", "geographic_diversification"], key)
        vp = number(row["premium_volume"], f"{key}.premium_volume", 0)
        vr = number(row["reserve_volume"], f"{key}.reserve_volume", 0)
        div = number(row["geographic_diversification"], f"{key}.diversification", 0, 1)
        require(div > 0, f"{key}.diversification", "positive factor required, use 1 for an empty segment")
        if key in _forced_geography_segments(profile, "health_nslt" if health else "nonlife"):
            require(div == scalar("geography_default", context), f"{key}.diversification",
                    "annex III forces the no-diversification factor for this segment")
        if premium_adjustments is not None:
            sigma_premium *= premium_adjustments[key]
        elif health:
            sigma_premium *= number(scalar("health_nonprop_adjustment", context), "health_nonprop_adjustment", 0)
        elif key in {"1", "4", "5"}:
            sigma_premium *= scalar("nonprop_adjustment", context)
        p, r = sigma_premium * vp, sigma_reserve * vr
        raw_sigma_volume = math.sqrt(p * p + p * r + r * r)
        scale = scalar("geography_base", context) + scalar("geography_weight", context) * div
        volume = (vp + vr) * scale
        amounts[key] = raw_sigma_volume * scale
        detail[key] = {"sigma": raw_sigma_volume / (vp + vr) if vp + vr else 0,
                       "volume": volume, "sigma_volume": amounts[key]}
    amount, details = quadratic(amounts, profile["matrices"][table_id])
    multiplier = "health_premium_reserve_multiplier" if health else "premium_reserve_multiplier"
    return scalar(multiplier, context) * amount, {
        **details, "segments": detail, "scope": "standard_parameters_and_selected_volumes"}
