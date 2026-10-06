"""Article192 LGD arithmetic on explicitly qualified external valuations."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


def _known_flag(value, field):
    require(value is None or isinstance(value, bool), field, "boolean or None required")
    require(value is not None, field, "external assessment unresolved", "REVIEW_REQUIRED")
    return value


@calculation("DR:article-197:1-4")
def default_risk_adjusted_collateral(market_value: float, market_adjustment: float | None, *,
        collateral_type: str, conditions: Mapping[str, bool | None], qualification_reference: str,
        context: Context, method: str = "standard", proportionality_reference: str | None = None,
        custodian_assessment: Mapping | None = None):
    """Literal collateral branches, with signed results and explicit legal evidence.

    Article197(3) says neither condition is met. Mixed failure is therefore
    not silently treated as zero. A negative result remains visible; downstream
    LGD APIs explicitly reject collateral outside their nonnegative contract.
    Article112 is an explicit alternative on market value, not an additional
    haircut after a market adjustment. Article88 qualification stays external.
    Optional Article214(2) assessment checks the deposit institution's CQS;
    its legal applicability and all other Article214 conditions stay external.
    Omission preserves the qualified-input API, not a numeric eligibility check.
    """
    _reference(qualification_reference, "qualification_reference")
    require(collateral_type in ("pledge", "title_transfer"), "collateral_type", "explicit collateral type required",
            "UNSUPPORTED_METHOD")
    fields = ("counterparty_requirement", "third_party_requirement", "article214_compliant") if collateral_type == "pledge" else (
        "article214_compliant",)
    exact_keys(conditions, fields, "conditions")
    flags = {key: _known_flag(conditions[key], f"conditions.{key}") for key in fields}
    custodian = {"status": "NOT_ASSESSED", "applies": None, "credit_quality_step": None}
    if custodian_assessment is not None:
        exact_keys(custodian_assessment, ("applies", "credit_quality_step"), "custodian_assessment")
        applies = _known_flag(custodian_assessment["applies"], "custodian_assessment.applies")
        cqs = custodian_assessment["credit_quality_step"]
        maximum = number(scalar("collateral_custodian_max_cqs", context), "collateral_custodian_max_cqs", 0, 6)
        require(maximum == int(maximum), "collateral_custodian_max_cqs", "integer CQS required")
        if applies:
            cqs = number(cqs, "custodian_assessment.credit_quality_step", 0, 6)
            require(cqs == int(cqs), "custodian_assessment.credit_quality_step", "integer CQS required")
            require(cqs <= maximum, "custodian_assessment.credit_quality_step",
                    "Article214(2)(b) deposit institution requirement not met", "REVIEW_REQUIRED")
        else:
            require(cqs is None, "custodian_assessment.credit_quality_step", "omit CQS when Article214(2) does not apply")
        custodian = {"status": "NUMERIC_CHECK_ONLY" if applies else "DECLARED_NOT_APPLICABLE",
                     "applies": applies, "credit_quality_step": cqs, "maximum_cqs": maximum,
                     "qualification_status": "EXTERNAL_UNVERIFIED"}
    value = number(market_value, "market_value", 0)
    require(method in ("standard", "simplified_112"), "method",
            "explicit supported collateral valuation method required", "UNSUPPORTED_METHOD")
    if method == "simplified_112":
        _reference(proportionality_reference, "proportionality_reference")
        require(collateral_type == "pledge", "collateral_type",
                "Article112 concerns pledged collateral only", "UNSUPPORTED_METHOD")
        require(market_adjustment is None, "market_adjustment",
                "omit adjustment for Article112; percentages apply directly to market value")
        require(flags["counterparty_requirement"], "conditions.counterparty_requirement",
                "Article112 counterparty requirement not met", "UNSUPPORTED_METHOD")
        third = flags["third_party_requirement"]
        # Paragraph1 does not repeat paragraph2's explicit Article214 gate.
        # A downstream Article176(5) application must still qualify Article214.
        require(third or flags["article214_compliant"], "conditions.article214_compliant",
                "Article112(2) requires Article214", "UNSUPPORTED_METHOD")
        parameter = "simplified_collateral_full_factor" if third else "simplified_collateral_third_party_failed_factor"
        factor = number(scalar(parameter, context), parameter, 0, 1)
        source = "DR:article-112:1" if third else "DR:article-112:2"
        return value * factor, {"market_value": value, "market_adjustment": None,
            "method": method, "factor": factor, "collateral_type": collateral_type,
            "conditions": flags, "custodian_assessment": custodian, "qualification_reference": qualification_reference,
            "proportionality_reference": proportionality_reference,
            "qualification_status": "EXTERNAL_UNVERIFIED",
            "scope": "article112_value_only_no_implicit_downstream_eligibility",
            "_sources": [source] + (["DR:article-214:2:b"] if custodian_assessment is not None else [])}
    require(proportionality_reference is None, "proportionality_reference",
            "Article112 reference is unused by the standard method")
    adjustment = number(market_adjustment, "market_adjustment")
    difference = number(value - adjustment, "value_minus_adjustment")
    if collateral_type == "title_transfer":
        require(flags["article214_compliant"], "conditions", "title-transfer recognition not established", "REVIEW_REQUIRED")
        factor, branch, source = 1, "TITLE_TRANSFER", "DR:article-197:4"
    elif not flags["counterparty_requirement"] and not flags["article214_compliant"]:
        factor, branch, source = 0, "NEITHER_REQUIREMENT_MET", "DR:article-197:3"
    else:
        require(flags["counterparty_requirement"] and flags["article214_compliant"], "conditions",
                "mixed failure not resolved by literal neither-nor clause; separate assessment required", "REVIEW_REQUIRED")
        if flags["third_party_requirement"]:
            factor, branch, source = 1, "PLEDGE_ALL_REQUIREMENTS", "DR:article-197:1"
        else:
            factor = number(scalar("default_collateral_third_party_haircut", context), "third_party_haircut", 0, 1)
            branch, source = "PLEDGE_THIRD_PARTY_FAILED", "DR:article-197:2"
    return factor * difference, {"market_value": value, "market_adjustment": adjustment,
        "value_minus_adjustment": difference, "factor": factor, "branch": branch,
        "collateral_type": collateral_type, "conditions": flags,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "custodian_assessment": custodian,
        "scope": "signed_risk_adjusted_value_only_no_implicit_LGD_eligibility",
        "_sources": [source] + (["DR:article-214:2:b"] if custodian_assessment is not None else [])}


@calculation("DR:article-198:1-2")
def default_risk_adjusted_mortgage(property_value: float, market_adjustment: float, *,
        valuation_reference: str, context: Context):
    """Subtract adjustment from externally assessed Article198(2) property value.

    Monitoring, prior claims and the independent valuation's market-value cap
    must already be reflected in property_value; no appraisal is invented here.
    """
    _reference(valuation_reference, "valuation_reference")
    value = number(property_value, "property_value", 0)
    adjustment = number(market_adjustment, "market_adjustment")
    return value - adjustment, {"property_value": value, "market_adjustment": adjustment,
        "valuation_reference": valuation_reference, "valuation_status": "EXTERNAL_UNVERIFIED",
        "scope": "signed_mortgage_value_after_external_198_2_assessment_no_zero_floor"}


@calculation("DR:article-192:5-6")
def default_other_lgd(recognised_value: float, *, exposure_type: str, classification_reference: str,
                       nominal_value: float | None = None, context: Context):
    """Two externally classified nonnegative valuation conventions; no hidden offsetting."""
    require(exposure_type in ("commitment", "deposit_or_receivable"), "exposure_type",
            "supported Article192(5)/(6) exposure type required", "UNSUPPORTED_METHOD")
    _reference(classification_reference, "classification_reference")
    value = number(recognised_value, "recognised_value", 0)
    if exposure_type == "commitment":
        nominal = number(nominal_value, "nominal_value", 0)
        lgd = nominal - value
        require(lgd >= 0, "lgd", "negative nominal-minus-value requires separate assessment", "REVIEW_REQUIRED")
    else:
        require(nominal_value is None, "nominal_value", "not used for deposits/receivables; omit rather than net")
        nominal, lgd = None, value
    return lgd, {"exposure_type": exposure_type, "recognised_value": value, "nominal_value": nominal,
                  "classification_reference": classification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                  "scope": "article_192_5_6_formula_only"}


@calculation("DR:article-192:1")
def default_single_name_lgd(exposure_lgds: Mapping[str, float], *, grouping_reference: str, context: Context):
    """Sum already assessed LGDs; qualified netting sets must not be counted twice."""
    _reference(grouping_reference, "grouping_reference")
    require(isinstance(exposure_lgds, Mapping), "exposure_lgds", "labelled LGD mapping required")
    require(bool(exposure_lgds), "exposure_lgds", "explicit exposure or zero row required", "MISSING_INPUT")
    values = {}
    for label, value in exposure_lgds.items():
        require(isinstance(label, str) and bool(label.strip()), "exposure_lgds", "nonempty exposure ID required")
        values[label] = number(value, f"{label}.lgd", 0)
    return math.fsum(values.values()), {"exposure_lgds": values, "grouping_reference": grouping_reference,
                                       "grouping_status": "EXTERNAL_UNVERIFIED",
                                       "scope": "single_name_sum_only_not_grouping_or_netting"}


def _factor(factor_type, ignored, context):
    ignored = _known_flag(ignored, "collateral_ignored_in_estate_share")
    rows = effective_resource("profile.json", context)["tables"]["default_collateral_factors"]["rows"]
    factors = {row[0]: row[1:] for row in rows}
    require(isinstance(factor_type, str) and factor_type in factors,
            "factor_type", "F, F_prime, F_double_prime or F_triple_prime required")
    return number(factors[factor_type][1 if ignored else 0], "collateral_factor", 0, 1)


@calculation("DR:article-194", "DR:article-195", "DR:article-197:7")
def default_pool_lgd(best_estimate: float, risk_mitigation_contribution: float,
                     risk_adjusted_collateral: float, *, variant: str,
                     encumbered_asset_fraction: float, collateral_ignored_in_estate_share: bool | None,
                     qualification_reference: str, undertaking_share: float | None = None,
                     counterparty_share: float | None = None, context: Context):
    """Externally qualified type B/C pool formula, not pool classification.

    B uses already net BEC/BEU; C uses the whole pool's BECE. The recovery
    threshold is inclusive, unlike Article192(2). DeltaRM is not halved.
    """
    require(variant in ("B_joint", "B_proportional", "C"), "variant",
            "explicit B_joint, B_proportional or C required", "UNSUPPORTED_METHOD")
    _reference(qualification_reference, "qualification_reference")
    be = number(best_estimate, "best_estimate")
    rm = number(risk_mitigation_contribution, "risk_mitigation_contribution")
    collateral = number(risk_adjusted_collateral, "risk_adjusted_collateral", 0)
    fraction = number(encumbered_asset_fraction, "encumbered_asset_fraction", 0, 1)
    pu = pc = None
    if variant in ("B_joint", "C"):
        pu = number(undertaking_share, "undertaking_share", 0, 1)
    else:
        require(undertaking_share is None, "undertaking_share", "not used by B_proportional; omit")
    if variant in ("B_joint", "B_proportional"):
        pc = number(counterparty_share, "counterparty_share", 0, 1)
    else:
        require(counterparty_share is None, "counterparty_share", "not used by C; omit")
    if variant == "B_joint":
        require(pc < 1, "counterparty_share", "joint formula requires a positive 1-PC denominator")
        require(pu + pc <= 1, "shares", "undertaking and counterparty shares must not exceed total pool risk")
        weight, basis = pu / (1 - pc), "BEC_net_of_external_reinsurance"
    elif variant == "B_proportional":
        weight, basis = pc, "BEU_net_of_external_reinsurance"
    else:
        weight, basis = pu, "BECE_whole_pool_to_external_counterparty"
    threshold = number(scalar("default_pool_encumbrance_threshold", context), "pool_threshold", 0, 1)
    high = fraction >= threshold
    recovery = number(scalar("default_pool_recovery_encumbered" if high else
                             "default_pool_recovery_standard", context), "recovery_rate", 0, 1)
    factor = _factor("F", collateral_ignored_in_estate_share, context)
    exposure = number(weight * be, "weighted_best_estimate")
    gross = number((1 - recovery) * number(exposure + rm, "exposure_plus_rm"), "gross_lgd")
    raw = number(gross - factor * collateral, "unfloored_lgd")
    return max(raw, 0), {"variant": variant, "best_estimate_basis": basis, "best_estimate": be,
                         "risk_mitigation_contribution": rm, "risk_adjusted_collateral": collateral,
                         "undertaking_share": pu, "counterparty_share": pc, "exposure_weight": weight,
                         "weighted_best_estimate": exposure, "encumbered_asset_fraction": fraction,
                         "encumbrance_threshold": threshold, "threshold_inclusive": True,
                         "recovery_rate": recovery, "collateral_factor": factor, "unfloored_lgd": raw,
                         "qualification_reference": qualification_reference,
                         "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "pool_B_C_formula_only"}


def _lgd(exposure, rm, collateral, variant, ignored, context):
    exposure = number(exposure, "exposure")
    rm = number(rm, "risk_mitigation", 0)
    collateral = number(collateral, "collateral", 0)
    rows = effective_resource("profile.json", context)["tables"]["default_lgd_coefficients"]["rows"]
    a, b, c, factor_type = next(row[1:] for row in rows if row[0] == variant)
    a, b, c = (number(value, key, 0, 1) for key, value in
               (("exposure_weight", a), ("rm_weight", b), ("collateral_weight", c)))
    factor = _factor(factor_type, ignored, context)
    gross = number(a * (exposure + b * rm), "gross_lgd_component")
    reduction = number(c * factor * collateral, "collateral_component")
    raw = number(gross - reduction, "unfloored_lgd")
    return max(raw, 0), {"variant": variant, "exposure": exposure, "risk_mitigation": rm,
                        "collateral": collateral, "exposure_weight": a, "rm_weight": b,
                        "collateral_weight": c, "factor_type": factor_type, "collateral_factor": factor,
                        "gross_lgd_component": gross, "collateral_component": reduction, "unfloored_lgd": raw,
                        "collateral_ignored_in_estate_share": ignored,
                        "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "lgd_formula_only"}


@calculation("DR:article-196")
def default_risk_mitigation(scr_without: float, scr_with: float, *, valuation_reference: str, context: Context):
    """Difference for the same relevant risk module; never substitute overall SCR."""
    without = number(scr_without, "scr_without", 0)
    with_agreement = number(scr_with, "scr_with", 0)
    _reference(valuation_reference, "valuation_reference")
    difference = without - with_agreement
    return max(difference, 0), {"unfloored_difference": difference, "scr_without": without,
                               "scr_with": with_agreement, "valuation_reference": valuation_reference,
                               "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "same_risk_module_difference_only"}


@calculation("DR:article-197:5-6", "DR:article-198:3-4")
def default_collateral_market_adjustment(scr_without: float, scr_with: float, *,
                                         valuation_reference: str, context: Context):
    """Literal document-profile order; signed adjustment, not collateral eligibility.

    External valuations must assess FX against exposure/loan currency. Do not
    silently reverse this source's subtraction or apply the Article196 floor.
    """
    _reference(valuation_reference, "valuation_reference")
    without = number(scr_without, "scr_without", 0)
    with_asset = number(scr_with, "scr_with", 0)
    return without - with_asset, {"scr_without": without, "scr_with": with_asset,
                                  "subtraction_order": "without_minus_with",
                                  "valuation_reference": valuation_reference,
                                  "valuation_status": "EXTERNAL_UNVERIFIED",
                                  "scope": "literal_document_profile_market_adjustment_only",
                                  "open_review": "source_sign_and_application_not_legally_validated"}


@calculation("DR:article-197:7", unit="ratio")
def default_collateral_factor(factor_type: str, *, collateral_ignored_in_estate_share: bool | None,
                               legal_reference: str, context: Context):
    """Select a coefficient, not an insolvency-law interpretation or collateral valuation."""
    _reference(legal_reference, "legal_reference")
    value = _factor(factor_type, collateral_ignored_in_estate_share, context)
    return value, {"factor_type": factor_type, "collateral_ignored_in_estate_share": collateral_ignored_in_estate_share,
                   "legal_reference": legal_reference, "legal_assessment_status": "EXTERNAL_UNVERIFIED"}


@calculation("DR:article-192:2", "DR:article-197:7")
def default_reinsurance_lgd(recoverables: float, risk_mitigation: float, risk_adjusted_collateral: float, *,
                             counterparty_is_insurer: bool | None,
                             collateral_ignored_in_estate_share: bool | None,
                             qualification_reference: str, encumbered_asset_fraction: float | None = None,
                             context: Context, method: str = "standard",
                             proportionality_reference: str | None = None):
    """Choose standard/high-encumbrance formula; input includes corresponding receivables.

    This SCR LGD is distinct from the technical-provisions loss in Article42.
    Netting, collateral eligibility and contract qualifications remain external.
    """
    _reference(qualification_reference, "qualification_reference")
    require(method in ("standard", "simplified_112a"), "method",
            "explicit supported reinsurance LGD method required", "UNSUPPORTED_METHOD")
    if method == "simplified_112a":
        _reference(proportionality_reference, "proportionality_reference")
        require(counterparty_is_insurer is None and encumbered_asset_fraction is None,
                "counterparty_inputs", "standard encumbrance inputs unused by Article112a")
        exposure = number(recoverables, "recoverables")
        rm = number(risk_mitigation, "risk_mitigation", 0)
        collateral = number(risk_adjusted_collateral, "risk_adjusted_collateral", 0)
        exposure_weight = number(scalar("simplified_reinsurance_lgd_weight", context), "lgd_weight", 0, 1)
        rm_weight = number(scalar("simplified_reinsurance_lgd_rm_weight", context), "rm_weight", 0, 1)
        factor = _factor("F", collateral_ignored_in_estate_share, context)
        gross = number(exposure_weight * number(exposure + rm_weight * rm, "weighted_exposure"), "gross_lgd")
        reduction = number(factor * collateral, "collateral_component")
        raw = number(gross - reduction, "unfloored_lgd")
        return max(raw, 0), {"variant": "reinsurance_simplified_112a", "exposure": exposure,
            "risk_mitigation": rm, "collateral": collateral, "collateral_basis": "risk_adjusted",
            "exposure_weight": exposure_weight, "rm_weight": rm_weight,
            "factor_type": "F", "collateral_factor": factor,
            "collateral_ignored_in_estate_share": collateral_ignored_in_estate_share,
            "gross_lgd_component": gross, "collateral_component": reduction, "unfloored_lgd": raw,
            "qualification_reference": qualification_reference,
            "proportionality_reference": proportionality_reference,
            "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "lgd_formula_only",
            "_sources": ["DR:article-112a"]}
    require(proportionality_reference is None, "proportionality_reference",
            "simplification reference unused by standard method")
    insurer = _known_flag(counterparty_is_insurer, "counterparty_is_insurer")
    fraction = (number(encumbered_asset_fraction, "encumbered_asset_fraction", 0, 1)
                if encumbered_asset_fraction is not None else None)
    require(not insurer or fraction is not None, "encumbered_asset_fraction",
            "insurer encumbrance assessment required", "REVIEW_REQUIRED")
    threshold = number(scalar("default_lgd_encumbrance_threshold", context), "encumbrance_threshold", 0, 1)
    high = insurer and fraction > threshold
    variant = "reinsurance_encumbered" if high else "reinsurance_standard"
    value, details = _lgd(recoverables, risk_mitigation, risk_adjusted_collateral, variant,
                          collateral_ignored_in_estate_share, context)
    return value, {**details, "counterparty_is_insurer": insurer, "encumbered_asset_fraction": fraction,
                   "encumbrance_threshold": threshold, "qualification_reference": qualification_reference,
                   "collateral_basis": "risk_adjusted"}


@calculation("DR:article-192:3-3c", "DR:article-197:7")
def default_derivative_lgd(derivative_value: float, risk_mitigation: float, collateral_value: float, *,
                            variant: str, collateral_basis: str, collateral_ignored_in_estate_share: bool | None,
                            qualification_reference: str, context: Context):
    """Four externally qualified variants, with explicit market/risk-adjusted collateral.

    For a qualified netting set, RM and collateral must be assessed at set level;
    summing stand-alone risk mitigation is not justified by this function.
    """
    require(variant in ("3", "3a", "3b", "3c"), "variant", "Article192 derivative variant required",
            "UNSUPPORTED_METHOD")
    expected_basis = "risk_adjusted" if variant == "3c" else "market_value"
    require(collateral_basis == expected_basis, "collateral_basis", f"{expected_basis} required for this variant")
    _reference(qualification_reference, "qualification_reference")
    value, details = _lgd(derivative_value, risk_mitigation, collateral_value, "derivative_" + variant,
                          collateral_ignored_in_estate_share, context)
    return value, {**details, "collateral_basis": collateral_basis, "qualification_reference": qualification_reference}


@calculation("DR:article-192:4")
def default_mortgage_lgd(loan_value: float, risk_adjusted_mortgage: float, eligible_guarantee: float, *,
                          qualification_reference: str, context: Context,
                          guarantee_conditions: Mapping | None = None):
    """Use a qualified stress guarantee, not an arbitrary guarantee nominal amount.

    The future Article192(4) adds a floor on the non-guaranteed loan value.
    Historical results retain the published zero floor, not the new 5% floor.
    """
    loan = number(loan_value, "loan_value", 0)
    mortgage = number(risk_adjusted_mortgage, "risk_adjusted_mortgage", 0)
    guarantee = number(eligible_guarantee, "eligible_guarantee", 0)
    _reference(qualification_reference, "qualification_reference")
    weight = number(scalar("default_lgd_mortgage_weight", context), "default_lgd_mortgage_weight", 0, 1)
    protection = number(weight * mortgage + guarantee, "protection")
    raw = number(loan - protection, "unfloored_lgd")
    future = effective_resource("profile.json", context).get("methods", {}).get("default_lgd_rules") == "2027"
    guarantee_audit = None
    if guarantee_conditions is not None:
        exact_keys(guarantee_conditions, ("provider_route", "conditions"), "guarantee_conditions")
        route = guarantee_conditions["provider_route"]
        require(isinstance(route, str) and route in ("direct_public", "publicly_guaranteed",
                "publicly_guaranteed_provisional"), "provider_route", "explicit supported guarantee route required")
        require(future or route == "direct_public", "provider_route",
                "indirect public guarantee route only available in future profile", "UNSUPPORTED_RULESET")
        fields = ["provider_180_2_a_to_d" if route == "direct_public" else
                  "provider_fully_guaranteed_by_180_2_a_to_d", "article209", "article210", "amount_at_required_stress"]
        fields += (["article215_other_a_to_e", "timely_provisional_payment_right",
                    "robust_loss_estimate_including_missed_payments", "proportional_to_guarantee_cover"]
                   if route == "publicly_guaranteed_provisional" else ["article215_a_to_e"])
        flags = guarantee_conditions["conditions"]
        exact_keys(flags, tuple(fields), "guarantee_conditions.conditions")
        checked = {key: _known_flag(flags[key], key) for key in fields}
        require(all(checked.values()), "guarantee_conditions",
                "guarantee recognition conditions not established", "REVIEW_REQUIRED")
        guarantee_audit = {"provider_route": route, "conditions": checked}
    floor_rate = number(scalar("default_lgd_mortgage_floor", context), "mortgage_floor_rate", 0, 1) if future else 0
    floor = floor_rate * max(0, loan - guarantee)
    return max(raw, floor), {"loan_value": loan, "risk_adjusted_mortgage": mortgage, "eligible_guarantee": guarantee,
                        "mortgage_weight": weight, "protection": protection, "unfloored_lgd": raw,
                        "floor_rate": floor_rate, "floor_amount": floor,
                        "guarantee_conditions": guarantee_audit,
                        "guarantee_conditions_status": ("DECLARED_CONDITIONS_CHECKED_EXTERNAL_UNVERIFIED"
                            if guarantee_audit is not None else "NOT_ASSESSED"),
                        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                        "scope": "mortgage_lgd_only_not_eligibility_or_collateral_valuation"}


@calculation("DR:article-192:3e-3f")
def default_securities_financing_lgd_2027(exposure: float, risk_adjusted_collateral: float, *,
        netting_applied: bool, qualification_reference: str, context: Context):
    """Qualified repo/reverse-repo/securities-lending LGD, not a netting engine.

    Netted inputs must already represent the same legally qualified set's
    economic effect; collateral is assessed at set level, not blindly summed.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(netting_applied, bool), "netting_applied", "explicit netting choice required")
    exposure = number(exposure, "exposure", 0)
    collateral = number(risk_adjusted_collateral, "risk_adjusted_collateral", 0)
    raw = exposure - collateral
    return max(raw, 0), {"exposure": exposure, "risk_adjusted_collateral": collateral,
        "unfloored_lgd": raw, "netting_applied": netting_applied,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "qualified_financing_LGD_only_not_netting_decision_or_capital"}
