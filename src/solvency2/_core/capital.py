"""Capital components with source-specific floors and explicit external inputs."""
import math
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DR:article-37:1", "DR:article-39")
def risk_margin(projected_scr: list[float], basic_rates: list[float], runoff_complete: bool, *, context: Context):
    """Discount SCR(t) of the Art.38 reference undertaking at basic rates t+1."""
    require(runoff_complete is True, "runoff_complete", "complete runoff required", "MISSING_INPUT")
    require(isinstance(projected_scr, (list, tuple)) and isinstance(basic_rates, (list, tuple)),
            "projection", "ordered vectors required")
    require(len(projected_scr) == len(basic_rates) and bool(projected_scr), "projection", "equal nonzero lengths required")
    profile = effective_resource("profile.json", context)
    method = profile.get("methods", {}).get("risk_margin")
    require(method in {"UNDAMPED_BASELINE", "TIME_ADJUSTED_2027"}, "risk_margin_method",
            "unimplemented versioned risk-margin method", "UNSUPPORTED_METHOD")
    decay, time_floor = 1.0, 1.0
    if method == "TIME_ADJUSTED_2027":
        decay = number(scalar("risk_margin_time_decay", context), "time_decay", 0, 1)
        time_floor = number(scalar("risk_margin_time_floor", context), "time_floor", 0, 1)
    discounted, factors = [], []
    for t, (scr, rate) in enumerate(zip(projected_scr, basic_rates), 1):
        scr, rate = number(scr, f"scr[{t-1}]", 0), number(rate, f"rate[{t}]")
        require(rate > -1, f"rate[{t}]", "annual rate must exceed -1")
        factor = max(decay ** (t - 1), time_floor)
        factors.append(factor)
        discounted.append(factor * scr / (1 + rate) ** t)
    cost = number(scalar("cost_of_capital", context), "cost_of_capital", 0)
    return cost * math.fsum(discounted), {
        "discounted_scr": discounted, "cost_of_capital": cost,
        "risk_margin_method": method, "time_adjustment_factors": factors,
        "projection_support": "EXTERNAL_INPUT_ONLY",
        "source_profile": context.profile_id,
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":articles-37-39"]}


@calculation("DR:article-203")
def intangible_risk(recognised_value: float, *, context: Context):
    """Charge on intangible value already recognised under Article 12."""
    return number(recognised_value, "recognised_value", 0) * scalar("intangible", context), {}


@calculation("DR:article-204:1-4")
def operational_risk(bscr: float, earned_life: float, earned_life_ul: float,
                     earned_nonlife: float, previous_life: float, previous_life_ul: float,
                     previous_nonlife: float, tp_life: float, tp_life_ul: float,
                     tp_nonlife: float, expenses_ul: float, *, context: Context):
    """Gross premium/provision calculation; provisions exclude the risk margin."""
    bscr, expenses_ul = number(bscr, "bscr", 0), number(expenses_ul, "expenses_ul", 0)
    e, u, n, p, pu, pn = [number(v, k, 0) for k, v in zip(
        ("earned_life", "earned_life_ul", "earned_nonlife", "previous_life", "previous_life_ul", "previous_nonlife"),
        (earned_life, earned_life_ul, earned_nonlife, previous_life, previous_life_ul, previous_nonlife))]
    require(u <= e and pu <= p, "unit_linked_premiums", "subset cannot exceed total premiums")
    t, tu, tn = (number(v, k) for k, v in zip(("tp_life", "tp_life_ul", "tp_nonlife"),
                                             (tp_life, tp_life_ul, tp_nonlife)))
    growth = scalar("op_growth_threshold", context)
    prem = (scalar("op_life_premium", context) * (e - u) + scalar("op_nonlife_premium", context) * n
            + max(0, scalar("op_life_premium", context) * ((e - u) - growth * (p - pu)))
            + max(0, scalar("op_nonlife_premium", context) * (n - growth * pn)))
    prov = scalar("op_life_tp", context) * max(0, t - tu) + scalar("op_nonlife_tp", context) * max(0, tn)
    base = max(prem, prov)
    return min(scalar("op_cap", context) * bscr, base) + scalar("op_ul_expense", context) * expenses_ul, {
        "premium_charge": prem, "provision_charge": prov, "basic_charge": base,
        "cap": scalar("op_cap", context) * bscr,
        "unit_linked_addition": scalar("op_ul_expense", context) * expenses_ul}


