"""Health ADC wrappers and shared2027 arithmetic; qualification/valuation stay external."""
from .core import Context, calculation, effective_resource, number, require, scalar


def _inputs(segment, nominal_net_best_estimate, reference, risk_type, context):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external ADC contract-group and nominal valuation qualification required", "MISSING_INPUT")
    rows = effective_resource("profile.json", context)["tables"][risk_type + "_segments"]["rows"]
    require(isinstance(segment, str) and segment in {row[0] for row in rows},
            "segment", f"explicit {risk_type} annex segment required")
    sigma = number(next(row[2] for row in rows if row[0] == segment), "annex_reserve_sigma", 0)
    nominal = number(nominal_net_best_estimate, "nominal_net_best_estimate", 0)
    key = risk_type + "_adc_stress_multiplier"
    multiplier = number(scalar(key, context), key, 0)
    return nominal, sigma, multiplier, {
        "risk_type": risk_type, "segment": segment, "nominal_net_best_estimate": nominal, "annex_reserve_sigma": sigma,
        "stress_multiplier": multiplier, "qualification_reference": reference,
        "qualification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DR:article-148:4:conditions", "DR:article-148:5", "DR:annex-XIV")
def health_adc_recovery_2027(segment: str, nominal_net_best_estimate: float,
                            attachment_point: float, cover_size: float, *,
                            qualification_reference: str, context: Context):
    """Scenario indemnity for one externally qualified ADC, before cession/prudence.

    Do not add multiple covers automatically or substitute the discounted
    claims volume for the source-defined nominal net best estimate.
    """
    return _recovery(segment, nominal_net_best_estimate, attachment_point, cover_size,
                     qualification_reference, "health", context)


def _recovery(segment, nominal_net_best_estimate, attachment_point, cover_size,
              qualification_reference, risk_type, context):
    """Identical DR117/148 formula, with explicit risk-specific source parameters."""
    nominal, sigma, multiplier, details = _inputs(
        segment, nominal_net_best_estimate, qualification_reference, risk_type, context)
    attachment = number(attachment_point, "attachment_point", 0)
    cover = number(cover_size, "cover_size", 0)
    ceiling = number(nominal * (1 + sigma), "attachment_ceiling", 0)
    # Compare the equivalent ratio to avoid rounding100*1.057 below105.7 at
    # the inclusive boundary. No economic tolerance or rounded currency cap.
    eligible_attachment = attachment == 0 if nominal == 0 else attachment / nominal <= 1 + sigma
    require(eligible_attachment, "attachment_point", "ADC attachment condition not met",
            "UNSUPPORTED_METHOD")
    excess = number(nominal * (1 + multiplier * sigma) - attachment, "scenario_excess")
    require(excess >= 0, "scenario_excess", "modified assumptions imply negative indemnity",
            "REVIEW_REQUIRED")
    return min(excess, cover), {**details, "attachment_point": attachment, "cover_size": cover,
        "attachment_ceiling": ceiling, "scenario_excess": excess,
        "scope": "single_qualified_adc_indemnity_only_not_scr"}


@calculation("DR:article-148:4", "DR:annex-XIV", unit="ratio")
def health_adc_reserve_factor_2027(segment: str, nominal_net_best_estimate: float,
                                  recovery: float, cession_share: float, additional_premium: float, *,
                                  qualification_reference: str, context: Context):
    """Reserve-sigma adjustment; no invented upper cap or automatic eligibility.

    Recovery is the paragraph5 indemnity before applying cession and prudence.
    Additional premium is supplied before its prescribed zero floor. A zero
    denominator needs review, not an implicit no-adjustment factor.
    """
    return _reserve_factor(segment, nominal_net_best_estimate, recovery, cession_share,
                           additional_premium, qualification_reference, "health", context)


def _reserve_factor(segment, nominal_net_best_estimate, recovery, cession_share,
                    additional_premium, qualification_reference, risk_type, context):
    """Shared arithmetic only: no cross-risk parameter or source inheritance."""
    nominal, sigma, multiplier, details = _inputs(
        segment, nominal_net_best_estimate, qualification_reference, risk_type, context)
    indemnity = number(recovery, "recovery", 0)
    cession = number(cession_share, "cession_share", 0, 1)
    supplied_premium = number(additional_premium, "additional_premium")
    premium = max(supplied_premium, 0)
    key = risk_type + "_adc_prudence"
    prudence = number(scalar(key, context), key, 0)
    denominator = number(nominal * multiplier * sigma, "denominator", 0)
    require(denominator > 0, "denominator", "undefined ADC factor for zero denominator", "REVIEW_REQUIRED")
    numerator = number(denominator - indemnity * cession * prudence + premium, "numerator")
    return max(0, numerator / denominator), {**details, "recovery": indemnity, "cession_share": cession,
        "prudence_factor": prudence, "additional_premium_before_floor": supplied_premium,
        "additional_premium": premium, "numerator": numerator, "denominator": denominator,
        "scope": "qualified_adc_reserve_sigma_factor_only_not_scr"}
