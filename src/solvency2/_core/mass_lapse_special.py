"""Declared special life mass-lapse category, not a contract valuation."""
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-142:6:a", unit="indicator")
def life_mass_lapse_special_eligibility(policyholder_type: str, conditions: Mapping, *,
        beneficiary_count: int | None = None, qualification_reference: str, context: Context):
    """Screen declared142(6)a facts; a negative result does NOT select category b.

    Related beneficiaries are excluded independently of count. The20-person
    limit belongs to the separate estate/inheritance-purpose exclusion only.
    Underlying reinsurance scope and worst termination valuation remain external.
    """
    require(isinstance(policyholder_type, str) and policyholder_type in
            ("natural_person", "non_natural_person"), "policyholder_type",
            "explicit supported policyholder type required", "UNSUPPORTED_METHOD")
    _reference(qualification_reference, "qualification_reference")
    natural = policyholder_type == "natural_person"
    keys = ["in_directive_scope", "termination_increases_tp"] + (
        ["acts_for_beneficiaries", "related_to_beneficiaries", "estate_or_inheritance_purpose"]
        if natural else ["beneficiary_consent_required"])
    exact_keys(conditions, keys, "conditions")
    flags = {key: _known_flag(conditions[key], key) for key in keys}
    count = limit = None
    estate_excluded = False
    if natural:
        count = number(beneficiary_count, "beneficiary_count", 1)
        require(count.is_integer(), "beneficiary_count", "positive whole beneficiary count required")
        limit = number(scalar("mass_lapse_beneficiary_limit", context), "beneficiary_limit", 0)
        require(limit.is_integer(), "beneficiary_limit", "whole threshold required", "REVIEW_REQUIRED")
        estate_excluded = flags["estate_or_inheritance_purpose"] and count <= limit
        branch = flags["acts_for_beneficiaries"] and not flags["related_to_beneficiaries"] and not estate_excluded
    else:
        require(beneficiary_count is None, "beneficiary_count", "unused in non-natural branch; omit")
        branch = not flags["beneficiary_consent_required"]
    checks = {"directive_scope": flags["in_directive_scope"],
              "tp_increase_excluding_risk_margin": flags["termination_increases_tp"],
              "policyholder_branch": branch}
    eligible = all(checks.values())
    return int(eligible), {
        "policyholder_type": policyholder_type, "conditions": flags, "checks": checks,
        "failed_checks": [key for key, passed in checks.items() if not passed],
        "beneficiary_count": count, "beneficiary_limit": limit, "estate_exception_applies": estate_excluded,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "standard_category_inferred": False, "capital_charge_computed": False,
        "underlying_reinsurance_scope_verified": False, "worst_termination_valued": False,
        "scope": "declared_special_mass_lapse_eligibility_only"}