@calculation("DR:article-206:1")
def lac_tp(bscr: float, net_bscr: float, future_discretionary_benefits: float, *, context: Context):
    """Signed (nonpositive) loss-absorbing adjustment for technical provisions."""
    gross, net, fdb = (number(v, k, 0) for k, v in zip(("bscr", "net_bscr", "fdb"),
                                                     (bscr, net_bscr, future_discretionary_benefits)))
    return -max(min(gross - net, fdb), 0), {"unbounded_difference": gross - net, "fdb_cap": fdb}


def _pre_tax_stress(bscr, operational, adjustment_tp):
    gross = number(bscr, "bscr", 0)
    op = number(operational, "operational", 0)
    tp = number(adjustment_tp, "adjustment_tp", -gross, 0)
    return math.fsum((gross, op, tp)), {"bscr": gross, "operational": op, "adjustment_tp": tp}


@calculation("DR:article-207:1")
def lac_dt_stress_amount(bscr: float, operational: float, adjustment_tp: float, *, context: Context):
    """Loss for the external tax revaluation, before (not after) the tax adjustment."""
    amount, components = _pre_tax_stress(bscr, operational, adjustment_tp)
    return amount, {**components, "tax_revaluation": "EXTERNAL_INPUT_ONLY"}


@calculation("DR:article-207:2-4", "DR:article-15")
def lac_dt(base_dta: float, base_dtl: float, stressed_dta: float, stressed_dtl: float, *,
           recoverability_reference: str | None = None, context: Context):
    """Signed tax adjustment from externally valued balances after the Article 207(1) loss.

    A nonempty evidence reference records the caller's basis for increased DTA;
    it does not substantively establish future profits or legal recoverability.
    """
    dta, dtl, post_dta, post_dtl = (number(value, key, 0) for key, value in (
        ("base_dta", base_dta), ("base_dtl", base_dtl),
        ("stressed_dta", stressed_dta), ("stressed_dtl", stressed_dtl)))
    if recoverability_reference is not None:
        require(isinstance(recoverability_reference, str) and bool(recoverability_reference.strip()),
                "recoverability_reference", "nonempty external evidence reference required")
    require(post_dta <= dta or recoverability_reference is not None, "recoverability_reference",
            "increased deferred tax assets require recoverability evidence", "MISSING_INPUT")
    change_dta, change_dtl = post_dta - dta, post_dtl - dtl
    raw = change_dtl - change_dta
    return min(raw, 0), {"change_dta": change_dta, "change_dtl": change_dtl,
                         "unfloored_adjustment": raw, "positive_adjustment_zeroed": raw > 0,
                         "recoverability_reference": recoverability_reference,
                         "recoverability_status": "EXTERNAL_UNVERIFIED" if post_dta > dta
                         else "NO_DTA_INCREASE", "scope": "externally_valued_tax_balances"}


