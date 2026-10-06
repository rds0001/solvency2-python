"""Tier-limit checks for proposed full coverage, not own-funds classification."""
import math
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .evidence import _declared_bool, _evidence_inventory


@calculation("DR:articles-62-67", "DR:articles-69;71-79", unit="indicator")
def own_funds_classification_evidence_check(evidence: Mapping, *, tier: str,
                                            own_funds_kind: str, unlisted: bool,
                                            assessment_reference: str, context: Context):
    """Inventory declared classification evidence, never classify an instrument.

    References identify the applicable instrument/subparagraph, justified
    non-applicability and any approved exception. Periods describe those routes;
    they are not unconditional maturity tests or permission to repay. Tier1
    quality in excess of its cap may follow73(1)(j), not ordinary Tier2 terms.
    Values for subsequent allocation remain independently qualified inputs.
    """
    require(isinstance(tier, str) and tier in ("tier1", "tier2", "tier3"),
            "tier", "explicit proposed tier required")
    require(isinstance(own_funds_kind, str) and own_funds_kind in ("basic", "ancillary"),
            "own_funds_kind", "basic or ancillary required")
    require(not (tier == "tier1" and own_funds_kind == "ancillary"),
            "tier", "ancillary funds cannot be classified Tier1", "UNSUPPORTED_PARAMETER")
    _declared_bool(unlisted, "unlisted")
    profile = effective_resource("profile.json", context)
    scopes = {"always", own_funds_kind + "_" + tier}
    if own_funds_kind == "ancillary":
        scopes.add("ancillary")
    if unlisted:
        scopes.add("unlisted")
    rows = [row[:3] for row in profile["tables"]["own_funds_classification_controls"]["rows"] if row[3] in scopes]
    value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    keys = ({"tier1": ("tier1_first_call_years", "tier1_margin_window_end_years"),
             "tier2": ("tier2_original_term_years", "tier2_first_call_years", "tier2_incentive_start_years"),
             "tier3": ("tier3_original_term_years",)}[tier] if own_funds_kind == "basic" else
            (("mutual_call_horizon_months", "ancillary_method_reference_years") if tier == "tier2" else
             ("ancillary_method_reference_years",)))
    if context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1":
        keys = (*keys, "buyback_option_exception_months")
    periods = {}
    for key in keys:
        parameter = profile["scalars"]["own_funds_" + key]
        limit = number(parameter["value"], key, 0)
        require(limit > 0, key, "positive contractual reference period required")
        periods[key] = {"value": limit, "unit": parameter["unit"], "source": parameter["source"]}
        details["_sources"].append(parameter["source"])
    return value, {**details, "proposed_tier": tier, "own_funds_kind": own_funds_kind,
        "unlisted": unlisted, "conditional_reference_periods": periods,
        "period_applicability": "Qualified instrument subparagraph and exceptions control applicability; not blanket gates.",
        "instrument_classification_verified": False, "actual_terms_or_periods_verified": False,
        "supervisory_approval_verified": False, "eligible_amount_calculated": False,
        "scope": "declared_classification_evidence_not_legal_tier_assignment_or_redemption_permission"}


