"""Premium-only AnnexIII concentration for Article121–124 other-region CAT."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require


@calculation("DR:annex-III:1:8", unit="ratio")
def natural_cat_other_diversification(peril: str, regional_premiums: Mapping, *,
        qualification_reference: str, context: Context):
    """Return sum of squared premium shares over all explicit regions5..18.

    All amounts must use the externally qualified peril, gross-premium basis,
    period, currency/unit and risk-location classification. These region IDs
    are AnnexIII macroregions, not NatCat risk-zone IDs. No reserve amounts,
    premium/reserve segment exceptions, USP override or implicit default enter
    this CAT-only calculation. Zero total is undefined, not an assumed one.
    """
    articles = {"windstorm": ("121", "9"), "earthquake": ("122", "6"),
                "flood": ("123", "9"), "hail": ("124", "9")}
    require(isinstance(peril, str) and peril in articles, "peril",
            "only four prescribed premium-based other-region perils supported", "UNSUPPORTED_PARAMETER")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "premium scope, period and regional qualification required", "MISSING_INPUT")
    labels = tuple(str(i) for i in range(5, 19))
    exact_keys(regional_premiums, labels, "regional_premiums")
    premiums = {key: number(regional_premiums[key], key + ".premium", 0) for key in labels}
    scale = max(premiums.values())
    require(scale > 0, "regional_premiums", "zero total gives undefined0/0 diversification", "REVIEW_REQUIRED")
    scaled = {key: value / scale for key, value in premiums.items()}
    total = math.fsum(scaled.values())
    shares = {key: value / total for key, value in scaled.items()}
    value = math.fsum(share * share for share in shares.values())
    article, paragraph = articles[peril]
    profile = effective_resource("profile.json", context)
    return value, {"peril": peril, "regional_shares": shares, "regions": list(labels),
                   "qualification_reference": qualification_reference,
                   "qualification_status": "EXTERNAL_UNVERIFIED",
                   "premium_basis_and_period_verified": False, "geography_verified": False,
                   "reserve_volume_used": False, "premium_reserve_exceptions_applied": False,
                   "default_factor_applied": False, "scope": "premium_only_diversification_not_claim_or_scr",
                   "_sources": [f"DR:article-{article}:{paragraph}:a",
                                context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":annex-III"]}
