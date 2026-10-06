"""Article133/AnnexXI liability claims, not reinsurance or BOF valuation."""
from fractions import Fraction

from .core import Context, calculation, effective_resource, number, require, scalar


def _reference(reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external classification/representative-claims reference required", "MISSING_INPUT")


@calculation("DR:article-133:2", "DR:annex-XI")
def liability_cat_loss(group: str, gross_premium: float, *, qualification_reference: str, context: Context):
    """Group factor times next12month earned gross premium before reinsurance.

    AnnexXI classifications and exclusions are external, including the group4
    exclusions for groups1–3, private households and specified craftsmen.
    """
    _reference(qualification_reference)
    table = effective_resource("profile.json", context)["tables"]["liability_cat_factors"]
    factors = dict(table["rows"])
    require(isinstance(group, str) and group in factors, "group", "AnnexXI group1–5 required")
    premium = number(gross_premium, "gross_premium", 0)
    factor = number(factors[group], "factor", 0)
    return premium * factor, {"group": group, "gross_premium": premium, "factor": factor,
                              "qualification_reference": qualification_reference,
                              "qualification_status": "EXTERNAL_UNVERIFIED",
                              "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}


@calculation("DR:article-133:3:a-c", unit="count")
def liability_cat_claim_count(loss: float, unlimited: bool | None, largest_limit: float | None = None,
                              *, qualification_reference: str, context: Context):
    """Smallest integer STRICTLY above the ratio, or one for unlimited coverage.

    Fraction arithmetic on decimal representations preserves exact boundaries
    such as 115/(1.15*100)=1; ceil would be wrong there. Representative loss
    allocation across those claims and reinsurance response remain external.
    """
    _reference(qualification_reference)
    amount = number(loss, "loss", 0)
    require(unlimited is None or isinstance(unlimited, bool), "unlimited", "explicit boolean required")
    require(unlimited is not None, "unlimited", "coverage status unknown", "REVIEW_REQUIRED")
    multiplier = number(scalar("liability_claim_limit_multiplier", context), "limit_multiplier", 0)
    require(multiplier > 0, "limit_multiplier", "positive divisor required")
    limit = None
    if unlimited:
        require(largest_limit is None, "largest_limit", "omit finite limit for unlimited coverage")
        count = 1
    else:
        limit = number(largest_limit, "largest_limit", 0)
        require(limit > 0, "largest_limit", "positive largest liability limit required", "REVIEW_REQUIRED")
        ratio = Fraction(str(amount)) / (Fraction(str(multiplier)) * Fraction(str(limit)))
        count = ratio.numerator // ratio.denominator + 1
        require(count <= 2**53, "claim_count", "count exceeds exact numeric result precision", "NUMERICAL_ERROR")
    return count, {"loss": amount, "unlimited": unlimited, "largest_limit": limit,
                   "limit_multiplier": multiplier, "rounding_rule": "strictly_greater_integer",
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "claim_count_only_representative_claim_allocation_external"}
