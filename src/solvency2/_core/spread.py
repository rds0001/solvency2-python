"""Piecewise document-profile spread shocks, distinct from BOF revaluation."""
import math
from collections.abc import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DR:article-180:4-8", unit="ratio")
def financial_issuer_spread_stress(modified_duration: float, *, category: str, qualification_reference: str,
                                   credit_quality_step: str | None = None, solvency_ratio: float | None = None,
                                   mcr_compliant: bool | None = None, sfcr_published: bool | None = None,
                                   context: Context):
    """Route insurer and externally qualified financial-issuer factors, not legal eligibility.

    After first SFCR, MCR breach takes precedence even over an available rating.
    Before SFCR, compliance and current solvency inputs are not used/accepted.
    """
    insurers = ("rated_insurer", "unrated_insurer")
    specials = ("unrated_equivalent_third_country_insurer", "unrated_compliant_credit_financial")
    require(isinstance(category, str) and category in (*insurers, *specials),
            "category", "explicit qualified financial issuer category required", "UNSUPPORTED_METHOD")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external issuer/rating/applicability evidence required", "MISSING_INPUT")
    duration = number(modified_duration, "modified_duration", 0)
    if category == "rated_insurer":
        require(isinstance(credit_quality_step, str) and credit_quality_step in tuple(str(i) for i in range(7)),
                "credit_quality_step", "explicit string CQS0 through6 required")
    else:
        require(credit_quality_step is None, "credit_quality_step", "unused in unrated category; omit")
    effective_ratio = None
    if category in specials:
        require(sfcr_published is None and mcr_compliant is None and solvency_ratio is None,
                "inputs", "SFCR/MCR/current solvency inputs unused for externally qualified special categories")
        branch = "ASSUMED_SOLVENCY_SPECIAL"
    else:
        require(isinstance(sfcr_published, bool), "sfcr_published", "explicit first SFCR status required", "REVIEW_REQUIRED")
        if not sfcr_published:
            require(mcr_compliant is None and solvency_ratio is None,
                    "inputs", "MCR/current solvency inputs unused before first SFCR")
            branch = "PRE_SFCR_RATING" if category == "rated_insurer" else "PRE_SFCR_ASSUMED_SOLVENCY"
        else:
            require(isinstance(mcr_compliant, bool), "mcr_compliant", "explicit MCR compliance required", "REVIEW_REQUIRED")
            branch = "MCR_BREACH" if not mcr_compliant else "RATING" if category == "rated_insurer" else "CURRENT_SOLVENCY"
            if branch != "CURRENT_SOLVENCY":
                require(solvency_ratio is None, "solvency_ratio", "unused in selected branch; omit")
    if branch == "MCR_BREACH":
        result = specific_exposure_spread_stress(duration, category="insurer_mcr_breach",
            qualification_reference=qualification_reference, context=context)
    elif branch in ("PRE_SFCR_RATING", "RATING"):
        result = bond_spread_stress(duration, category="rated", credit_quality_step=credit_quality_step,
            classification_reference=qualification_reference, context=context)
    else:
        effective_ratio = number(solvency_ratio, "solvency_ratio", 0) if branch == "CURRENT_SOLVENCY" else number(
            scalar("financial_issuer_assumed_solvency_ratio", context), "assumed_solvency_ratio", 0)
        result = insurer_solvency_spread_stress(duration, effective_ratio,
            qualification_reference=qualification_reference, context=context)
    return result.value, {"category": category, "branch": branch, "effective_solvency_ratio": effective_ratio,
        "sfcr_published": sfcr_published, "mcr_compliant": mcr_compliant, "credit_quality_step": credit_quality_step,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "factor_details": result.details, "scope": "financial_issuer_relative_factor_routing_only",
        "_sources": list(result.sources)}


