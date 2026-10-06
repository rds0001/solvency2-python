"""Concentration components; legal grouping and BOF revaluation stay explicit."""
import math
from collections.abc import Mapping
from fractions import Fraction

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _future_rules(context):
    return effective_resource("profile.json", context).get("methods", {}).get("concentration_rules") == "2027"


@calculation("DR:article-184:2")
def concentration_assets(assets: Mapping[str, dict], *, classification_reference: str, context: Context):
    """Select Assets from externally classified holdings; intragroup needs all five flags.

    Exclusions are not inferred from names. Intragroup category itself asserts
    group membership externally; a failed exclusion condition retains the asset.
    """
    require(isinstance(classification_reference, str) and bool(classification_reference.strip()),
            "classification_reference", "external asset scope/classification reference required", "MISSING_INPUT")
    require(isinstance(assets, Mapping) and bool(assets), "assets", "nonempty labelled asset mapping required", "MISSING_INPUT")
    categories = ("included", "policyholder_risk", "intragroup", "deducted_financial_participation",
                  "counterparty_default", "deferred_tax_asset", "intangible", "captive_pooling")
    if _future_rules(context):
        categories += ("negative_equity",)
    flags = ("eligible_counterparty_type", "fully_consolidated", "common_risk_procedures",
             "eu_resident", "no_transfer_obstacles")
    included, excluded, decisions = {}, {}, {}
    for label, row in assets.items():
        require(isinstance(label, str) and bool(label.strip()), "assets", "nonempty string asset IDs required")
        require(isinstance(row, Mapping), label, "asset row mapping required")
        category = row.get("category")
        require(category in categories, f"{label}.category", "explicit supported asset classification required", "UNSUPPORTED_METHOD")
        conditional = category in ("intragroup", "captive_pooling")
        exact_keys(row, ("value", "category", "conditions") if conditional else ("value", "category"), label)
        value = number(row["value"], f"{label}.value", None if category == "negative_equity" else 0)
        if category == "negative_equity":
            require(value < 0, f"{label}.value", "negative equity exclusion requires a strictly negative value")
        omit = category != "included"
        if conditional:
            selected_flags = flags if category == "intragroup" else (
                "article88_89_satisfied", "intragroup_pooling", "legally_enforceable_offset")
            exact_keys(row["conditions"], selected_flags, f"{label}.conditions")
            for flag in selected_flags:
                if category == "captive_pooling":
                    require(row["conditions"][flag] is not None, f"{label}.{flag}",
                            "pooling qualification unresolved", "REVIEW_REQUIRED")
                require(isinstance(row["conditions"][flag], bool), f"{label}.{flag}", "explicit boolean condition required")
            omit = all(row["conditions"].values())
        (excluded if omit else included)[label] = value
        decisions[label] = {"category": category, "excluded": omit,
                            "conditions": dict(row["conditions"]) if conditional else None}
    return math.fsum(included.values()), {"included": included, "excluded": excluded, "decisions": decisions,
        "classification_reference": classification_reference, "classification_status": "EXTERNAL_UNVERIFIED",
        "scope": "Article184_2_Assets_only_not_single_name_zero_factor_adjustment",
        "_sources": ["DR:article-106:1"] if any(d["category"] == "captive_pooling" for d in decisions.values()) else []}


@calculation("DR:article-184:3")
def concentration_adjusted_exposure(exposures: Mapping[str, dict], *, grouping_reference: str, context: Context):
    """Ei excluding zero-gi counterparties; does not alter Assets or quality weights."""
    _reference(grouping_reference)
    require(isinstance(exposures, Mapping) and bool(exposures), "exposures", "nonempty labelled exposures required", "MISSING_INPUT")
    included, removed = {}, {}
    for label, row in exposures.items():
        require(isinstance(label, str) and bool(label.strip()), "exposures", "nonempty string exposure IDs required")
        exact_keys(row, ("value", "risk_factor"), label)
        value = number(row["value"], f"{label}.value", 0)
        factor = number(row["risk_factor"], f"{label}.risk_factor", 0, 1)
        (removed if factor == 0 else included)[label] = value
    return math.fsum(included.values()), {"included": included, "zero_factor_removed": removed,
        "grouping_reference": grouping_reference, "grouping_status": "EXTERNAL_UNVERIFIED",
        "scope": "Article184_3_Ei_only_Assets_and_quality_unchanged"}


