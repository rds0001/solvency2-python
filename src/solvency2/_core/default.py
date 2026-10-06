"""Counterparty capital on externally classified single-name exposures."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _evidence(value, field):
    require(isinstance(value, str) and bool(value.strip()), field, "nonempty external reference required", "MISSING_INPUT")


def _pd_solvency(ratio, context):
    rows = effective_resource("profile.json", context)["tables"]["default_pd_solvency"]["rows"]
    points = [(number(x, "solvency_axis", 0), number(y, "pd", 0, 1)) for x, y in rows]
    require(len(points) >= 2 and all(a[0] > b[0] for a, b in zip(points, points[1:])),
            "default_pd_solvency", "strictly descending solvency axis required")
    if ratio >= points[0][0]:
        return points[0][1]
    if ratio <= points[-1][0]:
        return points[-1][1]
    for upper, lower in zip(points, points[1:]):
        if lower[0] <= ratio <= upper[0]:
            weight = (ratio - lower[0]) / (upper[0] - lower[0])
            return lower[1] * (1 - weight) + upper[1] * weight
    raise AssertionError("validated solvency interval must exist")


@calculation("DR:article-199:2-9", "DR:article-199:12-13", unit="probability")
def default_probability(category: str, *, classification_reference: str,
                         credit_quality_step: str | None = None, solvency_ratio: float | None = None,
                         mcr_compliant: bool | None = None, sfcr_published: bool | None = None,
                         context: Context):
    """Apply an externally qualified Article 199 category; not a rating/classification engine.

    Clearing exceptions in (12)/(13) take precedence in the external category
    decision. A 'rated' call cannot establish that those exceptions are absent.
    """
    tables = effective_resource("profile.json", context)["tables"]
    specials = dict(tables["default_pd_categories"]["rows"])
    require(isinstance(category, str) and category in ("rated", "rated_insurer", "unrated_insurer", *specials)
            and category != "mcr_breach", "category", "supported externally qualified category required",
            "UNSUPPORTED_METHOD")
    _evidence(classification_reference, "classification_reference")
    if category not in ("unrated_insurer", "rated_insurer"):
        require(solvency_ratio is None and mcr_compliant is None and sfcr_published is None,
                "category_inputs", "insurer-branch inputs only valid for insurer categories")
    if category not in ("rated", "rated_insurer"):
        require(credit_quality_step is None, "credit_quality_step", "rating input only valid for rated category")
    details = {"category": category, "classification_reference": classification_reference,
               "classification_status": "EXTERNAL_UNVERIFIED", "scope": "pd_rule_only_not_exposure_qualification"}
    if category in ("rated", "rated_insurer"):
        ratings = dict(tables["default_pd_ratings"]["rows"])
        require(isinstance(credit_quality_step, str) and credit_quality_step in ratings,
                "credit_quality_step", "externally assigned string step 0–6 required")
        value = ratings[credit_quality_step]
        details["credit_quality_step"] = credit_quality_step
    if category in ("unrated_insurer", "rated_insurer"):
        for field, flag in (("mcr_compliant", mcr_compliant), ("sfcr_published", sfcr_published)):
            require(flag is None or isinstance(flag, bool), field, "boolean or None required")
        ratio = number(solvency_ratio, "solvency_ratio") if solvency_ratio is not None else None
        require(sfcr_published is not None, "sfcr_published", "first SFCR publication status required", "REVIEW_REQUIRED")
        if not sfcr_published:
            if category == "rated_insurer":
                branch, effective_ratio = "PRE_SFCR_RATING", None
            else:
                effective_ratio = number(scalar("default_pd_pre_sfcr_ratio", context), "default_pd_pre_sfcr_ratio", 0)
                value, branch = _pd_solvency(effective_ratio, context), "PRE_SFCR"
        else:
            require(mcr_compliant is not None, "mcr_compliant", "MCR compliance status required", "REVIEW_REQUIRED")
            if not mcr_compliant:
                value, branch, effective_ratio = specials["mcr_breach"], "MCR_BREACH", None
            elif category == "rated_insurer":
                branch, effective_ratio = "RATING", None
            else:
                require(ratio is not None, "solvency_ratio", "current solvency ratio required", "MISSING_INPUT")
                value, branch, effective_ratio = _pd_solvency(ratio, context), "SOLVENCY_TABLE", ratio
        details.update(branch=branch, input_solvency_ratio=ratio, effective_solvency_ratio=effective_ratio,
                       mcr_compliant=mcr_compliant, sfcr_published=sfcr_published)
    elif category != "rated":
        value = specials[category]
    return number(value, "pd", 0, 1), details


@calculation("DR:article-199:1", unit="probability")
def default_single_name_pd(exposures: Mapping[str, dict], *, grouping_reference: str, context: Context):
    """LGD-weighted PD for one externally grouped single name, not legal grouping."""
    _evidence(grouping_reference, "grouping_reference")
    require(isinstance(exposures, Mapping), "exposures", "labelled exposure mapping required")
    require(bool(exposures), "exposures", "explicit exposures required", "MISSING_INPUT")
    values = {}
    for label, row in exposures.items():
        require(isinstance(label, str) and bool(label.strip()), "exposures", "nonempty exposure ID required")
        exact_keys(row, ("pd", "lgd"), label)
        values[label] = (number(row["pd"], f"{label}.pd", 0, 1), number(row["lgd"], f"{label}.lgd", 0))
    scale = max(lgd for _, lgd in values.values())
    require(scale > 0, "lgd", "zero aggregate LGD has no defined weighted PD", "REVIEW_REQUIRED")
    denominator = math.fsum(lgd / scale for _, lgd in values.values())
    weights = {label: (lgd / scale) / denominator for label, (_, lgd) in values.items()}
    return math.fsum(values[label][0] * weight for label, weight in weights.items()), {
        "weights": weights, "lgd_scale": scale, "scaled_lgd_sum": denominator,
        "grouping_reference": grouping_reference, "grouping_status": "EXTERNAL_UNVERIFIED",
        "scope": "single_name_weighted_pd_only_not_group_classification"}


def _type1_charge(sigma: float, total_lgd: float, context: Context | None = None) -> tuple[float, str]:
    low = number(scalar("default_boundary_low", context), "default_boundary_low", 0, 1)
    high = number(scalar("default_boundary_high", context), "default_boundary_high", 0, 1)
    low_multiplier = number(scalar("default_multiplier_low", context), "default_multiplier_low", 0)
    high_multiplier = number(scalar("default_multiplier_high", context), "default_multiplier_high", 0)
    require(low <= high, "default_boundaries", "ordered variance thresholds required")
    if sigma <= low * total_lgd:
        return low_multiplier * sigma, "low"
    if sigma <= high * total_lgd:
        return high_multiplier * sigma, "middle"
    return total_lgd, "high"


@calculation("DR:article-200", "DR:article-201")
def default_type1(counterparties: list[dict], *, context: Context,
                  method: str = "standard", proportionality_reference: str | None = None):
    """Type-1 variance and charge; PD/LGD supplied per already grouped single name."""
    require(isinstance(counterparties, list), "counterparties", "list required")
    require(method in ("standard", "simplified_112b"), "method",
            "explicit supported Type1 method required", "UNSUPPORTED_METHOD")
    if method == "simplified_112b":
        _evidence(proportionality_reference, "proportionality_reference")
    else:
        require(proportionality_reference is None, "proportionality_reference",
                "simplification reference is unused by standard method")
    # Resolve calibrated parameters once, not for every covariance pair.
    inter_scale = number(scalar("default_inter_scale", context), "default_inter_scale", 0)
    intra_numerator = number(scalar("default_intra_numerator", context), "default_intra_numerator", 0)
    intra_denominator = number(scalar("default_intra_denominator", context), "default_intra_denominator", 0)
    ids, groups, total_lgd, intra_terms = set(), {}, 0.0, []
    for row in counterparties:
        exact_keys(row, ["id", "pd", "lgd"], "counterparty")
        require(isinstance(row["id"], str) and bool(row["id"]), "id", "nonempty string required")
        require(row["id"] not in ids, "id", "single-name exposures must be consolidated")
        ids.add(row["id"])
        pd, lgd = number(row["pd"], "pd", 0, 1), number(row["lgd"], "lgd", 0)
        require(pd < 1, "pd", "defaulted exposure outside performing-exposure contract")
        groups[pd] = groups.get(pd, 0) + lgd
        total_lgd += lgd
        require(intra_denominator > pd, "default_intra_denominator", "positive intra denominator required")
        intra_terms.append(intra_numerator * pd * (1 - pd) / (intra_denominator - pd) * lgd ** 2)
    inter_terms = []
    for p, lgd_p in groups.items():
        for q, lgd_q in groups.items():
            # DR201(2)a explicitly excludes the zero/zero pair in2027. This
            # also preserves the historical continuous-zero boundary, without
            # masking invalid nonzero denominators after analyst overrides.
            if p == q == 0:
                continue
            denominator = inter_scale * (p + q) - p * q
            require(denominator > 0, "default_inter_scale", "positive nonzero-PD covariance denominator required")
            term = p * (1 - p) * q * (1 - q) / denominator
            inter_terms.append(term * lgd_p * lgd_q)
    inter, intra = math.fsum(inter_terms), math.fsum(intra_terms)
    sigma = math.sqrt(inter + intra)
    if method == "simplified_112b":
        boundary = number(scalar("simplified_default_sigma_limit", context), "sigma_limit", 0, 1)
        multiplier = number(scalar("simplified_default_sigma_multiplier", context), "sigma_multiplier", 0)
        require(sigma <= boundary * total_lgd, "sigma",
                "Article112b standard deviation limit exceeded", "UNSUPPORTED_METHOD")
        return multiplier * sigma, {"inter_variance": inter, "intra_variance": intra,
            "sigma": sigma, "total_lgd": total_lgd, "branch": "simplified_112b",
            "sigma_limit": boundary, "multiplier": multiplier,
            "proportionality_reference": proportionality_reference,
            "qualification_status": "EXTERNAL_UNVERIFIED",
            "classification_pd_lgd_support": "EXTERNAL_INPUT_ONLY", "_sources": ["DR:article-112b"]}
    charge, branch = _type1_charge(sigma, total_lgd, context)
    return charge, {"inter_variance": inter, "intra_variance": intra, "sigma": sigma,
                     "total_lgd": total_lgd, "branch": branch,
                     "classification_pd_lgd_support": "EXTERNAL_INPUT_ONLY"}


@calculation("DR:article-202")
def default_type2_shock(overdue_intermediary_lgd: float, other_lgd: float, *, context: Context):
    """Value-decrease amount; BOF must still be revalued to determine the capital charge."""
    overdue = number(overdue_intermediary_lgd, "overdue_intermediary_lgd", 0)
    other = number(other_lgd, "other_lgd", 0)
    return scalar("default_overdue", context) * overdue + scalar("default_other", context) * other, {
        "scope": "exposure_value_decrease_only", "capital_charge_requires_revaluation": True}


@calculation("DR:article-202")
def default_type2_shock_2027(overdue_intermediary_lgd: float, defaulted_forborne_lgd: float,
                             other_lgd: float, *, qualification_reference: str, context: Context):
    """Three disjoint2027 LGD pools; no implicit zero for defaulted/forborne loans.

    Inputs are qualified externally and the residual pool excludes both special
    pools. The result is the exposure-value shock, not a completed BOF revaluation.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
        "qualification_reference", "complete disjoint LGD pool qualification required", "MISSING_INPUT")
    pools = {"overdue_intermediary": number(overdue_intermediary_lgd, "overdue_intermediary_lgd", 0),
             "defaulted_forborne": number(defaulted_forborne_lgd, "defaulted_forborne_lgd", 0),
             "other": number(other_lgd, "other_lgd", 0)}
    keys = {"overdue_intermediary": "default_overdue", "defaulted_forborne": "default_defaulted_forborne",
            "other": "default_other"}
    factors = {name: number(scalar(key, context), key, 0, 1) for name, key in keys.items()}
    charges = {name: value * factors[name] for name, value in pools.items()}
    return math.fsum(charges.values()), {"pool_shocks": charges, "factors": factors,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "exposure_value_decrease_only", "capital_charge_requires_revaluation": True}


