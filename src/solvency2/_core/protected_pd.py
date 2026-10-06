"""Explicit Article199 provider election with overriding clearing PD branches."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .default import default_probability
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-199:10", "DR:article-199:12-13", unit="probability")
def default_protected_probability(original_pd: float, *, substitute_provider: bool | None,
        protection: Mapping | None, clearing_category: str | None,
        qualification_reference: str, context: Context,
        central_government_guarantee: Mapping | None = None):
    """Select a qualified provider PD, never the minimum of two probabilities.

    Full protection and Articles209–215 compliance are externally assessed.
    Clearing precedence is explicit. This does not regroup names under189(5),
    change LGD, or infer sovereign zero-PD eligibility from a provider identity.
    """
    _reference(qualification_reference, "qualification_reference")
    original = number(original_pd, "original_pd", 0, 1)
    elected = _known_flag(substitute_provider, "substitute_provider")
    require(clearing_category is not None, "clearing_category",
            "explicit presence or absence of clearing precedence required", "REVIEW_REQUIRED")
    categories = ("none", "cleared_article192_3", "cleared_article192_3a",
                  "cleared_article192_7", "cleared_article192_8")
    require(isinstance(clearing_category, str) and clearing_category in categories,
            "clearing_category", "explicit supported clearing route required", "UNSUPPORTED_METHOD")
    provider_id, provider_pd = None, None
    selected, branch = original, "ORIGINAL_COUNTERPARTY"
    if elected:
        require(protection is not None, "protection", "elected provider data required", "MISSING_INPUT")
        exact_keys(protection, ("provider_id", "pd", "full_protection", "mitigation_qualified"), "protection")
        _reference(protection["provider_id"], "provider_id")
        provider_id = protection["provider_id"]
        provider_pd = number(protection["pd"], "protection.pd", 0, 1)
        full = _known_flag(protection["full_protection"], "full_protection")
        qualified = _known_flag(protection["mitigation_qualified"], "mitigation_qualified")
        require(full and qualified, "protection", "full qualifying209–215 protection required",
                "REVIEW_REQUIRED")
        selected, branch = provider_pd, "ELECTED_PROVIDER"
    else:
        require(protection is None, "protection", "provider data only accepted with explicit election")
    central_audit = None
    if central_government_guarantee is not None:
        require(elected, "central_government_guarantee", "central-government route requires provider election")
        exact_keys(central_government_guarantee, ("listed_109a_2_a", "unconditional", "irrevocable",
                   "central_government_pd", "classification_reference"), "central_government_guarantee")
        flags = {key: _known_flag(central_government_guarantee[key], key)
                 for key in ("listed_109a_2_a", "unconditional", "irrevocable")}
        require(all(flags.values()), "central_government_guarantee",
                "Article199(11) guarantee conditions not established", "REVIEW_REQUIRED")
        _reference(central_government_guarantee["classification_reference"], "classification_reference")
        selected = number(central_government_guarantee["central_government_pd"], "central_government_pd", 0, 1)
        central_audit = {**central_government_guarantee, "central_government_pd": selected}
        branch = "CENTRAL_GOVERNMENT_EQUIVALENT"
    if clearing_category != "none":
        rows = effective_resource("profile.json", context)["tables"]["default_pd_categories"]["rows"]
        require(clearing_category in dict(rows), "clearing_category",
                "clearing route not available in selected profile", "UNSUPPORTED_RULESET")
        selected = default_probability(clearing_category,
            classification_reference=qualification_reference, context=context).value
        branch = "CLEARING_PRECEDENCE"
    return selected, {
        "original_pd": original, "substitute_provider": elected,
        "provider_id": provider_id, "provider_pd": provider_pd,
        "clearing_category": clearing_category, "branch": branch,
        "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "provider_qualification_verified": False,
        "central_government_equivalence_assessed": central_audit is not None,
        "central_government_guarantee": central_audit,
        "central_government_classification_verified": False,
        "_sources": ["DR:article-199:11"] if central_audit is not None else [],
        "single_name_count_substitution_performed": False,
        "scope": "individual_exposure_pd_selection_only_not_grouping_lgd_or_capital"}