def _qualification(reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external scope/rating/specific-exposure qualification required", "MISSING_INPUT")


def _quality_step(step, allowed=tuple(str(i) for i in range(7))):
    if not isinstance(step, str):
        value = number(step, "credit_quality_step", 0, 6)
        require(value.is_integer(), "credit_quality_step", "integer CQS required; no implicit rounding")
        step = str(int(value))
    require(step in allowed, "credit_quality_step", "explicit allowed CQS required")
    return step


@calculation("DR:article-182:5-11", unit="credit_quality_step")
def concentration_credit_quality(category: str, *, qualification_reference: str,
                                  credit_quality_step: str | float | None = None,
                                  solvency_ratio: float | None = None, mcr_compliant: bool | None = None,
                                  sfcr_published: bool | None = None, context: Context):
    """Position quality before single-name weighting/ceiling; eligibility is external.

    Here the quality itself is interpolated, unlike Article180 stress-factor
    interpolation. MCR/SFCR routing in Article182(6-8) concerns unrated insurers.
    """
    categories = ("rated", "unrated_insurer", "unrated_equivalent_third_country_insurer",
                  "unrated_compliant_credit_financial", "residual")
    if _future_rules(context):
        categories += ("sovereign_domestic_rated", "regional_local", "regional_local_guaranteed")
    require(category in categories, "category", "explicit qualified concentration category required", "UNSUPPORTED_METHOD")
    _qualification(qualification_reference)
    details = {"category": category, "qualification_reference": qualification_reference,
               "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "position_quality_before_weighting_and_ceiling"}
    if category not in ("rated", "sovereign_domestic_rated"):
        require(credit_quality_step is None, "credit_quality_step", "unused in unrated/residual category; omit")
    if category != "unrated_insurer":
        require(solvency_ratio is None and mcr_compliant is None and sfcr_published is None,
                "inputs", "SFCR/MCR/solvency inputs only apply to unrated insurer")
    if category in ("rated", "sovereign_domestic_rated"):
        value = float(_quality_step(credit_quality_step))
        branch = "RATING"
        if category == "sovereign_domestic_rated":
            # Only the externally qualified domestic-currency/funding category
            # invokes Article182(5); ordinary rated positions are unchanged.
            details["unadjusted_quality"] = value
            if value >= 2:
                value -= number(scalar("concentration_sovereign_improvement", context), "quality_improvement", 0, 2)
            branch = "QUALIFIED_SOVEREIGN_2027"
            details["_sources"] = ["DR:article-182:5"]
    elif category in ("regional_local", "regional_local_guaranteed"):
        value = scalar("concentration_regional_quality", context)
        branch = "QUALIFIED_REGIONAL_POSITION_2027"
        details["_sources"] = ["DR:article-182:5a-5b"]
    elif category == "residual":
        value = scalar("concentration_residual_quality", context)
        branch = "EXTERNALLY_QUALIFIED_RESIDUAL"
    elif category != "unrated_insurer":
        value = scalar("concentration_assumed_quality", context)
        branch = "EXTERNALLY_QUALIFIED_ASSUMED_QUALITY"
    else:
        require(isinstance(sfcr_published, bool), "sfcr_published", "explicit first SFCR status required", "REVIEW_REQUIRED")
        if not sfcr_published:
            require(mcr_compliant is None and solvency_ratio is None, "inputs", "unused before first SFCR; omit")
            value = scalar("concentration_assumed_quality", context)
            branch = "PRE_SFCR"
        else:
            require(isinstance(mcr_compliant, bool), "mcr_compliant", "explicit MCR status required", "REVIEW_REQUIRED")
            if not mcr_compliant:
                require(solvency_ratio is None, "solvency_ratio", "unused for MCR breach; omit")
                value = scalar("concentration_mcr_breach_quality", context)
                branch = "MCR_BREACH"
            else:
                ratio = number(solvency_ratio, "solvency_ratio", 0)
                table = effective_resource("profile.json", context)["tables"]["concentration_solvency_quality"]
                rows = [(number(x, "solvency_knot", 0), number(y, "quality_knot", 0, 6)) for x, y in table["rows"]]
                require(len(rows) >= 2 and all(lo[0] < hi[0] for lo, hi in zip(rows, rows[1:])),
                        "table", "strictly increasing solvency knots required")
                if ratio <= rows[0][0]:
                    lower = upper = rows[0]
                elif ratio >= rows[-1][0]:
                    lower = upper = rows[-1]
                else:
                    lower, upper = next((lo, hi) for lo, hi in zip(rows, rows[1:]) if lo[0] <= ratio <= hi[0])
                weight = 0 if lower == upper else (ratio - lower[0]) / (upper[0] - lower[0])
                value = (1 - weight) * lower[1] + weight * upper[1]
                branch = "SOLVENCY_QUALITY_INTERPOLATION"
                details.update(solvency_ratio=ratio, lower_knot=lower, upper_knot=upper, upper_weight=weight,
                               _sources=[table["source"]])
    details.update(branch=branch, sfcr_published=sfcr_published, mcr_compliant=mcr_compliant)
    return number(value, "quality", 0, 6), details


@calculation("DR:article-185", "DR:article-187:1-2", unit="ratio")
def concentration_threshold(category: str, *, qualification_reference: str,
                             credit_quality_step: str | float | None = None, context: Context):
    """CT on externally established single-name quality or qualified special exposure."""
    captive_categories = ("captive_external_credit_institution", "captive_group_cash_manager")
    require(category in ("standard", "covered_bond", "property", *captive_categories),
            "category", "supported threshold category required", "UNSUPPORTED_METHOD")
    _qualification(qualification_reference)
    if category in captive_categories:
        # The reference must qualify DR88/89 and the precise DR106(2) role.
        # This is not the threshold for every exposure held by a captive.
        _quality_step(credit_quality_step, ("2",))
        value, source = scalar("captive_concentration_threshold", context), "DR:article-106:2"
    elif category == "property":
        require(credit_quality_step is None, "credit_quality_step", "unused for property; omit")
        value, source = scalar("concentration_property_threshold", context), "DR:article-187:2"
    elif category == "covered_bond":
        _quality_step(credit_quality_step, ("0", "1"))
        value, source = scalar("concentration_covered_threshold", context), "DR:article-187:1"
    else:
        key = _quality_step(credit_quality_step)
        table = effective_resource("profile.json", context)["tables"]["concentration_threshold"]
        value, source = dict(table["rows"])[key], table["source"]
    return number(value, "threshold", 0, 1), {"category": category, "credit_quality_step": credit_quality_step,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "concentration_threshold_only", "_sources": [source]}


@calculation("DR:article-186:1", "DR:article-187:2-4", unit="ratio")
def concentration_factor(category: str, *, qualification_reference: str,
                          credit_quality_step: str | float | None = None, context: Context):
    """gi selection, not grouping or CT selection; regional CQS2 reference affects gi only."""
    require(category in ("standard", "sovereign", "property", "regional_local", "regional_local_guaranteed"),
            "category", "supported concentration factor category required", "UNSUPPORTED_METHOD")
    _qualification(qualification_reference)
    require(not (_future_rules(context) and category in ("regional_local", "regional_local_guaranteed")),
            "category", "2027 requires position quality, single-name weighting and standard factor; old regional fixed rule deleted",
            "REVIEW_REQUIRED")
    effective_step = credit_quality_step
    if category in ("standard", "sovereign"):
        effective_step = _quality_step(credit_quality_step)
    else:
        require(credit_quality_step is None, "credit_quality_step", "unused in fixed-factor category; omit")
        effective_step = "2" if category != "property" else None
    if category == "property":
        value, source = scalar("concentration_property_factor", context), "DR:article-187:2"
    else:
        key = "concentration_factor" if category == "standard" else "concentration_sovereign_factor"
        table = effective_resource("profile.json", context)["tables"][key]
        value, source = dict(table["rows"])[effective_step], table["source"]
        if category in ("regional_local", "regional_local_guaranteed"):
            source = "DR:article-187:4a" if category == "regional_local" else "DR:article-187:4b"
    return number(value, "risk_factor", 0, 1), {"category": category, "credit_quality_step": credit_quality_step,
        "effective_factor_quality_step": effective_step, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "gi_only_not_CT_or_legal_qualification", "_sources": [source]}


def _reference(value):
    require(isinstance(value, str) and bool(value.strip()), "grouping_reference",
            "external grouping/exposure scope reference required", "MISSING_INPUT")


def _amounts(values, field):
    require(isinstance(values, Mapping) and bool(values), field, "nonempty labelled mapping required", "MISSING_INPUT")
    result = {}
    for label, value in values.items():
        require(isinstance(label, str) and bool(label.strip()), field, "nonempty string IDs required")
        result[label] = number(value, f"{field}.{label}", 0)
    return result


@calculation("DR:article-182:2-3")
def concentration_exposure_sum(exposures: Mapping[str, float], *, grouping_reference: str, context: Context):
    """Sum externally grouped counterparty/single-name exposures, not all Assets."""
    _reference(grouping_reference)
    amounts = _amounts(exposures, "exposures")
    return math.fsum(amounts.values()), {"exposures": amounts, "grouping_reference": grouping_reference,
        "grouping_status": "EXTERNAL_UNVERIFIED", "scope": "externally_grouped_exposure_sum"}


@calculation("DR:article-182:4", unit="credit_quality_step")
def concentration_single_name_quality(exposures: Mapping[str, dict], *, grouping_reference: str, context: Context):
    """Ceil value-weighted quality only after aggregation, without epsilon rounding.

    Exact arithmetic on validated binary inputs protects integer boundaries and
    avoids overflow in weighted products. Input qualities may be fractional.
    """
    _reference(grouping_reference)
    require(isinstance(exposures, Mapping) and bool(exposures), "exposures", "nonempty exposure mapping required", "MISSING_INPUT")
    values = {}
    total, numerator = Fraction(0), Fraction(0)
    for label, row in exposures.items():
        require(isinstance(label, str) and bool(label.strip()), "exposures", "nonempty string IDs required")
        exact_keys(row, ("value", "quality"), label)
        value = number(row["value"], f"{label}.value", 0)
        quality = number(row["quality"], f"{label}.quality", 0, 6)
        total += Fraction(value)
        numerator += Fraction(value) * Fraction(quality)
        values[label] = {"value": value, "quality": quality}
    require(total > 0, "exposures", "positive total value required for weighted quality", "REVIEW_REQUIRED")
    average = numerator / total
    return math.ceil(average), {"exposures": values, "weighted_quality_before_rounding": float(average),
        "grouping_reference": grouping_reference, "grouping_status": "EXTERNAL_UNVERIFIED",
        "scope": "single_name_quality_only", "rounding": "exact_input_weighted_average_ceiling_no_epsilon"}


@calculation("DR:article-184:1")
def concentration_excess(exposure: float, assets: float, threshold: float, *, context: Context):
    """Threshold excess on already scoped Assets and zero-factor-adjusted exposure."""
    exposure = number(exposure, "exposure", 0)
    assets = number(assets, "assets", 0)
    threshold = number(threshold, "threshold", 0, 1)
    limit = threshold * assets
    return max(0, exposure - limit), {"exposure": exposure, "assets": assets, "threshold": threshold,
        "threshold_amount": limit, "scope": "excess_only_external_184_2_3_scope_adjustments_required"}


@calculation("DR:article-183:2")
def concentration_asset_loss(excess: float, risk_factor: float, *, context: Context):
    """Immediate asset-value loss, explicitly NOT the resulting BOF capital charge."""
    excess = number(excess, "excess", 0)
    factor = number(risk_factor, "risk_factor", 0, 1)
    return excess * factor, {"excess": excess, "risk_factor": factor, "scope": "asset_loss_not_BOF_capital"}


@calculation("DR:article-183:1")
def concentration_risk(single_name_charges: Mapping[str, float], *, context: Context):
    """Euclidean norm of already valued single-name BOF charges; not asset losses."""
    charges = _amounts(single_name_charges, "single_name_charges")
    return math.hypot(*charges.values()), {"single_name_charges": charges, "scope": "BOF_charge_aggregation_only"}
