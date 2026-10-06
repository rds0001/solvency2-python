"""Explicit valuation rules on externally qualified assets and method inputs."""
import math
from typing import Mapping

from ._cashflows import payment_discount_factor
from .core import Context, calculation, exact_keys, number, require, scalar


def _reference(value):
    require(isinstance(value, str) and bool(value.strip()), "qualification_reference",
            "external asset/method/valuation qualification required", "MISSING_INPUT")



@calculation("DR:article-9:4", "VALUATION_GUIDANCE:guideline-12:1.33", unit="indicator")
def valuation_accounts_method_conditions(conditions: Mapping[str, bool], *,
                                         in_ifrs_consolidation_group: bool,
                                         qualification_reference: str, context: Context):
    """Check declared Article9(4) facts; never establish method compatibility.

    The IFRS-group exclusion is distinct from the four Article9 conditions.
    Article13/16 restrictions and substantive comparison evidence remain separate.
    """
    _reference(qualification_reference)
    keys = ("article75_compatible", "risk_proportionate", "not_ifrs_in_accounts", "ifrs_cost_disproportionate")
    exact_keys(conditions, keys, "conditions")
    facts = {**conditions, "in_ifrs_consolidation_group": in_ifrs_consolidation_group}
    for name, value in facts.items():
        require(value is not None, name, "external method qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(value, bool), name, "explicit boolean required")
    met = all(conditions.values()) and not in_ifrs_consolidation_group
    return int(met), {"conditions": dict(conditions), "in_ifrs_consolidation_group": in_ifrs_consolidation_group,
                      "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                      "scope": "declared_method_conditions_not_valuation_or_legal_method_approval"}


@calculation("DIR:article-75", "DIR:article-88:1", "DR:article-9:5-6")
def valuation_balance_sheet_excess(assets: Mapping[str, float], liabilities: Mapping[str, float], *,
                                    complete_scope: bool, qualification_reference: str, context: Context):
    """Sum externally qualified positions, retaining negative values and surplus.

    Own shares remain assets and subordinated debt remains a liability here;
    the separate Article88 component subsequently adjusts those exactly once.
    A declared complete input scope does not certify a complete insurer balance.
    """
    _reference(qualification_reference)
    require(complete_scope is None or isinstance(complete_scope, bool), "complete_scope", "explicit boolean required")
    require(complete_scope is True, "complete_scope", "complete chosen scope must be externally qualified",
            "REVIEW_REQUIRED")
    sides = {}
    for name, positions in (("assets", assets), ("liabilities", liabilities)):
        require(isinstance(positions, Mapping), name, "position-labelled mapping required")
        checked = {}
        for key, amount in positions.items():
            require(isinstance(key, str) and bool(key.strip()), name, "nonempty position identifier required")
            checked[key] = number(amount, f"{name}.{key}")
        sides[name] = checked
    require(not (set(sides["assets"]) & set(sides["liabilities"])), "positions",
            "position identifiers must not occur on both balance-sheet sides")
    try:
        total_assets = math.fsum(sides["assets"].values())
        total_liabilities = math.fsum(sides["liabilities"].values())
        excess = math.fsum([*sides["assets"].values(), *(-v for v in sides["liabilities"].values())])
    except OverflowError:
        require(False, "balance_sheet", "balance-sheet sum not representable", "REVIEW_REQUIRED")
    return excess, {**sides, "total_assets": total_assets, "total_liabilities": total_liabilities,
                    "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                    "scope": "qualified_position_arithmetic_not_recognition_or_complete_insurer_certification"}


@calculation("DR:article-14:1")
def valuation_liability_excluding_own_credit(current_value: float, own_credit_change: float, *,
                                              qualification_reference: str, context: Context):
    """Remove externally isolated cumulative own-credit value change since initial recognition.

    The input is a monetary valuation effect, not a spread or a period-only
    delta. Initial-recognition credit is retained; do not also apply this
    correction to a bottom-up value already holding initial credit constant.
    """
    _reference(qualification_reference)
    current = number(current_value, "current_value")
    credit = number(own_credit_change, "own_credit_change")
    try:
        value = math.fsum((current, -credit))
    except OverflowError:
        require(False, "adjusted_value", "own-credit-adjusted value not representable", "REVIEW_REQUIRED")
    return value, {"current_value": current, "excluded_own_credit_change": credit,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "top_down_value_correction_not_credit_model_or_initial_credit_removal"}


@calculation("DR:article-15", "VALUATION_GUIDANCE:guideline-9:1.26-1.27")
def valuation_deferred_tax_net(deferred_tax_assets: float, deferred_tax_liabilities: float, *,
                                legally_enforceable_offset: bool, same_tax_authority: bool,
                                same_taxable_entity: bool, undiscounted: bool,
                                qualification_reference: str, context: Context,
                                excluded_participations: Mapping | None = None, valuation_level: str | None = None,
                                recognition_conditions: Mapping | None = None, recognition_documents: Mapping | None = None):
    """Net externally recognised, undiscounted tax balances only when qualified.

    Positive results are net assets; negative results are net liabilities.
    No tax rates, taxable-profit projections, expiry or LAC-DT are calculated.
    """
    _reference(qualification_reference)
    asset = number(deferred_tax_assets, "deferred_tax_assets", 0)
    liability = number(deferred_tax_liabilities, "deferred_tax_liabilities", 0)
    flags = {"legally_enforceable_offset": legally_enforceable_offset, "same_tax_authority": same_tax_authority,
             "same_taxable_entity": same_taxable_entity, "undiscounted": undiscounted}
    for name, flag in flags.items():
        require(flag is not None, name, "external tax qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(flag, bool), name, "explicit boolean required")
    require(all(flags.values()), "tax_conditions", "qualified offset conditions and undiscounted balances required",
            "UNSUPPORTED_METHOD")
    from .valuation_tax_controls import tax_controls
    original_asset, original_liability = asset, liability
    asset, liability, controls, sources = tax_controls(asset, liability, excluded_participations,
        valuation_level, recognition_conditions, recognition_documents)
    net = asset - liability
    return net, {"deferred_tax_assets": asset, "deferred_tax_liabilities": liability,
                 "original_deferred_tax_assets": original_asset, "original_deferred_tax_liabilities": original_liability,
                 "recognition_controls": controls, "_sources": sources,
                 "net_asset": max(net, 0), "net_liability": max(-net, 0),
                 "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                 "scope": "qualified_tax_netting_not_recognition_profit_projection_or_lac_dt"}


@calculation("DR:article-16:1")
def valuation_short_term_deposit_cost_2027(cost_value: float, term_years: float, *,
                                           small_non_complex: bool, no_material_valuation_error: bool,
                                           alternative_value: float | None = None, method: str,
                                           qualification_reference: str, context: Context):
    """Apply the 2027 deposit exception, without computing cost or amortisation.

    Deposit classification, term basis, SNC status and materiality are external.
    Both comparisons are strict; failure does not invent a fair-value fallback.
    """
    _reference(qualification_reference)
    require(method in ("cost", "amortised_cost"), "method", "cost or amortised_cost required", "UNSUPPORTED_METHOD")
    cost = number(cost_value, "cost_value", 0)
    term = number(term_years, "term_years", 0)
    limit = number(scalar("valuation_deposit_term_limit_years", context), "valuation_deposit_term_limit_years", 0)
    require(limit > 0, "valuation_deposit_term_limit_years", "positive term limit required")
    for name, flag in (("small_non_complex", small_non_complex),
                       ("no_material_valuation_error", no_material_valuation_error)):
        require(flag is not None, name, "external deposit qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(flag, bool), name, "explicit boolean required")
    require(small_non_complex and term < limit, "eligibility",
            "SNC classification and term strictly below limit required", "UNSUPPORTED_METHOD")
    if no_material_valuation_error:
        require(alternative_value is None, "alternative_value", "omit unused alternative value")
        branch = "no_material_valuation_error"
    else:
        alternative = number(alternative_value, "alternative_value", 0)
        require(cost < alternative, "alternative_value", "cost must be strictly below alternative value",
                "UNSUPPORTED_METHOD")
        branch = "strictly_lower_than_alternative"
    return cost, {"method": method, "term_years": term, "term_limit_years": limit,
                  "condition_branch": branch, "alternative_value": alternative_value,
                  "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                  "scope": "qualified_short_term_deposit_exception_not_cost_model_or_SNC_classification"}


@calculation("DR:article-13:2", "DIR:article-214:2", "DIR:article-229")
def valuation_participation_value(*, excluded_from_group_supervision: bool,
                                  deducted_from_group_own_funds: bool,
                                  qualified_value: float | None = None,
                                  qualification_reference: str, context: Context):
    """Apply two externally qualified exclusions, not a group-scope decision.

    Flags refer specifically to Directive214(2) and229. Otherwise the external
    Article13 value passes through without a floor or a second ownership share.
    """
    _reference(qualification_reference)
    for name, flag in (("excluded_from_group_supervision", excluded_from_group_supervision),
                       ("deducted_from_group_own_funds", deducted_from_group_own_funds)):
        require(flag is not None, name, "external exclusion qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(flag, bool), name, "explicit boolean required")
    excluded = excluded_from_group_supervision or deducted_from_group_own_funds
    if excluded:
        require(qualified_value is None, "qualified_value", "omit unused value for excluded participation")
        value = number(scalar("valuation_participation_zero_value", context), "valuation_participation_zero_value", 0)
    else:
        value = number(qualified_value, "qualified_value")
    return value, {"excluded_from_group_supervision": excluded_from_group_supervision,
                   "deducted_from_group_own_funds": deducted_from_group_own_funds,
                   "zero_rule_applied": excluded, "qualification_reference": qualification_reference,
                   "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "participation_recognition_component_not_exclusion_or_method_qualification"}


@calculation("DR:article-11", "DR:article-14:2")
def valuation_contingent_liability(cashflows: Mapping[str, dict], *, recognised_under_article11: bool,
                                   runoff_complete: bool, curve_basis: str,
                                   qualification_reference: str, curve_reference: str, context: Context):
    """Discount externally expected settlement payments on a basic risk-free curve.

    Recognition/materiality, complete runoff, probability weighting and curve
    construction are external. In particular VA/MA curves are not accepted.
    """
    _reference(qualification_reference)
    require(isinstance(curve_reference, str) and bool(curve_reference.strip()), "curve_reference",
            "external basic-risk-free curve reference required", "MISSING_INPUT")
    for name, flag in (("recognised_under_article11", recognised_under_article11), ("runoff_complete", runoff_complete)):
        require(flag is None or isinstance(flag, bool), name, "explicit boolean required")
        require(flag is True, name, "recognition and complete runoff must be externally qualified", "REVIEW_REQUIRED")
    require(curve_basis == "basic_risk_free", "curve_basis", "Article14(2) requires basic risk-free curve",
            "UNSUPPORTED_PARAMETER")
    require(isinstance(cashflows, Mapping), "cashflows", "date-labelled mapping required")
    require(bool(cashflows), "cashflows", "explicit cashflow or zero row required", "MISSING_INPUT")
    rows = {}
    for label, row in cashflows.items():
        exact_keys(row, ("expected_payment", "discount_factor"), label)
        payment = number(row["expected_payment"], f"{label}.expected_payment", 0)
        factor = payment_discount_factor(label, row["discount_factor"], context)
        discounted = payment * factor
        require(math.isfinite(discounted), label, "discounted payment not representable", "REVIEW_REQUIRED")
        rows[label] = {"expected_payment": payment, "discount_factor": factor, "discounted_payment": discounted}
    try:
        value = math.fsum(row["discounted_payment"] for row in rows.values())
    except OverflowError:
        require(False, "present_value", "present value not representable", "REVIEW_REQUIRED")
    return value, {"cashflows": rows, "curve_basis": curve_basis, "curve_reference": curve_reference,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "recognised_contingent_liability_pv_not_materiality_or_projection_model"}


@calculation("DR:article-12:1-2", "DR:article-10")
def valuation_intangible_value(asset_type: str, *, separately_saleable: bool | None = None,
                                active_market_value_evidenced: bool | None = None,
                                qualified_value: float | None = None,
                                qualification_reference: str, context: Context):
    """Apply goodwill/other-intangible zero rules, not a fair-value model.

    Positive recognition requires both external Article12 qualifications and a
    separately supplied Article10 value. Unused values are rejected, not ignored.
    """
    _reference(qualification_reference)
    require(asset_type in ("goodwill", "other_intangible"), "asset_type", "explicit intangible category required",
            "UNSUPPORTED_PARAMETER")
    zero = number(scalar("valuation_intangible_zero_value", context), "valuation_intangible_zero_value", 0)
    if asset_type == "goodwill":
        require(separately_saleable is None and active_market_value_evidenced is None and qualified_value is None,
                "goodwill", "omit unused saleability, market and value inputs")
        value, branch = zero, "goodwill_zero_rule"
    else:
        for name, flag in (("separately_saleable", separately_saleable),
                           ("active_market_value_evidenced", active_market_value_evidenced)):
            require(flag is not None, name, "external qualification unresolved", "REVIEW_REQUIRED")
            require(isinstance(flag, bool), name, "explicit boolean required")
        if separately_saleable and active_market_value_evidenced:
            value, branch = number(qualified_value, "qualified_value", 0), "externally_qualified_article10_value"
        else:
            require(qualified_value is None, "qualified_value", "omit unused value for zero-rule branch")
            value, branch = zero, "other_intangible_zero_rule"
    return value, {"asset_type": asset_type, "valuation_branch": branch,
                   "separately_saleable": separately_saleable,
                   "active_market_value_evidenced": active_market_value_evidenced,
                   "qualified_value": qualified_value, "zero_rule_value": zero,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "intangible_rule_component_not_market_valuation_or_factual_qualification"}


@calculation("DR:article-13:3-4")
def valuation_adjusted_equity_component(excess_assets_over_liabilities: float, share: float, *,
                                         qualification_reference: str, context: Context):
    """Apply the held share to externally qualified Article13 net assets.

    No floor, method-ranking decision, Article13(2) exclusion determination or
    asset/technical-provision valuation is inferred from this arithmetic.
    """
    _reference(qualification_reference)
    excess = number(excess_assets_over_liabilities, "excess_assets_over_liabilities")
    proportion = number(share, "share", 0, 1)
    return excess * proportion, {"excess_assets_over_liabilities": excess, "share": proportion,
                                 "qualification_reference": qualification_reference,
                                 "qualification_status": "EXTERNAL_UNVERIFIED",
                                 "scope": "adjusted_equity_arithmetic_not_method_or_final_recognition_decision"}


@calculation("DR:article-13:5-6", "DR:article-12")
def valuation_accounting_equity_adjustment(participation_value: float, goodwill_amount: float,
                                            zero_valued_intangibles_amount: float, *, method: str,
                                            qualification_reference: str, context: Context):
    """Deduct already scope-aligned goodwill and Article12-zero intangibles.

    Method eligibility, hierarchy and Article13(2) exclusions are external.
    Inputs use the same held-participation basis; never apply ownership twice.
    """
    _reference(qualification_reference)
    require(method in ("ias_equity_fallback", "accounts_method_fallback"), "method",
            "explicit Article13(5) or13(6) method required", "UNSUPPORTED_METHOD")
    value = number(participation_value, "participation_value")
    goodwill = number(goodwill_amount, "goodwill_amount", 0)
    intangible = number(zero_valued_intangibles_amount, "zero_valued_intangibles_amount", 0)
    try:
        adjusted = math.fsum((value, -goodwill, -intangible))
    except OverflowError:
        require(False, "adjusted_value", "adjusted participation value not representable", "REVIEW_REQUIRED")
    return adjusted, {"participation_value": value, "goodwill_deduction": goodwill,
                      "zero_intangible_deduction": intangible, "method": method,
                      "_sources": ["DR:article-13:5" if method == "ias_equity_fallback" else "DR:article-13:6",
                                   "DR:article-12"],
                      "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                      "scope": "accounting_equity_adjustment_not_method_eligibility_or_final_recognition"}
