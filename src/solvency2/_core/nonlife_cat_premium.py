"""Articles127/135 gross claims: external scope and valuation, not BOF capital."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "external qualification reference required", "MISSING_INPUT")


@calculation("DR:article-127:2")
def nonprop_property_cat_loss(gross_premium: float, diversification: float, *,
                             qualification_reference: str, context: Context):
    """Next12month eligible LOB28 earned gross premiums; AnnexIII DIV supplied.

    Exclude nonproportional obligations relating to LOB9/21. DIV is based on
    earned premiums, not the premium/reserve volume measure. Qualification and
    DIV derivation remain external; the reference is not regulatory approval.
    """
    premium = number(gross_premium, "gross_premium", 0)
    div = number(diversification, "diversification", 0, 1)
    require(div > 0, "diversification", "positive AnnexIII diversification required")
    _reference(qualification_reference, "qualification_reference")
    multiplier = number(scalar("nonprop_property_multiplier", context), "multiplier", 0)
    weight = number(scalar("nonprop_property_div_weight", context), "div_weight", 0)
    base = number(scalar("nonprop_property_base_weight", context), "base_weight", 0)
    factor = multiplier * (weight * div + base)
    return factor * premium, {"gross_premium": premium, "diversification": div,
                              "effective_factor": factor,
                              "qualification_reference": qualification_reference,
                              "qualification_status": "EXTERNAL_UNVERIFIED",
                              "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}


@calculation("DR:article-135", "DR:annex-XII")
def other_nonlife_cat_loss(group_premiums: Mapping, *, classification_reference: str, context: Context):
    """All five AnnexXII groups, next12month earned gross premiums.

    Classify obligations and exclusions externally, including the conditional
    extended-warranty exclusion in group3. Groups1/2 combine before squaring.
    """
    _reference(classification_reference, "classification_reference")
    table = effective_resource("profile.json", context)["tables"]["other_nonlife_cat_factors"]
    factors = {key: number(value, key + ".factor", 0) for key, value in table["rows"]}
    exact_keys(group_premiums, list(factors), "group_premiums")
    premiums = {key: number(group_premiums[key], key + ".premium", 0) for key in factors}
    weighted = {key: number(premiums[key] * factors[key], key + ".weighted", 0) for key in factors}
    joint = math.fsum((weighted["1"], weighted["2"]))
    return math.hypot(joint, weighted["3"], weighted["4"], weighted["5"]), {
        "group_premiums": premiums, "factors": factors, "weighted_premiums": weighted,
        "joint_groups_1_2": joint, "classification_reference": classification_reference,
        "classification_status": "EXTERNAL_UNVERIFIED",
        "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}