@calculation("DR:article-181:b", unit="annual_rate")
def matching_fundamental_spread_increase(asset_stress: float, modified_duration: float, *, category: str,
                                         qualification_reference: str, credit_quality_step: str | None = None,
                                         context: Context):
    """Fundamental-spread increment, not MA/technical-provision revaluation.

    Use actual modified duration here, not the floor used to determine the
    separately supplied asset shock. The last paragraph overrides CQS3 for
    qualified infrastructure investments and infrastructure corporate assets.
    """
    require(category in ("rated", "unrated", "qualifying_infrastructure"),
            "category", "explicit Article181 category required", "UNSUPPORTED_METHOD")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external MA portfolio/rating/qualification evidence required", "MISSING_INPUT")
    stress = number(asset_stress, "asset_stress", 0, 1)
    duration = number(modified_duration, "modified_duration", 0)
    require(duration > 0, "modified_duration", "strictly positive actual modified duration required")
    if category == "unrated":
        require(credit_quality_step is None, "credit_quality_step", "unused for unrated; omit")
    else:
        require(isinstance(credit_quality_step, str) and credit_quality_step in tuple(str(i) for i in range(7)),
                "credit_quality_step", "explicit string CQS0 through6 required")
    exception = category == "unrated" or category == "qualifying_infrastructure" and credit_quality_step == "3"
    if exception:
        factor = scalar("matching_spread_exception_factor", context)
        source = "DR:article-181:last-paragraph"
    else:
        table = effective_resource("profile.json", context)["tables"]["matching_spread_reduction"]
        factor = dict(table["rows"])[credit_quality_step]
        source = table["source"]
    factor = number(factor, "reduction_factor", 0, 1)
    widening = number(stress / duration, "absolute_spread_widening", 0)
    return widening * factor, {"asset_stress": stress, "modified_duration": duration,
        "absolute_spread_widening": widening, "reduction_factor": factor, "exception_applied": exception,
        "category": category, "credit_quality_step": credit_quality_step,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "fundamental_spread_increment_only_not_MA_or_TP_revaluation", "_sources": [source]}