def _qualification(reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external valuation/classification/completeness reference required", "MISSING_INPUT")


def _version_sources(context, *references):
    profile = effective_resource("profile.json", context)
    return [context.profile_id + ":" + profile["sources"][reference.split(":", 1)[0]]["sha256"]
            + ":" + reference.split(":", 1)[1] for reference in references]


def _all_facts(*values):
    return False if any(value is False for value in values) else None if None in values else True


def _any_facts(*values):
    return True if any(value is True for value in values) else None if None in values else False


@calculation(unit="rate")
def own_funds_step_up_limit(original_credit_spread: float, swap_spread: float, *, tier: str,
                             one_off_coupon_increase_with_call_option: bool | None,
                             qualification_reference: str, context: Context):
    """Art73(4)/77(4) maximum modest one-off step-up, not whole-tier eligibility.

    Decimal rate units:100bp=.01. The original-to-stepped-index swap spread is
    subtracted in BOTH branches; a negative limit is retained, never floored.
    """
    _qualification(qualification_reference)
    require(tier in ("tier2", "tier3"), "tier", "Tier2 or Tier3 required", "UNSUPPORTED_METHOD")
    flag = one_off_coupon_increase_with_call_option
    require(flag is None or isinstance(flag, bool), "one_off_coupon_increase_with_call_option",
            "boolean or unresolved None required")
    require(flag is not None, "one_off_coupon_increase_with_call_option", "instrument arrangement unresolved",
            "REVIEW_REQUIRED")
    require(flag, "one_off_coupon_increase_with_call_option", "outside one-off step-up with call scope",
            "UNSUPPORTED_METHOD")
    article = "73" if tier == "tier2" else "77"
    credit, swap = number(original_credit_spread, "original_credit_spread"), number(swap_spread, "swap_spread")
    absolute = number(scalar(f"step_up_{article}_absolute", context), "absolute", 0)
    fraction = number(scalar(f"step_up_{article}_credit_fraction", context), "credit_fraction", 0)
    limit = max(absolute - swap, fraction * credit - swap)
    return limit, {"tier": tier, "absolute_branch": absolute - swap,
                   "credit_branch": fraction * credit - swap,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "modest_step_up_numeric_limit_not_tier_eligibility",
                   "_sources": [f"DR:article-{article}:4"]}


@calculation("DR:article-71:8", unit="indicator")
def own_funds_tier1_loss_absorption_trigger(eligible_scr_own_funds: float, scr: float,
                                           eligible_mcr_own_funds: float, mcr: float, *,
                                           scr_not_restored_within_period: bool | None,
                                           additional_contractual_trigger: bool | None,
                                           qualification_reference: str, context: Context):
    """Article71(8) event screen, NOT write-down/conversion or Tier1 eligibility.

    Use distinct SCR/MCR eligible funds. Equality at either threshold triggers.
    The three-month non-restoration history and any additional contractual event
    are externally established; a current recovery does not erase a past event.
    Article71(10) waiver may affect execution, never the fact of the event.
    """
    _qualification(qualification_reference)
    funds_scr = number(eligible_scr_own_funds, "eligible_scr_own_funds")
    funds_mcr = number(eligible_mcr_own_funds, "eligible_mcr_own_funds")
    scr_value, mcr_value = number(scr, "scr", 0), number(mcr, "mcr", 0)
    require(scr_value > 0 and mcr_value > 0, "capital_requirements",
            "positive qualified SCR and MCR required", "REVIEW_REQUIRED")
    for key, flag in (("scr_not_restored_within_period", scr_not_restored_within_period),
                      ("additional_contractual_trigger", additional_contractual_trigger)):
        require(flag is None or isinstance(flag, bool), key, "boolean or unresolved None required")
    threshold = number(scalar("tier1_loss_absorption_scr_threshold", context), "scr_threshold", 0, 1)
    mcr_threshold = number(scalar("tier1_loss_absorption_mcr_threshold", context), "mcr_threshold", 0, 1)
    months = number(scalar("tier1_loss_absorption_nonrestoration_months", context), "period_months", 0)
    require(months > 0, "period_months", "positive qualification period required", "REVIEW_REQUIRED")
    events = {"scr_threshold": funds_scr <= threshold * scr_value,
              "mcr_threshold": funds_mcr <= mcr_threshold * mcr_value,
              "scr_nonrestoration": scr_not_restored_within_period,
              "additional_contractual": additional_contractual_trigger}
    triggered = _any_facts(*events.values())
    require(triggered is not None, "events", "necessary event history unresolved", "REVIEW_REQUIRED")
    return int(triggered), {"events": events, "scr_threshold": threshold,
                            "mcr_threshold": mcr_threshold, "nonrestoration_period_months": months,
                            "eligible_scr_own_funds": funds_scr, "eligible_mcr_own_funds": funds_mcr,
                            "scr": scr_value, "mcr": mcr_value,
                            "qualification_reference": qualification_reference,
                            "qualification_status": "EXTERNAL_UNVERIFIED",
                            "instrument_classification_verified": False,
                            "mechanism_execution_determined": False, "supervisory_waiver_applied": False,
                            "scope": "article71_8_event_only_not_tier_classification_or_mechanism_execution"}


@calculation("DR:article-71:5a", "DR:article-71:6a", "DR:article-71:10", unit="indicator")
def own_funds_tier1_mechanism_requirements(eligible_scr_own_funds: float, scr: float,
                                          eligible_mcr_own_funds: float, mcr: float, *,
                                          scr_not_restored_within_period: bool | None,
                                          additional_contractual_trigger: bool | None,
                                          mechanism: str, partial_restoration_sufficient: bool | None,
                                          qualification_reference: str, context: Context,
                                          waiver_conditions: Mapping | None = None,
                                          waiver_reference: str | None = None):
    """Select statutory execution requirements; no instrument amount or booking.

    a/b requires full absorption. c permits partial restoration or at-least-linear
    absorption, unless the narrowly qualified supervisory exception is declared.
    Contract-only additional triggers have no universal execution rule here.
    """
    require(mechanism in ("write_down", "conversion"), "mechanism", "explicit mechanism required",
            "UNSUPPORTED_METHOD")
    require(partial_restoration_sufficient is None or isinstance(partial_restoration_sufficient, bool),
            "partial_restoration_sufficient", "boolean or unresolved None required")
    screen = own_funds_tier1_loss_absorption_trigger(
        eligible_scr_own_funds, scr, eligible_mcr_own_funds, mcr,
        scr_not_restored_within_period=scr_not_restored_within_period,
        additional_contractual_trigger=additional_contractual_trigger,
        qualification_reference=qualification_reference, context=context)
    events = screen.details["events"]
    full = events["scr_threshold"] or events["mcr_threshold"]
    waiver = False
    if waiver_conditions is not None:
        keys = ("instrument_terms_permit_waiver", "no_previous_a_or_b_events",
                "supervisory_exceptional_approval", "tax_projections_submitted_with_recovery_plan",
                "likely_severely_adverse_tax_liability", "auditor_realistic_assumptions_certified")
        exact_keys(waiver_conditions, keys, "waiver_conditions")
        for key, flag in waiver_conditions.items():
            require(flag is None or isinstance(flag, bool), key, "boolean or unresolved None required")
        waiver = _all_facts(not full, events["scr_nonrestoration"], *waiver_conditions.values())
        require(waiver is not None, "waiver_conditions", "necessary exception facts unresolved", "REVIEW_REQUIRED")
        if waiver:
            require(isinstance(waiver_reference, str) and bool(waiver_reference.strip()),
                    "waiver_reference", "specific external supervisory/tax/auditor evidence required", "MISSING_INPUT")
    else:
        require(waiver_reference is None, "waiver_reference", "reference without exception declaration")
    if not screen.value:
        route = "NO_EVENT"
    elif full:
        route = "FULL_ABSORPTION"
    elif events["scr_nonrestoration"] is True:
        if waiver:
            route = "DECLARED_SUPERVISORY_EXCEPTION"
        else:
            require(partial_restoration_sufficient is not None, "partial_restoration_sufficient",
                    "restoration capability requires external assessment", "REVIEW_REQUIRED")
            route = "PARTIAL_RESTORATION" if partial_restoration_sufficient else "AT_LEAST_LINEAR_ABSORPTION"
    else:
        require(events["scr_nonrestoration"] is not None, "scr_not_restored_within_period",
                "statutory versus contract-only event unresolved", "REVIEW_REQUIRED")
        require(False, "additional_contractual_trigger", "contract-only event execution must be externally specified",
                "UNSUPPORTED_METHOD")
    review_months = number(scalar("tier1_loss_absorption_review_months", context), "review_months", 0)
    full_by = number(scalar("tier1_loss_absorption_full_by_ratio", context), "full_by_ratio", 0, 1)
    require(review_months > 0, "review_months", "positive review period required", "REVIEW_REQUIRED")
    return int(route in ("FULL_ABSORPTION", "PARTIAL_RESTORATION", "AT_LEAST_LINEAR_ABSORPTION")), {
        "events": events, "mechanism": mechanism, "required_route": route,
        "partial_restoration_sufficient": partial_restoration_sufficient,
        "full_absorption_by_scr_ratio": full_by, "subsequent_review_period_months": review_months,
        "linear_followup_required": route == "AT_LEAST_LINEAR_ABSORPTION",
        "first_period_deterioration_monitoring_required": route == "AT_LEAST_LINEAR_ABSORPTION",
        "later_a_or_b_requires_full_absorption": route == "AT_LEAST_LINEAR_ABSORPTION",
        "waiver_conditions": dict(waiver_conditions) if waiver_conditions is not None else None,
        "waiver_reference": waiver_reference, "declared_waiver_conditions_met": waiver,
        "supervisory_approval_verified": False, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "nominal_amount_calculated": False,
        "instrument_transaction_executed": False,
        "scope": "article71_declared_mechanism_requirements_not_instrument_classification_or_execution"}


@calculation("DR:article-68:3", unit="indicator")
def own_funds_financial_exemption_screen(facts: Mapping, *, qualification_reference: str,
                                          context: Context, approval_reference: str | None = None):
    """Version-specific declared-prerequisite screen, never approval of an exemption.

    Unknown necessary facts block the decision. A proved alternative can settle
    an OR without inventing facts. The 2027 branch separately requires declared
    actual supervisory permission; evidence remains externally qualified.
    """
    _qualification(qualification_reference)
    profile = effective_resource("profile.json", context)
    method = profile.get("methods", {}).get("financial_participation_exemption")
    require(method in ("METHOD1_BASELINE", "SUPERVISORY_PERMISSION_2027"), "profile_id",
            "explicit exemption method required", "UNSUPPORTED_RULESET")
    keys = (("strategic", "method1_financial_conglomerate", "method1_solvency2")
            if method == "METHOD1_BASELINE" else
            ("strategic", "same_qualified_group", "no_article228_5_deduction",
             "technical_methods_permitted", "same_supplementary_supervision",
             "supervisory_management_satisfactory", "non_deduction_approved"))
    exact_keys(facts, keys, "facts")
    for key, value in facts.items():
        require(value is None or isinstance(value, bool), "facts." + key, "explicit boolean or None required")
    sources = [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-68-3"]
    if method == "METHOD1_BASELINE":
        require(approval_reference is None, "approval_reference", "unused in historical Method1 screen")
        route = _any_facts(facts["method1_financial_conglomerate"], facts["method1_solvency2"])
        decision = _all_facts(facts["strategic"], route)
    else:
        approved = facts["non_deduction_approved"]
        if approved is True:
            require(isinstance(approval_reference, str) and bool(approval_reference.strip()),
                    "approval_reference", "reference to actual supervisory permission required", "MISSING_INPUT")
        else:
            require(approval_reference is None, "approval_reference", "permission reference requires explicit approved fact")
        group = _all_facts(facts["same_qualified_group"], facts["no_article228_5_deduction"])
        supplementary = _all_facts(facts["technical_methods_permitted"], facts["same_supplementary_supervision"])
        route = _any_facts(group, supplementary)
        decision = _all_facts(facts["strategic"], route, facts["supervisory_management_satisfactory"], approved)
        sources.append(context.profile_id + ":" + profile["sources"]["DIR"]["sha256"] + ":article-92-1a")
    require(decision is not None, "facts", "unknown necessary exemption prerequisites", "REVIEW_REQUIRED")
    return int(decision), {"facts": dict(facts), "method": method, "qualifying_route_declared": route,
        "qualification_reference": qualification_reference, "approval_reference": approval_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "approval_status": "NOT_INDEPENDENTLY_VERIFIED",
        "decision": "DECLARED_PREREQUISITES_MET" if decision else "DECLARED_PREREQUISITES_NOT_MET",
        "scope": "article68_3_declared_prerequisite_screen_not_exemption_approval", "_sources": sources}


@calculation("DR:article-68:5")
def own_funds_financial_deduction_tier(tier: str, available: Mapping, deductions: Mapping, *,
                                       qualification_reference: str, context: Context):
    """Select a remaining own-fund bucket after externally qualified deductions.

    All available amounts precede Article68 deductions. The deduction amounts
    already reflect version-specific exemption/approval decisions. This does not
    classify instruments, grant exemptions or calculate eligible own funds.
    """
    _qualification(qualification_reference)
    keys = ("unrestricted_tier1", "restricted_tier1", "tier2")
    require(tier in keys, "tier", "explicit affected own-fund tier required")
    exact_keys(available, keys, "available")
    exact_keys(deductions, ("cet1", "additional_tier1", "tier2", "unclassified"), "deductions")
    before = {key: number(available[key], "available." + key,
                          None if key == "unrestricted_tier1" else 0) for key in keys}
    charges = {key: number(value, "deductions." + key, 0) for key, value in deductions.items()}
    tier2_used = min(before["tier2"], charges["tier2"])
    tier2_excess = charges["tier2"] - tier2_used
    restricted_claim = math.fsum((charges["additional_tier1"], tier2_excess))
    restricted_used = min(before["restricted_tier1"], restricted_claim)
    restricted_excess = restricted_claim - restricted_used
    unrestricted_used = math.fsum((charges["cet1"], charges["unclassified"], restricted_excess))
    after = {"unrestricted_tier1": number(before["unrestricted_tier1"] - unrestricted_used, "remaining.unrestricted_tier1"),
             "restricted_tier1": before["restricted_tier1"] - restricted_used,
             "tier2": before["tier2"] - tier2_used}
    profile = effective_resource("profile.json", context)
    guidance = profile["sources"]["RELATED_GUIDANCE"]
    return after[tier], {"tier": tier, "available_before_deductions": before, "deductions": charges,
        "remaining": after, "tier2_excess": tier2_excess, "restricted_excess": restricted_excess,
        "deducted_by_tier": {"unrestricted_tier1": unrestricted_used,
                             "restricted_tier1": restricted_used, "tier2": tier2_used},
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "guidance_document": guidance["document_id"], "guidance_warning": guidance.get("source_warning"),
        "scope": "selected_remaining_bucket_not_total_eligible_own_funds_or_exemption_decision",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-68-5",
                     context.profile_id + ":" + guidance["sha256"] + ":" + guidance["document_id"]]}


@calculation("DIR:article-88")
def own_funds_basic_before_adjustments(excess_assets_over_liabilities: float,
                                       subordinated_liabilities: float, own_shares: float, *,
                                       qualification_reference: str, context: Context):
    """Compose Article88 amounts before further deductions and eligibility limits.

    Excess must still include own shares; using an already adjusted surplus
    here would double-deduct them. This is not eligible own funds or Tier1.
    """
    _qualification(qualification_reference)
    excess = number(excess_assets_over_liabilities, "excess_assets_over_liabilities")
    subordinate = number(subordinated_liabilities, "subordinated_liabilities", 0)
    shares = number(own_shares, "own_shares", 0)
    return math.fsum([excess, subordinate, -shares]), {
        "excess_assets_over_liabilities": excess, "subordinated_liabilities": subordinate,
        "own_shares": shares, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "basic_components_before_other_deductions_classification_and_eligibility",
        "regulatory_total_released": False}


@calculation("DR:article-70:1:2")
def own_funds_reconciliation_reserve(excess_assets_over_liabilities: float, deductions: Mapping, *,
                                      qualification_reference: str, context: Context):
    """Subtract Article70 items, with explicit financial-participation overlap.

    Future-premium expected profit is already in the supplied surplus, not an
    extra addition. A signed reserve is preserved; no Tier1 eligibility is
    inferred from this arithmetic. All deduction categories must be supplied.
    """
    _qualification(qualification_reference)
    excess = number(excess_assets_over_liabilities, "excess_assets_over_liabilities")
    keys = ["own_shares", "foreseeable_distributions", "listed_basic_items", "approved_unlisted_items",
            "restricted_items", "financial_participation_deductions", "financial_participation_already_counted"]
    exact_keys(deductions, keys, "deductions")
    amounts = {key: number(deductions[key], "deductions." + key, 0) for key in keys}
    first_five = math.fsum(amounts[key] for key in keys[:5])
    financial = amounts["financial_participation_deductions"]
    overlap = amounts["financial_participation_already_counted"]
    require(overlap <= financial and overlap <= first_five, "financial_participation_already_counted",
            "overlap cannot exceed financial deduction or other deductions")
    residual = financial - overlap
    return math.fsum([excess, -first_five, -residual]), {
        "_sources": _version_sources(context, "DR:article-70"),
        "excess_assets_over_liabilities": excess, "deductions": amounts,
        "deductions_a_to_e": first_five, "residual_financial_participation_deduction": residual,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "future_premium_profits": "ALREADY_INCLUDED_IN_EXCESS_NOT_ADDED_AGAIN",
        "scope": "reconciliation_reserve_arithmetic_not_tier1_classification_or_eligibility"}


@calculation("DR:article-70:1:e", "DR:article-80:2", "DR:article-81")
def own_funds_restricted_deduction(restricted_own_funds: float, portfolio_kind: str,
                                   immaterial_simplification: bool, *, notional_scr: float | None = None,
                                   qualification_reference: str, context: Context):
    """Deduct restricted surplus, or the full elected immaterial RFF amount.

    Restricted funds already exclude future shareholder transfers. Materiality,
    portfolio classification and notional SCR are externally qualified; no
    internal model or arbitrary materiality threshold is supplied here.
    """
    _qualification(qualification_reference)
    require(isinstance(portfolio_kind, str) and portfolio_kind in {"ring_fenced", "matching_adjustment"},
            "portfolio_kind", "ring_fenced or matching_adjustment required")
    method = effective_resource("profile.json", context).get("methods", {}).get("restricted_funds")
    require(method in ("RFF_AND_MA_BASELINE", "RFF_ONLY_2027"), "profile_id",
            "explicit restricted-funds scope required", "UNSUPPORTED_RULESET")
    require(method != "RFF_ONLY_2027" or portfolio_kind == "ring_fenced", "portfolio_kind",
            "2027 Article81 no longer includes matching-adjustment portfolios", "UNSUPPORTED_METHOD")
    require(isinstance(immaterial_simplification, bool), "immaterial_simplification", "explicit option decision required")
    restricted = number(restricted_own_funds, "restricted_own_funds", 0)
    if immaterial_simplification:
        require(portfolio_kind == "ring_fenced", "portfolio_kind", "Article81(2) option is for immaterial ring-fenced funds")
        require(notional_scr is None, "notional_scr", "omit unused SCR for full-deduction option")
        scr, deduction = None, restricted
    else:
        scr = number(notional_scr, "notional_scr", 0)
        deduction = max(restricted - scr, 0)
    return deduction, {
        "restricted_own_funds": restricted, "portfolio_kind": portfolio_kind,
        "immaterial_simplification": immaterial_simplification, "notional_scr": scr,
        "future_shareholder_transfers": "ALREADY_EXCLUDED_FROM_RESTRICTED_INPUT",
        "rule_scope": method, "_sources": _version_sources(context, "DR:article-70-1-e", "DR:article-81"),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "restricted_funds_deduction_not_classification_or_notional_scr_derivation"}


@calculation("DR:article-68:1:2:4")
def own_funds_financial_participation_deduction(participations: Mapping,
                                                threshold_basis: float, *,
                                                qualification_reference: str, context: Context):
    """Deduct qualified nonexempt financial participations, with per-holding audit.

    Each input is a complete participation, not an arbitrary instrument slice.
    Article68(3) exemptions and direct/indirect ownership are qualified before
    calling. SRC-0135 Guideline5 / SRC-0067 paragraph26 require the basis
    BEFORE Article68 deductions; exemptions are not inherited across versions.
    Deduction amounts here are not yet allocated to own-funds tiers.
    """
    _qualification(qualification_reference)
    require(isinstance(participations, Mapping), "participations", "complete explicit mapping required")
    require(all(isinstance(key, str) and key.strip() for key in participations),
            "participations", "nonempty string participation IDs required")
    basis = number(threshold_basis, "threshold_basis")
    fraction = number(scalar("own_funds_financial_participation_threshold", context), "threshold_fraction", 0, 1)
    threshold = number(basis * fraction, "threshold")
    values = {key: number(value, "participations." + key, 0) for key, value in participations.items()}
    full = {key: value for key, value in values.items() if value > threshold}
    pool = {key: value for key, value in values.items() if key not in full}
    pool_value = number(math.fsum(pool.values()), "residual_pool_value", 0)
    pool_deduction = max(pool_value - threshold, 0) if pool_value > 0 else 0
    factor = pool_deduction / pool_value if pool_value > 0 else 0
    rows = {}
    for key, value in values.items():
        deduction = value if key in full else value * factor
        rows[key] = {"value": value, "deduction": deduction, "remaining_value": value - deduction,
                     "branch": "FULL_INDIVIDUAL" if key in full else "RESIDUAL_POOL"}
    profile = effective_resource("profile.json", context)
    guidance = profile["sources"]["RELATED_GUIDANCE"]
    return math.fsum([*full.values(), pool_deduction]), {
        "threshold_basis": basis, "basis_timing": "BEFORE_ARTICLE68_DEDUCTIONS",
        "threshold_fraction": fraction, "threshold": threshold,
        "residual_pool_value": pool_value, "residual_pool_deduction": pool_deduction,
        "residual_pool_factor": factor, "participations": rows,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "guidance_document": guidance["document_id"], "guidance_warning": guidance.get("source_warning"),
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-68-1-2-4",
                     context.profile_id + ":" + guidance["sha256"] + ":" + guidance["document_id"]],
        "scope": "nonexempt_participation_deductions_not_ownership_exemption_or_tier_allocation"}


