"""Article170 factor selection from externally qualified duration-method evidence."""
from typing import Mapping

from .contracts import _date, _reference
from .core import effective_resource, exact_keys, number, require


def duration_equity_factor(category, sa, evidence, context):
    """Do not infer approval, ring-fencing, duration, strategic status or asset valuation."""
    require(isinstance(evidence, Mapping), "duration_based", "explicit qualification mapping required")
    table = effective_resource("profile.json", context)["tables"]["equity_duration"]
    cutoff = table["approval_cutoff"]
    fields = ["treatment", "approval_date", "approval_reference", "qualification_reference"]
    if cutoff is not None:
        fields += ["life_insurer", "continuing_approved_scope"]
    exact_keys(evidence, fields, "duration_based")
    for key in ("approval_reference", "qualification_reference"):
        _reference(evidence[key], "duration_based." + key)
    approval = _date(evidence["approval_date"], "duration_based.approval_date")
    require(approval <= _date(context.as_of, "as_of"), "duration_based.approval_date",
            "approval cannot follow the valuation date")
    if cutoff is not None:
        require(approval <= _date(cutoff, "approval_cutoff"), "duration_based.approval_date",
                "approval is outside the implemented grandfathered Article304 scope", "UNSUPPORTED_METHOD")
        for key in ("life_insurer", "continuing_approved_scope"):
            require(type(evidence[key]) is bool, "duration_based." + key, "explicit boolean required")
            require(evidence[key], "duration_based." + key,
                    "implemented continuation requires externally qualified life-insurer and approved-scope evidence",
                    "REVIEW_REQUIRED")
    require(isinstance(category, str) and isinstance(evidence["treatment"], str),
            "duration_based.category_or_treatment", "text labels required")
    rows = {(r[0], r[1]): r[2:] for r in table["rows"]}
    selected = rows.get((category, evidence["treatment"]))
    require(selected is not None, "duration_based.category_or_treatment",
            "unknown Article170 category or treatment; no Article169 long-term alias", "UNSUPPORTED_METHOD")
    base = number(selected[0], "equity_duration.base", 0, 1)
    weight = number(selected[1], "equity_duration.sa_weight", 0, 1)
    value = base + weight * sa
    require(0 <= value <= 1, "equity_duration.factor", "overridden factor requires review", "REVIEW_REQUIRED")
    return value, {"base_shock": base, "sa_weight": weight,
        "duration_based": dict(evidence), "approval_cutoff": cutoff,
        "qualification_status": "EXTERNAL_UNVERIFIED", "eligibility_support": "EXTERNAL_INPUT_ONLY",
        "approval_or_asset_scope_verified": False, "return_to_standard_method_approved": False,
        "scope": "factor_only_not_position_valuation_or_short_position_treatment",
        "_sources": ["DR:article-170:1-4", "DIR:article-304"]}