@calculation("DR:article-180:4", "DR:article-176:2-3", unit="ratio")
def insurer_solvency_spread_stress(modified_duration: float, solvency_ratio: float, *,
                                   qualification_reference: str, context: Context):
    """Interpolate stress, not rating, for externally qualified unrated insurers.

    Duplicate published 75% knots share CQS5_6. MCR/SFCR eligibility is external.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "unrated/MCR/SFCR/current solvency evidence required", "MISSING_INPUT")
    ratio = number(solvency_ratio, "solvency_ratio", 0)
    duration = number(modified_duration, "modified_duration", 0)
    minimum = number(scalar("bond_spread_minimum_duration", context), "minimum_duration", 0)
    effective = max(duration, minimum)
    cap = number(scalar("bond_spread_maximum_stress", context), "maximum_stress", 0, 1)
    tables = effective_resource("profile.json", context)["tables"]
    node_table = tables["insurer_spread_solvency_nodes"]
    nodes = node_table["rows"]
    require(len(nodes) == 5, "nodes", "five distinct solvency knots required")
    previous = None
    for row, group in zip(nodes, ("5_6", "4", "3", "2", "1")):
        knot = number(row[0], "solvency_knot", 0)
        require(previous is None or knot > previous, "nodes", "solvency knots must strictly increase")
        require(row[1] == group, "nodes", "original credit-quality mapping required")
        previous = knot
    if ratio <= nodes[0][0]:
        lower = upper = nodes[0]
    elif ratio >= nodes[-1][0]:
        lower = upper = nodes[-1]
    else:
        lower, upper = next((lo, hi) for lo, hi in zip(nodes, nodes[1:]) if lo[0] <= ratio <= hi[0])
    weight = 0 if lower == upper else (ratio - lower[0]) / (upper[0] - lower[0])
    stress_table = tables["bond_spread_rated"]

    def stress(group):
        rows = [row[1:] for row in stress_table["rows"] if row[0] == group]
        return _duration_band_stress([[*row, row[1] is None] for row in rows], effective, cap)[0]

    low_stress, high_stress = stress(lower[1]), stress(upper[1])
    result = (1 - weight) * low_stress + weight * high_stress
    return result, {"modified_duration": duration, "effective_duration": effective,
                    "solvency_ratio": ratio, "lower_solvency_knot": lower[0], "upper_solvency_knot": upper[0],
                    "lower_credit_quality_group": lower[1], "upper_credit_quality_group": upper[1],
                    "lower_stress": low_stress, "upper_stress": high_stress, "upper_weight": weight,
                    "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                    "scope": "Article180_4_factor_only", "source_note": "duplicate_75_percent_CQS5_6_combined",
                    "_sources": [node_table["source"], stress_table["source"]]}


@calculation("DR:article-180", "DR:article-176:2", unit="ratio")
def specific_exposure_spread_stress(modified_duration: float, *, category: str,
                                    qualification_reference: str, credit_quality_step: str | None = None,
                                    qualification: Mapping | None = None,
                                    context: Context):
    """Article180 table factors on externally qualified debt, not eligibility or BOF SCR.

    Published rounded discontinuities are retained. Insurer MCR breach requires
    external confirmation of the paragraph6 first-SFCR applicability condition.
    """
    rated = {"covered_bond": ("covered", ("0", "1")),
             "sovereign_rated": ("sovereign", tuple(str(i) for i in range(7))),
             "infrastructure_rated": ("infrastructure", ("0", "1", "2", "3")),
             "infrastructure_corporate_rated": ("infrastructure_corporate", ("0", "1", "2", "3"))}
    fixed = {"regional_local": ("sovereign", "2"),
             "regional_local_guaranteed": ("sovereign", "2"),
             "infrastructure_unrated": ("infrastructure", "3"),
             "infrastructure_corporate_unrated": ("infrastructure_corporate", "3"),
             "insurer_mcr_breach": ("insurer_mcr_breach", None)}
    require(isinstance(category, str) and category in (*rated, *fixed),
            "category", "explicit supported Article180 category required", "UNSUPPORTED_METHOD")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external legal/rating/duration qualification required", "MISSING_INPUT")
    if category in rated:
        name, allowed = rated[category]
        require(isinstance(credit_quality_step, str) and credit_quality_step in allowed,
                "credit_quality_step", "explicit category-appropriate string CQS required")
        group = credit_quality_step
        if name == "sovereign":
            group = "0_1" if group in ("0", "1") else "5_6" if group in ("5", "6") else group
    else:
        require(credit_quality_step is None, "credit_quality_step", "unused in this category; omit")
        name, group = fixed[category]
    qualified = None
    qualification_sources = []
    if qualification is not None:
        require(name in {"infrastructure", "infrastructure_corporate"}, "qualification",
                "declared screen is only available for infrastructure debt")
        from ._infrastructure_spread import qualify_infrastructure_spread
        qualified, qualification_sources = qualify_infrastructure_spread(
            qualification, category, credit_quality_step, context)
    duration = number(modified_duration, "modified_duration", 0)
    minimum = number(scalar("bond_spread_minimum_duration", context), "minimum_duration", 0)
    effective = max(duration, minimum)
    cap = number(scalar("bond_spread_maximum_stress", context), "maximum_stress", 0, 1)
    table_id = "specific_spread_" + name
    tables = effective_resource("profile.json", context)["tables"]
    # A qualified API does not imply that every category has an original table.
    # In particular the archived 2027 Article180(1) omits its covered-bond table.
    require(table_id in tables, "category", "original table unavailable for selected profile/category",
            "REVIEW_REQUIRED")
    table = tables[table_id]
    rows = table["rows"] if group is None else [row[1:] for row in table["rows"] if row[0] == group]
    result, details = _duration_band_stress(rows, effective, cap)
    note = None
    if name == "sovereign" and group == "2":
        note = "published_CQS2_intercept_above10_0.084_not_smoothed"
    elif name == "infrastructure_corporate":
        note = "published_rounded_intercepts_not_smoothed"
    return result, {**details, "category": category, "credit_quality_step": credit_quality_step,
                    "credit_quality_group": group, "modified_duration": duration,
                    "effective_duration": effective, "minimum_duration": minimum,
                    "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                    "declared_qualification": qualified,
                    "scope": "relative_position_shock_only", "source_note": note,
                    "table_id": table_id, "_sources": [table["source"], *qualification_sources]}


@calculation("DR:article-175")
def spread_risk(bonds: float, securitisation: float, credit_derivatives: float, *, context: Context):
    """Sum three already valued/selected spread submodules; no missing-component defaults."""
    components = {name: number(value, name, 0) for name, value in
                  (("bonds", bonds), ("securitisation", securitisation), ("credit_derivatives", credit_derivatives))}
    return math.fsum(components.values()), {"components": components, "scope": "spread_submodule_sum_only"}


def _duration_band_stress(rows, duration, cap):
    """Shared ordered-band evaluator; caps are explicit per source formula row."""
    require(bool(rows), "table", "duration bands missing", "UNSUPPORTED_PARAMETER")
    selected = None
    previous_upper = 0
    for i, (lower, upper, intercept, slope, capped) in enumerate(rows):
        lower = number(lower, "band.lower", 0)
        require(previous_upper is not None and lower == previous_upper,
                "table", "bands must be contiguous and ordered")
        if upper is not None:
            upper = number(upper, "band.upper", 0)
            require(upper > lower, "table", "positive band width required")
        require((upper is None) == (i == len(rows) - 1), "table", "last band alone must be unbounded")
        require(isinstance(capped, bool), "band.capped", "explicit formula cap flag required")
        intercept = number(intercept, "band.intercept", 0)
        slope = number(slope, "band.slope", 0)
        if selected is None and (upper is None or duration <= upper):
            selected = (lower, upper, intercept, slope, capped)
        previous_upper = upper
    lower, upper, intercept, slope, capped = selected
    raw = number(intercept + slope * (duration - lower), "uncapped_stress", 0)
    result = min(raw, cap) if capped else raw
    require(result <= 1, "stress", "stress outside [0,1]; check analyst parameters")
    return result, {"band_lower": lower, "band_upper": upper, "intercept": intercept, "slope": slope,
                    "uncapped_stress": raw, "cap_applied_band": capped, "maximum_stress": cap}


@calculation("DR:article-176:5", unit="ratio")
def secured_bond_spread_stress(unsecured_stress: float, asset_value: float, risk_adjusted_collateral: float,
                                *, qualification_reference: str, context: Context):
    """Three collateral branches on an externally qualified Article176(4) shock.

    Full coverage is inclusive; equality to the unsecured post-stress value
    leaves the original shock unchanged. This does not value collateral.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external rating/collateral qualification reference required", "MISSING_INPUT")
    stress = number(unsecured_stress, "unsecured_stress", 0, 1)
    value = number(asset_value, "asset_value", 0)
    require(value > 0, "asset_value", "positive title value required")
    collateral = number(risk_adjusted_collateral, "risk_adjusted_collateral", 0)
    post_stress = value * (1 - stress)
    gap = None
    factor = None
    if collateral >= value:
        branch = "a_full_coverage"
        factor = number(scalar("bond_spread_full_collateral_factor", context), "full_collateral_factor", 0, 1)
        result = stress * factor
    elif post_stress < collateral:
        branch = "b_partial_coverage"
        gap = (value - collateral) / value
        result = (stress + gap) / 2
    else:
        branch = "c_no_reduction"
        result = stress
    return result, {"branch": branch, "unsecured_stress": stress, "asset_value": value,
                    "risk_adjusted_collateral": collateral, "unsecured_post_stress_value": post_stress,
                    "relative_coverage_gap": gap, "full_collateral_factor": factor,
                    "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                    "scope": "unrated_qualified_collateral_shock_only"}


@calculation("DR:article-176:2-4a", unit="ratio")
def bond_spread_stress(modified_duration: float, *, category: str, classification_reference: str,
                        credit_quality_step: str | None = None, context: Context,
                        assigned_eligibility: Mapping | None = None, coinvestment: Mapping | None = None):
    """Use modified duration, floored at1; floats need externally assessed equivalent fixed duration.

    Assigned CQS eligibility and exclusions are external. The published CQS4
    jump above20 years is retained, not interpolated away.
    The 2027 scope explicitly excludes defaulted and forborne loans; callers
    must qualify that scope before supplying a position to this factor API.
    """
    require(category in ("rated", "assigned", "unrated_unsecured", "captive"), "category",
            "explicit supported bond spread category required", "UNSUPPORTED_METHOD")
    require(isinstance(classification_reference, str) and bool(classification_reference.strip()),
            "classification_reference", "external scope/rating/duration reference required", "MISSING_INPUT")
    eligibility = None
    coinvestment_details, coinvestment_sources = None, []
    if coinvestment is not None:
        from .coinvestment_evidence import coinvestment_evidence
        require(category == "assigned" and assigned_eligibility is None, "coinvestment",
                "176c requires assigned category and cannot be combined with176a route")
        coinvestment_details, coinvestment_sources = coinvestment_evidence(coinvestment, credit_quality_step, context)
    if assigned_eligibility is not None:
        from .assigned_credit_eligibility import assigned_credit_eligibility_screen
        require(category == "assigned", "assigned_eligibility", "176a evidence only for assigned category")
        exact_keys(assigned_eligibility, ("issuer_financials", "yield_inputs", "conditions",
                                        "qualification_reference", "assessment"), "assigned_eligibility")
        require(assigned_eligibility["assessment"] is not None, "assigned_eligibility.assessment",
                "explicit176b assessment evidence required for integrated route", "MISSING_INPUT")
        eligibility = assigned_credit_eligibility_screen(**assigned_eligibility,
            target_cqs=credit_quality_step, context=context)
        require(eligibility.value == 1, "assigned_eligibility", "chosen176a route failed", "UNSUPPORTED_METHOD")
    duration = number(modified_duration, "modified_duration", 0)
    minimum = number(scalar("bond_spread_minimum_duration", context), "minimum_duration", 0)
    effective_duration = max(duration, minimum)
    tables = effective_resource("profile.json", context)["tables"]
    group = None
    effective_quality = credit_quality_step
    if category == "captive":
        # DR105 classification includes external DR88/89 qualification.
        # This assumption is for spread only, not concentration quality.
        require(credit_quality_step is None, "credit_quality_step", "unused for captive assumption; omit")
        quality = number(scalar("captive_spread_assumed_quality", context), "assumed_quality", 0, 6)
        require(quality.is_integer(), "assumed_quality", "integer quality step required")
        effective_quality = str(int(quality))
    if category == "unrated_unsecured":
        require(credit_quality_step is None, "credit_quality_step", "unused for unrated_unsecured; omit")
        table = tables["bond_spread_unrated"]
        rows = table["rows"]
    else:
        require(isinstance(effective_quality, str) and effective_quality in ("0", "1", "2", "3", "4", "5", "6"),
                "credit_quality_step", "explicit string CQS0 through6 required")
        group = "5_6" if effective_quality in ("5", "6") else effective_quality
        table = tables["bond_spread_rated"]
        rows = [row[1:] for row in table["rows"] if row[0] == group]
    cap = number(scalar("bond_spread_maximum_stress", context), "maximum_stress", 0, 1)
    result, band = _duration_band_stress([[*row, row[1] is None] for row in rows], effective_duration, cap)
    return result, {"modified_duration": duration, "effective_duration": effective_duration,
                    "coinvestment": coinvestment_details if coinvestment_details is not None else {"status": "NOT_ASSESSED"},
                    "assigned_eligibility": ({"value": eligibility.value, "details": eligibility.details}
                                             if eligibility is not None else {"status": "NOT_ASSESSED"}),
                    "minimum_duration": minimum, "category": category, "credit_quality_step": credit_quality_step,
                    "credit_quality_group": group, **band,
                    "classification_reference": classification_reference, "classification_status": "EXTERNAL_UNVERIFIED",
                    "source_note": "CQS4_above20_published_intercept_0.466_not_smoothed" if group == "4" else None,
                    "scope": "relative_asset_shock_only", "effective_credit_quality_step": effective_quality,
                    "_sources": [table["source"], *(["DR:article-105"] if category == "captive" else []),
                                 *(eligibility.sources if eligibility is not None else []), *coinvestment_sources]}


def _securitisation_increase(value, details, increase_fraction, decision_reference, context):
    """Apply a declared257 sanction, not infer or impose a supervisory decision.

    Increased BY250% means3.5 times the178 factor. Article257 provides no new
    one-unit cap on the sanction. Further-breach escalation remains qualified
    in the imposed increase, not a fabricated fixed staircase.
    """
    if increase_fraction is None:
        require(decision_reference is None, "supervisory_decision_reference", "unused reference without imposed increase")
        return value, {**details, "article257_increase": {"status": "NOT_ASSESSED"}}
    require(isinstance(decision_reference, str) and bool(decision_reference.strip()),
            "supervisory_decision_reference", "qualified imposed Article257 decision required", "MISSING_INPUT")
    increase = number(increase_fraction, "imposed_increase_fraction", 0)
    minimum = number(scalar("securitisation_noncompliance_min_increase", context), "minimum_increase", 0)
    require(increase >= minimum, "imposed_increase_fraction", "increase below Article257 minimum", "UNSUPPORTED_METHOD")
    adjusted = number(value * (1 + increase), "increased_factor", 0)
    return adjusted, {**details, "article257_increase": {
        "status": "EXTERNAL_DECISION_UNVERIFIED", "ordinary_factor": value,
        "increase_fraction": increase, "minimum_increase_fraction": minimum,
        "supervisory_decision_reference": decision_reference,
        "further_breach_escalation_qualified_externally": True,
        "additional_cap_applied": False},
        "scope": "article257_increased_risk_factor_not_asset_value_or_total_SCR",
        "_sources": [*details.get("_sources", []), "DR:article-257:2-4"]}


@calculation("DR:article-178", unit="ratio")
def securitisation_spread_stress(modified_duration: float, *, category: str, qualification_reference: str,
                                  credit_quality_step: str | None = None,
                                  transition: Mapping | None = None, context: Context,
                                  imposed_increase_fraction: float | None = None,
                                  supervisory_decision_reference: str | None = None):
    """Article178 factors on externally qualified positions; no automatic transition relief.

    Paragraph6 literally uses the paragraph3 senior table at CQS5. The unusual
    source reference remains explicit, not silently redirected to paragraph4.
    """
    profile = effective_resource("profile.json", context)
    future = profile.get("methods", {}).get("securitisation_rules") == "2027"
    if category in ("legacy_type1_178a_3", "legacy_type1_178a_4"):
        from ._securitisation_legacy import historical_type1_factor
        value, details = historical_type1_factor(modified_duration, category, credit_quality_step, transition,
                                                qualification_reference, profile, context)
        return _securitisation_increase(value, details, imposed_increase_fraction, supervisory_decision_reference, context)
    require(not (future and category == "other_rated"), "category",
            "2027 other rated securitisations require explicit senior/non-senior classification", "REVIEW_REQUIRED")
    legacy = category == "legacy_type1_178a_1"
    transition_audit = None
    if legacy:
        from .zero_factors import _qualified_conditions
        transition_audit = _qualified_conditions(transition, ("issued_before_2019",
            "qualified_under_2018_article177_2", "no_new_or_replaced_underlying_after_2018"),
            qualification_reference)
    else:
        require(transition is None, "transition", "only the explicit legacy_type1_178a_1 route accepts transition facts")
    rated = ("sts_senior_rated", "sts_non_senior_rated", "resecuritisation_rated", "legacy_type1_178a_1") + (
        ("other_senior_rated", "other_non_senior_rated") if future else ("other_rated",))
    require(category in (*rated, "sts_senior_unrated", "sts_non_senior_unrated", "residual"),
            "category", "explicit supported securitisation category required", "UNSUPPORTED_METHOD")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external STS/seniority/rating assessment required", "MISSING_INPUT")
    duration = number(modified_duration, "modified_duration", 0)
    minimum = number(scalar("securitisation_minimum_duration", context), "minimum_duration", 0)
    effective = max(duration, minimum)
    cap = number(scalar("securitisation_maximum_stress", context), "maximum_stress", 0, 1)
    if category in rated:
        require(isinstance(credit_quality_step, str) and credit_quality_step in ("0", "1", "2", "3", "4", "5", "6"),
                "credit_quality_step", "explicit string CQS0 through6 required")
        if legacy:
            require(credit_quality_step in dict(profile["tables"]["securitisation_legacy_2018"]["rows"]),
                    "credit_quality_step", "declared historical177(2) type1 status contradicts CQS worse than3",
                    "REVIEW_REQUIRED")
    else:
        require(credit_quality_step is None, "credit_quality_step", "unused in unrated/residual category; omit")
    tables = effective_resource("profile.json", context)["tables"]
    group = None
    note = None
    if category == "residual":
        value = number(scalar("securitisation_residual_stress", context), "residual_stress", 0, 1)
        details = {"source_paragraph": "9"}
    else:
        if category in ("sts_senior_rated", "sts_non_senior_rated", "sts_non_senior_unrated", "legacy_type1_178a_1"):
            table_id = "securitisation_sts_non_senior" if category == "sts_non_senior_rated" else "securitisation_sts_senior"
            group = "5_6" if credit_quality_step in ("5", "6") or category == "sts_non_senior_unrated" else credit_quality_step
            if category == "sts_non_senior_unrated":
                note = "Article178_6_literal_reference_to_paragraph3_CQS5_unresolved_legal_review"
            rows = [row[1:] for row in tables[table_id]["rows"] if row[0] == group]
        elif category == "sts_senior_unrated":
            table_id = "securitisation_sts_senior_unrated"
            rows = tables[table_id]["rows"]
        else:
            table_id = {"resecuritisation_rated": "securitisation_resecuritisation",
                        "other_rated": "securitisation_other_rated",
                        "other_senior_rated": "securitisation_other_senior_rated",
                        "other_non_senior_rated": "securitisation_other_non_senior_rated"}[category]
            slopes = dict(tables[table_id]["rows"])
            rows = [[0, None, 0, slopes[credit_quality_step], True]]
        value, details = _duration_band_stress(rows, effective, cap)
        details.update({"table_id": table_id, "_sources": [tables[table_id]["source"]]})
    if legacy:
        details["_sources"].extend(["DR:article-178a:1", "DR:article-178a:2", "DR2018:article-177:2:a"])
    result_details = {**details, "modified_duration": duration, "effective_duration": effective,
                   "minimum_duration": minimum, "category": category, "credit_quality_step": credit_quality_step,
                   "credit_quality_group": group, "source_note": note,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "transition": transition_audit, "historical_classification_verified": False,
                   "scope": ("relative_position_shock_declared_178a_1_2_only" if legacy
                             else "relative_position_shock_only_not_transition_qualification")}
    return _securitisation_increase(value, result_details, imposed_increase_fraction, supervisory_decision_reference, context)