def _restricted_tier1(total: float, restricted: float, context: Context) -> None:
    """Article 82(3) applies to both SCR and MCR coverage allocations."""
    require(restricted <= total, "restricted_tier1", "subset exceeds total Tier 1")
    require(restricted <= scalar("own_funds_restricted_tier1_max", context) * total,
            "restricted_tier1", "restricted Tier 1 exceeds Article 82(3) limit",
            "INELIGIBLE_ALLOCATION")


@calculation("DIR:article-98:3", "DR:article-82:1", "DR:article-82:3")
def own_funds_scr_allocation(scr: float, tier1: float, restricted_tier1: float,
                             tier2: float, tier3: float, *, context: Context):
    """Validate one proposed full SCR-covering allocation of preclassified tiers."""
    scr = number(scr, "scr", 0)
    require(scr > 0, "scr", "positive target required for tier-limit review", "UNSUPPORTED_PARAMETER")
    t1, restricted, t2, t3 = (number(value, name, 0) for name, value in (
        ("tier1", tier1), ("restricted_tier1", restricted_tier1),
        ("tier2", tier2), ("tier3", tier3)))
    _restricted_tier1(t1, restricted, context)
    require(t1 >= scalar("own_funds_scr_tier1_min", context) * scr,
            "tier1", "Tier 1 below half the SCR", "INELIGIBLE_ALLOCATION")
    require(t3 < scalar("own_funds_scr_tier3_strict_max", context) * scr,
            "tier3", "Tier 3 must be strictly below 15% SCR", "INELIGIBLE_ALLOCATION")
    require(math.fsum((t2, t3)) <= scalar("own_funds_scr_tier2_tier3_max", context) * scr,
            "tier2_tier3", "Tier 2 plus Tier 3 exceeds half the SCR", "INELIGIBLE_ALLOCATION")
    total = math.fsum((t1, t2, t3))
    require(total >= scr, "allocation", "proposed own funds do not cover the SCR",
            "INSUFFICIENT_COVERAGE")
    return total, {"coverage_ratio": total / scr, "restricted_tier1": restricted,
                   "_sources": _version_sources(context, "DR:article-82", "DIR:article-98-3"),
                   "scope": "proposed_full_coverage_of_preclassified_amounts_only",
                   "classification_and_transferability": "EXTERNAL_INPUT_ONLY"}


