"""Article193 pool inputs and type-A arithmetic; no legal membership decisions."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, number, require, scalar
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-193:1:e-g", unit="ratio")
def default_pool_member_ratio(category: str, *, classification_reference: str,
                              credit_quality_step: str | None = None,
                              current_solvency_ratio: float | None = None,
                              equivalent: bool | None = None, context: Context):
    """Select the pool SR convention, not the counterparty PD table."""
    require(category in ("rated", "unrated_in_scope", "unrated_third_country"), "category",
            "explicit supported pool member category required", "UNSUPPORTED_METHOD")
    _reference(classification_reference, "classification_reference")
    if category == "rated":
        require(current_solvency_ratio is None and equivalent is None, "inputs", "unused inputs must be omitted")
        rows = effective_resource("profile.json", context)["tables"]["default_pool_member_ratios"]["rows"]
        ratios = dict(rows)
        require(isinstance(credit_quality_step, str) and credit_quality_step in ratios,
                "credit_quality_step", "explicit string CQS0 through6 required")
        ratio = number(ratios[credit_quality_step], "table_ratio", 0)
    elif category == "unrated_in_scope":
        require(credit_quality_step is None and equivalent is None, "inputs", "unused inputs must be omitted")
        ratio = number(current_solvency_ratio, "current_solvency_ratio", 0)
    else:
        require(credit_quality_step is None and current_solvency_ratio is None,
                "inputs", "unused inputs must be omitted")
        known = _known_flag(equivalent, "equivalent")
        ratio = number(scalar("default_pool_equivalent_ratio" if known else
                              "default_pool_nonequivalent_ratio", context), "third_country_ratio", 0)
    return ratio, {"category": category, "credit_quality_step": credit_quality_step,
                   "equivalent": equivalent, "classification_reference": classification_reference,
                   "classification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DR:article-193:1:a-d", "DR:article-193:2", unit="ratio")
def default_pool_solvency_ratio(in_scope_members: Mapping, out_of_scope_members: Mapping, *,
                                membership_reference: str, context: Context):
    """Harmonic EOF-weighted inner group plus risk-share-weighted outer group.

    Membership must include any central intermediary. Zero inner SR requires
    a separately assessed limiting case; it is not silently replaced by zero.
    """
    _reference(membership_reference, "membership_reference")
    require(isinstance(in_scope_members, Mapping) and isinstance(out_of_scope_members, Mapping),
            "members", "two explicit member mappings required")
    require(bool(in_scope_members) or bool(out_of_scope_members), "members", "pool is empty", "MISSING_INPUT")
    require(not set(in_scope_members).intersection(out_of_scope_members), "members", "duplicate member across groups")
    inside, outside = {}, {}
    for members, first, target in ((in_scope_members, "eligible_own_funds", inside),
                                    (out_of_scope_members, "risk_share", outside)):
        for label, row in members.items():
            require(isinstance(label, str) and bool(label.strip()), "members", "nonempty member ID required")
            require(isinstance(row, Mapping) and set(row) == {first, "solvency_ratio"},
                    label, "exact member fields required")
            weight = number(row[first], f"{label}.{first}", 0, 1 if first == "risk_share" else None)
            sr = number(row["solvency_ratio"], f"{label}.solvency_ratio", 0)
            if first == "eligible_own_funds":
                require(sr > 0, label, "zero inner SR needs separate limiting-case assessment", "REVIEW_REQUIRED")
            target[label] = {first: weight, "solvency_ratio": sr}
    p = math.fsum(row["risk_share"] for row in outside.values())
    require(p <= 1, "risk_shares", "outer shares exceed whole pool")
    outer = math.fsum(number(row["risk_share"] * row["solvency_ratio"], "outer_contribution")
                      for row in outside.values())
    inner_ratio = None
    if p < 1:
        require(bool(inside), "in_scope_members", "inner members required for residual pool share", "MISSING_INPUT")
        eof = math.fsum(row["eligible_own_funds"] for row in inside.values())
        denominator = math.fsum(number(row["eligible_own_funds"] / row["solvency_ratio"], "EOF_over_SR")
                                for row in inside.values())
        require(eof > 0 and denominator > 0, "in_scope_members", "positive inner EOF and denominator required",
                "REVIEW_REQUIRED")
        inner_ratio = number(eof / denominator, "inner_solvency_ratio", 0)
    sr = number((1 - p) * inner_ratio + outer if inner_ratio is not None else outer, "pool_solvency_ratio", 0)
    return sr, {"in_scope_members": inside, "out_of_scope_members": outside,
                "out_of_scope_risk_share": p, "inner_solvency_ratio": inner_ratio,
                "outer_contribution": outer, "membership_reference": membership_reference,
                "membership_status": "EXTERNAL_UNVERIFIED", "scope": "supplied_members_only"}


@calculation("DR:article-193:1")
def default_pool_type_a_lgd(base_lgd: float, *, joint_liability: bool | None,
                            qualification_reference: str, pool_solvency_ratio: float | None = None,
                            context: Context):
    """Apply type-A liability rule to an externally qualified Article192 LGD.

    Low SR legitimately gives a risk-share factor above1 in this source;
    there is no invented reduction-only clamp.
    """
    _reference(qualification_reference, "qualification_reference")
    joint = _known_flag(joint_liability, "joint_liability")
    base = number(base_lgd, "base_lgd", 0)
    ratio = cap = decay = None
    factor = 1
    if joint:
        ratio = number(pool_solvency_ratio, "pool_solvency_ratio", 0)
        cap = number(scalar("default_pool_solvency_cap", context), "solvency_cap", 0)
        decay = number(scalar("default_pool_risk_share_decay", context), "risk_share_decay", 0)
        factor = math.exp(-decay * (min(ratio, cap) - 1))
    else:
        require(pool_solvency_ratio is None, "pool_solvency_ratio", "unused for proportional liability; omit")
    return number(base * factor, "pool_type_a_lgd", 0), {
        "base_lgd": base, "joint_liability": joint, "pool_solvency_ratio": ratio,
        "solvency_cap": cap, "risk_share_decay": decay, "risk_share_factor": factor,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED"}
