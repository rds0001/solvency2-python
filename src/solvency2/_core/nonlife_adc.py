"""2027 nonlife ADC components, separately sourced from health despite shared arithmetic."""
from .core import Context, calculation
from .health_adc import _recovery, _reserve_factor


@calculation("DR:article-117:4:conditions", "DR:article-117:5", "DR:annex-II")
def nonlife_adc_recovery_2027(segment: str, nominal_net_best_estimate: float,
                             attachment_point: float, cover_size: float, *,
                             qualification_reference: str, context: Context):
    """One qualified ADC indemnity, before cession/prudence, using AnnexII sigma.

    Contract group, distinct tranche and source-defined nominal net valuation
    remain externally qualified. This is not discounted claims capital or an
    automatic aggregation of several overlapping covers.
    """
    return _recovery(segment, nominal_net_best_estimate, attachment_point, cover_size,
                     qualification_reference, "nonlife", context)


@calculation("DR:article-117:4", "DR:annex-II", unit="ratio")
def nonlife_adc_reserve_factor_2027(segment: str, nominal_net_best_estimate: float,
                                   recovery: float, cession_share: float, additional_premium: float, *,
                                   qualification_reference: str, context: Context):
    """Qualified reserve-sigma factor, no upper cap; zero denominator needs review.

    Recovery is before cession; supplied additional premium is floored at zero
    exactly once. No eligibility approval is inferred from the reference string.
    """
    return _reserve_factor(segment, nominal_net_best_estimate, recovery, cession_share,
                           additional_premium, qualification_reference, "nonlife", context)