@calculation("DR:article-279", "DR:article-282", "DR:article-284")
def capital_add_on_amount(base_scr: float, modified_scr: float, *, method: str,
                          qualification_reference: str, context: Context,
                          base_eligible_own_funds: float | None = None,
                          modified_eligible_own_funds: float | None = None,
                          rebuttal_established: bool | None = None):
    """Prescribed add-on arithmetic, not a supervisory imposition or risk model.

    SCR inputs exclude prior/concurrent add-ons. Modified valuations and any
    permitted offsetting under283(7) are externally qualified. Article279's
    risk-profile significance thresholds are separate from imposing an add-on.
    No quantitative governance/additional2027 Article37(1)e formula is invented.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external modified/base valuation qualification required", "MISSING_INPUT")
    require(isinstance(method, str) and method in {"risk_profile", "ltg"}, "method", "prescribed risk_profile or ltg formula required",
            "UNSUPPORTED_METHOD")
    base = number(base_scr, "base_scr", 0)
    modified = number(modified_scr, "modified_scr", 0)
    difference = Fraction(str(modified)) - Fraction(str(base))
    details = {"base_scr_without_addons": base, "modified_scr_without_addons": modified,
               "method": method, "qualification_reference": qualification_reference,
               "qualification_status": "EXTERNAL_UNVERIFIED", "supervisory_addon_imposed": False,
               "scope": "prescribed_formula_component_not_supervisory_decision"}
    if method == "risk_profile":
        require(base_eligible_own_funds is None and modified_eligible_own_funds is None,
                "eligible_own_funds", "own-fund inputs unused in Article282")
        require(rebuttal_established is None or isinstance(rebuttal_established, bool),
                "rebuttal_established", "explicit boolean or unresolved None required")
        lower = number(scalar("capital_addon_rebuttable_threshold", context), "rebuttable_threshold", 0)
        upper = number(scalar("capital_addon_mandatory_threshold", context), "mandatory_threshold", 0)
        require(upper >= lower, "thresholds", "mandatory threshold below rebuttable threshold")
        significance = "NO_THRESHOLD_PRESUMPTION"
        if base == 0:
            significance = "ZERO_BASE_REQUIRES_SUPERVISORY_ASSESSMENT"
        elif difference >= Fraction(str(upper)) * Fraction(str(base)):
            significance = "SIGNIFICANT_MANDATORY"
        elif difference >= Fraction(str(lower)) * Fraction(str(base)):
            significance = ("PRESUMPTION_REBUTTED" if rebuttal_established is True else
                            "SIGNIFICANT_PRESUMED" if rebuttal_established is False else
                            "PRESUMPTION_REBUTTAL_NOT_ASSESSED")
        details.update(significance=significance, rebuttal_established=rebuttal_established,
                       rebuttable_threshold=lower, mandatory_threshold=upper)
    else:
        require(rebuttal_established is None, "rebuttal_established", "Article279 threshold unused for Article284")
        original_funds = number(base_eligible_own_funds, "base_eligible_own_funds")
        modified_funds = number(modified_eligible_own_funds, "modified_eligible_own_funds")
        difference += Fraction(str(original_funds)) - Fraction(str(modified_funds))
        details.update(base_eligible_own_funds=original_funds, modified_eligible_own_funds=modified_funds,
                       significance="ARTICLE279_NOT_APPLICABLE")
    require(difference >= 0, "capital_addon", "negative add-on requires review; no silent zero floor", "REVIEW_REQUIRED")
    try:
        value = float(difference)
    except OverflowError:
        require(False, "capital_addon", "add-on not representable", "REVIEW_REQUIRED")
    return value, details


@calculation("DIR:article-103", "DR:article-205")
def scr_standard_formula(bscr: float, operational: float, adjustment_tp: float,
                          adjustment_dt: float, *, context: Context,
                          capital_addons: Mapping | None = None, purpose: str = "scr"):
    """Compose standard formula and explicit imposed add-ons, not a full release.

    Inputs exclude these add-ons already. For the risk_margin view only the
    governance Article37(1)c add-on is removed by37(5); all reference-undertaking
    selection underDR38 remains external, not inferred from this view switch.
    """
    require(isinstance(purpose, str) and purpose in {"scr", "risk_margin"}, "purpose", "scr or risk_margin view required")
    before_tax, components = _pre_tax_stress(bscr, operational, adjustment_tp)
    tax = number(adjustment_dt, "adjustment_dt", maximum=0)
    total = math.fsum((before_tax, tax))
    require(total >= 0, "scr", "negative total requires review of supplied components", "REVIEW_REQUIRED")
    require(capital_addons is None or isinstance(capital_addons, Mapping), "capital_addons", "labelled imposed add-ons required")
    addons, audit = [], {}
    allowed = {"a", "b", "c", "d"}
    if context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1":
        allowed.add("e")
    for identifier, row in (capital_addons or {}).items():
        require(isinstance(identifier, str) and bool(identifier.strip()), "capital_addons", "nonempty decision ID required")
        exact_keys(row, ("amount", "article37_reason", "decision_reference"), identifier)
        amount = number(row["amount"], identifier + ".amount", 0)
        reason = row["article37_reason"]
        require(isinstance(reason, str) and reason in allowed, identifier + ".article37_reason",
                "unavailable Article37 reason for profile", "UNSUPPORTED_METHOD")
        reference = row["decision_reference"]
        require(isinstance(reference, str) and bool(reference.strip()), identifier + ".decision_reference",
                "external imposed add-on decision reference required", "MISSING_INPUT")
        included = purpose != "risk_margin" or reason != "c"
        if included:
            addons.append(amount)
        audit[identifier] = {**row, "included": included,
                             "exclusion_reason": None if included else "ARTICLE37_5_GOVERNANCE_RISK_MARGIN"}
    addon_total = number(math.fsum(addons), "capital_addon_total", 0)
    value = number(math.fsum((total, addon_total)), "scr_with_addons", 0)
    return value, {**components, "adjustment_dt": tax, "loss_before_tax_adjustment": before_tax,
                   "combined_adjustment": components["adjustment_tp"] + tax,
                   "scr_before_addons": total, "capital_addon_total": addon_total, "capital_addons": audit,
                   "purpose": purpose, "scope": "component_composition_only", "regulatory_total_released": False,
                   "_sources": ["DIR:article-37:5"] if capital_addons else []}


@calculation("DIR:article-129:1:d", unit="EUR")
def mcr_absolute_floor(undertaking_type: str, covers_nonlife_classes_10_to_15: bool | None = None,
                       *, context: Context, third_country_branch: bool = False,
                       qualification_reference: str | None = None,
                       mixed_premiums: Mapping | None = None):
    """Select a printed EUR floor, including qualified Article166 direct branches.

    The half-floor is not a half-SCR or half-MCR multiplier. Pass it as the
    absolute floor into the ordinary branch-activity MCR calculation. Deposit,
    asset location, authorisation and Article167 relief remain separate.
    """
    require(context.currency == "EUR", "currency", "printed EUR floors need an explicit conversion",
            "UNSUPPORTED_CURRENCY")
    require(isinstance(undertaking_type, str), "undertaking_type", "undertaking class string required")
    require(isinstance(third_country_branch, bool), "third_country_branch", "explicit boolean required")
    if undertaking_type == "mixed" and not third_country_branch:
        require(mixed_premiums is not None, "mixed_premiums",
                "qualified Article73(2)(a/b) premiums required", "REVIEW_REQUIRED")
        require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
                "qualification_reference", "Article73(2)(a/b) authorisation qualification required", "MISSING_INPUT")
        require(covers_nonlife_classes_10_to_15 is None, "covers_nonlife_classes_10_to_15",
                "mixed route concerns qualified classes1/2, not an unrestricted composite licence")
        exact_keys(mixed_premiums, ("nonlife_1_2", "life", "total"), "mixed_premiums")
        premiums = {key: number(value, "mixed_premiums." + key, 0) for key, value in mixed_premiums.items()}
        total = premiums["total"]
        require(total > 0, "mixed_premiums.total", "zero total requires review", "REVIEW_REQUIRED")
        require(premiums["nonlife_1_2"] <= total and premiums["life"] <= total
                and premiums["nonlife_1_2"] / total + premiums["life"] / total <= 1 + 1e-12,
                "mixed_premiums", "component premiums must not exceed total")
        threshold = number(scalar("mcr_mixed_minor_premium_fraction", context), "minor_premium_fraction", 0, 1)
        require(premiums["life"] / total > threshold, "mixed_premiums.life",
                "Article253(3) printed cross-reference remains a source issue", "REVIEW_REQUIRED")
        minor_nonlife = premiums["nonlife_1_2"] / total <= threshold
        life_floor = number(scalar("mcr_amcr_life", context), "life_floor", 0)
        nonlife_floor = number(scalar("mcr_amcr_nonlife_standard", context), "nonlife_floor", 0)
        return life_floor if minor_nonlife else math.fsum((life_floor, nonlife_floor)), {
            "mixed_art_253": "PARAGRAPH2" if minor_nonlife else "PARAGRAPH1",
            "premiums": premiums, "minor_premium_fraction": threshold,
            "life_floor": life_floor, "nonlife_floor": nonlife_floor,
            "qualification_reference": qualification_reference,
            "undertaking_classification": "EXTERNAL_INPUT_ONLY",
            "legal_applicability_and_indexation": "PENDING",
            "third_country_branch": False, "paragraph3_source_issue_resolved": False,
            "_sources": ["DR:article-253:1-2", "DIR:article-73:2:a-b"]}
    require(mixed_premiums is None, "mixed_premiums", "unused outside qualified mixed route")
    if third_country_branch:
        require(undertaking_type in ("life", "nonlife"), "undertaking_type",
                "Article166 route requires a qualified direct-insurance branch", "UNSUPPORTED_METHOD")
        require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
                "qualification_reference", "branch activity and Article166 qualification required", "MISSING_INPUT")
    else:
        require(qualification_reference is None, "qualification_reference", "unused without branch route")
    require(undertaking_type != "mixed", "undertaking_type",
            "mixed/Art.73 and Art.253 cases require separate review", "REVIEW_REQUIRED")
    keys = {"life": "mcr_amcr_life", "reinsurance": "mcr_amcr_reinsurance",
            "captive_reinsurance": "mcr_amcr_captive_reinsurance"}
    if undertaking_type == "nonlife":
        require(isinstance(covers_nonlife_classes_10_to_15, bool),
                "covers_nonlife_classes_10_to_15", "explicit branch-10-to-15 assessment required",
                "MISSING_INPUT" if covers_nonlife_classes_10_to_15 is None else "INVALID_INPUT")
        key = ("mcr_amcr_nonlife_classes_10_to_15" if covers_nonlife_classes_10_to_15
               else "mcr_amcr_nonlife_standard")
    else:
        require(undertaking_type in keys, "undertaking_type", "unsupported undertaking class")
        require(covers_nonlife_classes_10_to_15 is None, "covers_nonlife_classes_10_to_15",
                "nonlife branch flag applies only to nonlife undertakings")
        key = keys[undertaking_type]
    amount = number(scalar(key, context), key, 0)
    fraction = number(scalar("mcr_branch_floor_fraction", context), "mcr_branch_floor_fraction", 0, 1) if third_country_branch else 1
    return amount * fraction, {
        "undertaking_classification": "EXTERNAL_INPUT_ONLY", "selected_parameter": key,
        "legal_applicability_and_indexation": "PENDING", "mixed_art_253": "NOT_COVERED",
        "third_country_branch": third_country_branch, "unadjusted_floor": amount,
        "branch_floor_fraction": fraction, "qualification_reference": qualification_reference,
        "deposit_and_asset_location_assessed": False,
        "_sources": ["DIR:article-166:1-4"] if third_country_branch else []}


@calculation("DR:article-248")
def mcr_combined(linear: float, scr: float, absolute_floor: float, *, context: Context):
    """Combined MCR including an explicitly supplied applicable absolute floor."""
    linear, scr, floor = number(linear, "linear"), number(scr, "scr", 0), number(absolute_floor, "absolute_floor", 0)
    lower = number(scalar("mcr_floor", context), "floor_fraction", 0, 1)
    upper = number(scalar("mcr_cap", context), "cap_fraction", 0, 1)
    require(lower <= upper, "bounds", "floor fraction must not exceed cap fraction")
    combined = min(max(linear, lower * scr), upper * scr)
    return max(combined, floor), {"combined_before_absolute_floor": combined,
                                 "absolute_floor_support": "EXTERNAL_INPUT_ONLY"}


@calculation("DR:article-252:6:11")
def mcr_notional_scr(nonlife_linear: float, life_linear: float, scr_excluding_addon: float,
                      activity: str, *, qualification_reference: str, context: Context):
    """Allocate SCR excluding add-ons by the two notional linear MCR components.

    Signed linear components are not silently floored. A zero denominator has
    no specified allocation here and requires review. Supervisory add-ons are
    allocated separately by the supervisor, not by this ratio.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external activity/input qualification required", "MISSING_INPUT")
    require(isinstance(activity, str) and activity in {"nonlife", "life"}, "activity", "nonlife or life required")
    nonlife, life = number(nonlife_linear, "nonlife_linear"), number(life_linear, "life_linear")
    scr = number(scr_excluding_addon, "scr_excluding_addon", 0)
    scale = max(abs(nonlife), abs(life))
    require(scale > 0, "linear_denominator", "zero denominator requires external review", "REVIEW_REQUIRED")
    denominator = math.fsum([nonlife / scale, life / scale])
    require(denominator != 0, "linear_denominator", "zero denominator requires external review", "REVIEW_REQUIRED")
    selected = nonlife if activity == "nonlife" else life
    share = number((selected / scale) / denominator, "allocation_ratio")
    return share * scr, {
        "activity": activity, "nonlife_linear": nonlife, "life_linear": life,
        "allocation_ratio": share, "scr_excluding_addon": scr,
        "signed_linear_inputs": nonlife < 0 or life < 0,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "notional_scr_allocation_only_not_activity_classification_or_addon_allocation"}


