"""Narrow RSR disclosure screen; no long-term equity qualification or SCR model."""
from fractions import Fraction

from .core import Context, calculation, number, scalar
from .evidence import _declared_bool, _reference


@calculation("DR:article-311:5", unit="indicator")
def rsr_long_term_equity_extra_disclosure_2027(long_term_equity_asset_share: float,
                                              scr_compliant_without_treatment: bool, *,
                                              qualification_reference: str, context: Context):
    """Extra impact/action disclosures for an externally qualified105a holding.

    Share is relative to ALL held assets, not the equity portfolio. The
    counterfactual SCR-compliance fact must already have been established.
    Exactly4% does not trigger the share branch. No general reporting waiver.
    """
    _reference(qualification_reference, "qualification_reference")
    share = number(long_term_equity_asset_share, "long_term_equity_asset_share", 0, 1)
    complies = _declared_bool(scr_compliant_without_treatment, "scr_compliant_without_treatment")
    limit = number(scalar("rsr_long_term_equity_asset_share_limit", context), "share_limit", 0, 1)
    share_trigger = Fraction(str(share)) > Fraction(str(limit))
    return int(share_trigger or not complies), {
        "long_term_equity_asset_share": share, "share_limit": limit,
        "strict_share_trigger": share_trigger,
        "scr_compliant_without_treatment": complies,
        "counterfactual_scr_compliance_trigger": not complies,
        "denominator_scope": "all_held_assets_not_equity_portfolio",
        "ordinary_article311_5_information_still_required": True,
        "hypothetical_scr_calculated": False, "article105a_eligibility_verified": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "additional_RSR_LTE_market_risk_impact_and_breach_action_disclosure_trigger_only",
    }