@calculation("DR:article-192:7-8")
def default_ccp_fund_lgd_2027(contribution: float, prefunded: bool, *,
                             qualification_reference: str, context: Context):
    """LGD of an externally qualified CCP default-fund contribution, not CCP eligibility."""
    _evidence(qualification_reference, "qualification_reference")
    require(isinstance(prefunded, bool), "prefunded", "explicit prefunding boolean required")
    contribution = number(contribution, "contribution", 0)
    key = "default_ccp_prefunded" if prefunded else "default_ccp_unfunded"
    factor = number(scalar(key, context), key, 0, 1)
    return contribution * factor, {"factor": factor, "prefunded": prefunded,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "qualified_CCP_fund_LGD_only_not_capital"}


@calculation("DR:article-192:4a")
def default_defaulted_loan_lgd_2027(loan: float, recoverables: float, *,
                                   qualification_reference: str, context: Context):
    """Article192(4a) floor; Loan is the source-defined qualified mortgage value.

    Classification and guideline-compliant recovery valuation are external. This
    does not extend the source-defined scope to arbitrary unsecured loans.
    """
    _evidence(qualification_reference, "qualification_reference")
    loan, recoverables = number(loan, "loan", 0), number(recoverables, "recoverables", 0)
    floor = number(scalar("default_defaulted_loan_floor", context), "default_defaulted_loan_floor", 0, 1)
    raw = loan - recoverables
    return max(raw, floor * loan), {"unfloored_lgd": raw, "floor_amount": floor * loan,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "externally_qualified_article192_4a_LGD_not_universal_loan_rule"}