@calculation("DR:article-252:2:3:7:8")
def mcr_notional_requirement(linear: float, notional_scr: float, capital_addon: float,
                             absolute_floor: float, *, qualification_reference: str, context: Context):
    """Notional activity MCR with a separately supervisor-assigned add-on.

    Preserve the printed min(max(...),...) ordering even for signed inputs.
    The applicable absolute floor and activity delimitation remain external.
    This is not a total-company MCR or an automatic Article253 decision.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external activity/input qualification required", "MISSING_INPUT")
    linear, scr = number(linear, "linear"), number(notional_scr, "notional_scr")
    addon = number(capital_addon, "capital_addon", 0)
    absolute = number(absolute_floor, "absolute_floor", 0)
    floor = number(scalar("mcr_notional_floor", context), "floor_fraction", 0, 1)
    cap = number(scalar("mcr_notional_cap", context), "cap_fraction", 0, 1)
    require(floor <= cap, "bounds", "floor fraction must not exceed cap fraction")
    base = number(math.fsum([scr, addon]), "scr_including_assigned_addon")
    lower, upper = floor * base, cap * base
    combined = min(max(linear, lower), upper)
    return max(combined, absolute), {
        "linear": linear, "notional_scr": scr, "capital_addon": addon,
        "scr_including_assigned_addon": base, "floor_fraction": floor, "cap_fraction": cap,
        "lower_formula_term": lower, "upper_formula_term": upper,
        "combined_before_absolute_floor": combined, "absolute_floor": absolute,
        "signed_inputs": linear < 0 or scr < 0,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "notional_activity_mcr_not_total_company_mcr", "regulatory_total_released": False}


@calculation("DR:article-249")
def mcr_linear(nonlife: float, life: float, *, context: Context):
    """Add the separately determined Art.250/251 parts; life may be signed."""
    nonlife = number(nonlife, "nonlife", 0)
    life = number(life, "life")
    return math.fsum((nonlife, life)), {
        "nonlife_component": nonlife, "life_component": life,
        "component_derivation_required": "DR:articles-250-251",
    }


def _contract_capital_at_risk(contracts: Mapping, *, qualification_reference: str):
    """Sum individually floored contract differences, never net across contracts.

    Current benefits and the PV of additional future benefits are independently
    valued for immediate death/disability, net of qualified recoveries. Future
    benefits exclude amounts already counted in current benefits. Signed net
    amounts, including negative best estimates, are not prematurely clipped.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external contract valuation/qualification required", "MISSING_INPUT")
    require(isinstance(contracts, Mapping), "contracts", "explicit contract mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in contracts),
            "contracts", "nonempty string contract IDs required")
    fields = ["net_current_benefits", "net_future_benefits_pv", "net_best_estimate"]
    differences, amounts = {}, {}
    for identifier, row in contracts.items():
        exact_keys(row, fields, identifier)
        current, future, best_estimate = [number(row[key], identifier + "." + key) for key in fields]
        difference = number(math.fsum((current, future, -best_estimate)), identifier + ".difference")
        differences[identifier] = difference
        amounts[identifier] = max(0, difference)
    return math.fsum(amounts.values()), {
        "contract_differences": differences, "contract_capital_at_risk": amounts,
        "empty_population": not bool(contracts), "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "mcr_capital_at_risk_only_not_benefit_valuation_or_coverage_classification"}


@calculation("DR:article-251:1:e")
def mcr_capital_at_risk(contracts: Mapping, *, qualification_reference: str, context: Context):
    """Article251 contract-level floors; external benefit/BE qualification unchanged."""
    return _contract_capital_at_risk(contracts, qualification_reference=qualification_reference)


@calculation("DR:article-251:1")
def mcr_life(components: Mapping[str, float], *, context: Context):
    """Linear life MCR; no premature floor on the signed linear total."""
    rows = effective_resource("profile.json", context)["tables"]["mcr_life"]["rows"]
    exact_keys(components, [row[0] for row in rows], "components")
    terms = {key: max(0, number(components[key], key)) * factor for key, factor in rows}
    return math.fsum(terms.values()), {"terms": terms}


@calculation("DR:article-250:1", "DR:annex-XIX")
def mcr_nonlife(segments: Mapping[str, dict], *, context: Context):
    """Linear nonlife/health MCR using all 16 annex-XIX segments, including explicit zeros."""
    rows = effective_resource("profile.json", context)["tables"]["mcr_nonlife"]["rows"]
    exact_keys(segments, [row[0] for row in rows], "segments")
    terms = {}
    for key, alpha, beta in rows:
        exact_keys(segments[key], ["technical_provisions", "written_premiums"], key)
        tp = max(number(segments[key]["technical_provisions"], f"{key}.tp"), 0)
        premium = max(number(segments[key]["written_premiums"], f"{key}.premiums"), 0)
        terms[key] = alpha * tp + beta * premium
    return math.fsum(terms.values()), {"terms": terms}