@calculation("DIR:article-98:4", "DR:article-82:2", "DR:article-82:3")
def own_funds_mcr_allocation(mcr: float, basic_tier1: float, restricted_tier1: float,
                             basic_tier2: float, *, context: Context):
    """Validate one proposed full MCR-covering allocation of basic own funds."""
    mcr = number(mcr, "mcr", 0)
    require(mcr > 0, "mcr", "positive target required for tier-limit review", "UNSUPPORTED_PARAMETER")
    t1, restricted, t2 = (number(value, name, 0) for name, value in (
        ("basic_tier1", basic_tier1), ("restricted_tier1", restricted_tier1),
        ("basic_tier2", basic_tier2)))
    _restricted_tier1(t1, restricted, context)
    require(t1 >= scalar("own_funds_mcr_tier1_min", context) * mcr,
            "basic_tier1", "basic Tier 1 below 80% MCR", "INELIGIBLE_ALLOCATION")
    require(t2 <= scalar("own_funds_mcr_tier2_max", context) * mcr,
            "basic_tier2", "basic Tier 2 exceeds 20% MCR", "INELIGIBLE_ALLOCATION")
    total = math.fsum((t1, t2))
    require(total >= mcr, "allocation", "proposed basic own funds do not cover the MCR",
            "INSUFFICIENT_COVERAGE")
    return total, {"coverage_ratio": total / mcr, "restricted_tier1": restricted,
                   "_sources": _version_sources(context, "DR:article-82", "DIR:article-98-4"),
                   "scope": "proposed_full_coverage_of_preclassified_basic_amounts_only",
                   "classification_and_transferability": "EXTERNAL_INPUT_ONLY"}
