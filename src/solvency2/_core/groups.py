"""Group arithmetic only: consolidation, eligibility and supervisory decisions external."""
import math
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DIR:article-229a:3", unit="indicator")
def group_immaterial_participation_screen_2027(consolidated_assets: float, book_values: Mapping,
                                               *, qualification_reference: str, context: Context):
    """Strict numerical thresholds only, never supervisory permission.

    All relevant holdings and consolidated assets are externally qualified.
    Exact decimal comparisons avoid a rounding tolerance at either boundary.
    """
    _reference(qualification_reference)
    assets = number(consolidated_assets, "consolidated_assets", 0)
    require(assets > 0, "consolidated_assets", "strictly positive consolidated assets required")
    _mapping(book_values, "book_values")
    require(bool(book_values), "book_values", "explicit holdings required", "MISSING_INPUT")
    values = {key: number(value, "book_values." + key, 0) for key, value in book_values.items()}
    individual = number(scalar("group_immaterial_individual_threshold", context), "individual_threshold", 0, 1)
    aggregate = number(scalar("group_immaterial_aggregate_threshold", context), "aggregate_threshold", 0, 1)
    exact_assets = Fraction(str(assets))
    exact_values = {key: Fraction(str(value)) for key, value in values.items()}
    individual_checks = {key: value < exact_assets * Fraction(str(individual))
                         for key, value in exact_values.items()}
    aggregate_check = sum(exact_values.values()) < exact_assets * Fraction(str(aggregate))
    return int(all(individual_checks.values()) and aggregate_check), {
        "consolidated_assets": assets, "book_values": values,
        "individual_threshold": individual, "aggregate_threshold": aggregate,
        "individual_below_threshold": individual_checks, "aggregate_below_threshold": aggregate_check,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "numerical_materiality_thresholds_only_not_supervisory_permission"}


@calculation("DR:article-336b:1-3", "DIR:article-229a:1-2")
def group_simplified_participation_scr_2027(participation_risk: float, *, entity_type: str,
                                           capital_requirement: float | None = None,
                                           approval_reference: str, qualification_reference: str,
                                           context: Context):
    """Externally approved simplified contribution; no extra ownership weighting.

    Article228 entities are outside scope. Third-country capital information
    must be supplied, never replaced with zero when unavailable.
    """
    _reference(qualification_reference)
    require(isinstance(approval_reference, str) and bool(approval_reference.strip()),
            "approval_reference", "external supervisory approval reference required", "MISSING_INPUT")
    require(entity_type in ("eu_insurer", "third_country_insurer", "other"),
            "entity_type", "unsupported simplified-contribution category", "UNSUPPORTED_PARAMETER")
    risk = number(participation_risk, "participation_risk", 0)
    if entity_type == "other":
        require(capital_requirement is None, "capital_requirement", "omit unused capital requirement")
        value, requirement = risk, None
    else:
        require(capital_requirement is not None, "capital_requirement",
                "explicit qualified SCR or local capital requirement required", "MISSING_INPUT")
        requirement = number(capital_requirement, "capital_requirement", 0)
        value = max(risk, requirement)
    return value, {
        "participation_risk": risk, "entity_type": entity_type, "capital_requirement": requirement,
        "approval_reference": approval_reference, "approval_status": "EXTERNAL_UNVERIFIED",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "approved_simplified_contribution_not_scope_or_approval_determination"}



def _reference(reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external group scope/method/eligibility reference required", "MISSING_INPUT")


def _mapping(values, field):
    require(isinstance(values, Mapping), field, "explicit entity mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in values), field, "nonempty entity IDs required")


def _future_rules(context):
    return effective_resource("profile.json", context).get("methods", {}).get("group_rules") == "2027"


@calculation("DIR:article-228:3:a:ii", "DIR:article-228:3:e")
def group_sector_capital_requirement_2027(sector: str, requirements: Mapping, *,
                                          qualification_reference: str, context: Context):
    """Select the prescribed maximum of complete externally calculated branches.

    Bank inputs include applicable buffers/add-ons, not just Pillar1 minima.
    Pension inputs cover both the required margin and national requirement.
    This component implements no CRR, IFR, IORP or third-country valuation.
    """
    _reference(qualification_reference)
    require(isinstance(sector, str) and sector in ("credit_institution", "iorp"),
            "sector", "only credit-institution and IORP maxima supported", "UNSUPPORTED_PARAMETER")
    keys = (("risk_based", "leverage_based") if sector == "credit_institution"
            else ("required_solvency_margin", "national_capital_requirement"))
    exact_keys(requirements, keys, "requirements")
    values = {key: number(requirements[key], key, 0) for key in keys}
    value = max(values.values())
    return value, {"sector": sector, "requirements": values,
                   "binding_branches": [key for key, amount in values.items() if amount == value],
                   "_sources": ["DIR:article-228:3:a:ii" if sector == "credit_institution" else "DIR:article-228:3:e"],
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "sector_requirement_maximum_not_external_sector_capital_model"}


@calculation("DIR:article-221:1a", "DIR:article-228:2-4")
def group_sector_contribution_2027(entities: Mapping, *, measure: str,
                                   qualification_reference: str, context: Context):
    """Sum disjoint qualified sector amounts using subscribed-capital shares.

    Eligible own funds must already reflect Article228 availability exclusions.
    Subgroup inclusion, exclusion of its individual members and supervisory
    decisions are externally qualified. Signed own funds are not floored.
    """
    _reference(qualification_reference)
    require(isinstance(measure, str) and measure in ("eligible_own_funds", "capital_requirement"),
            "measure", "explicit own-funds or capital-requirement measure required", "UNSUPPORTED_PARAMETER")
    _mapping(entities, "entities")
    contributions = {}
    for label, row in entities.items():
        exact_keys(row, ("amount", "share"), label)
        amount = number(row["amount"], label + ".amount", 0 if measure == "capital_requirement" else None)
        share = number(row["share"], label + ".share", 0, 1)
        contributions[label] = amount * share
    try:
        value = math.fsum(contributions.values())
    except OverflowError:
        require(False, "contributions", "sector total not representable", "REVIEW_REQUIRED")
    return value, {"measure": measure, "entity_contributions": contributions,
                   "share_basis": "externally_qualified_direct_indirect_subscribed_capital",
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "sector_contribution_sum_not_eligibility_or_consolidation_determination"}


def _sector_contributions(values, context, *, include_holdings=False):
    """Future-only, already weighted sector amounts; never infer an empty set."""
    if not _future_rules(context):
        require(values is None, "sector_contributions", "sector mapping is only available in the future profile",
                "UNSUPPORTED_PARAMETER")
        return {}
    _mapping(values, "sector_contributions")
    keys = ("eligible_own_funds", "capital_requirement") + (("participation_value",) if include_holdings else ())
    result = {}
    for label, row in values.items():
        exact_keys(row, keys, label)
        result[label] = {key: number(row[key], label + "." + key,
                                    None if key == "eligible_own_funds" else 0) for key in keys}
    return result


@calculation("DIR:article-233a:1-7", "DIR:article-221:1")
def group_combined_component_surplus_2027(consolidated_own_funds: float, consolidated_scr: float,
                                         minimum: float, method2_related: Mapping,
                                         sector_contributions: Mapping,
                                         method2_own_funds_adjustment: float, method2_capital_addon: float, *,
                                         approval_reference: str, qualification_reference: str, context: Context):
    """Compose externally approved disjoint methods, not a consolidation model.

    Consolidated inputs already exclude M2/sector holdings and reflect required
    currency sensitivity. Do not repeat pure-M2 participation-value deductions.
    M2 insurer subsidiary deficits retain Article221 treatment; sector amounts
    are already weighted and availability-adjusted under Article228.
    """
    _reference(qualification_reference)
    require(isinstance(approval_reference, str) and bool(approval_reference.strip()),
            "approval_reference", "external approval for method combination required", "MISSING_INPUT")
    eof = number(consolidated_own_funds, "consolidated_own_funds")
    scr = number(consolidated_scr, "consolidated_scr", 0)
    floor = number(minimum, "minimum", 0)
    adjustment = number(method2_own_funds_adjustment, "method2_own_funds_adjustment")
    addon = number(method2_capital_addon, "method2_capital_addon", 0)
    _mapping(method2_related, "method2_related")
    sectors = _sector_contributions(sector_contributions, context)
    require(not set(method2_related).intersection(sectors), "sector_contributions",
            "entity duplicated in M2 insurance and sector sets")
    rows = {}
    for label, row in method2_related.items():
        exact_keys(row, ("eligible_own_funds", "scr", "share", "is_subsidiary",
                         "proportionate_deficit_approved", "approval_reference"), label)
        required, detail = _shortfall(row["eligible_own_funds"], row["scr"], row["share"],
                                      row["is_subsidiary"], row["proportionate_deficit_approved"], row["approval_reference"])
        rows[label] = {**detail, "required_shortfall": required,
                       "weighted_own_funds": detail["share"] * detail["eligible_own_funds"],
                       "weighted_scr": detail["share"] * detail["scr"]}
    method2_eof = math.fsum(row["weighted_own_funds"] for row in rows.values())
    method2_scr = math.fsum(row["weighted_scr"] for row in rows.values())
    deficit_rest = math.fsum(row["additional_full_deficit"] for row in rows.values())
    sector_eof = math.fsum(row["eligible_own_funds"] for row in sectors.values())
    sector_capital = math.fsum(row["capital_requirement"] for row in sectors.values())
    effective = max(scr, floor)
    value = math.fsum((eof, -effective, method2_eof, -method2_scr, -deficit_rest,
                       adjustment, -addon, sector_eof, -sector_capital))
    return value, {"consolidated_own_funds": eof, "consolidated_scr": scr, "minimum": floor,
                   "effective_consolidated_scr": effective, "method2_related": rows,
                   "method2_own_funds": method2_eof, "method2_scr": method2_scr,
                   "additional_full_deficit_deduction": deficit_rest,
                   "method2_own_funds_adjustment": adjustment, "method2_capital_addon": addon,
                   "sector_contributions": sectors, "sector_own_funds": sector_eof,
                   "sector_capital_requirement": sector_capital,
                   "approval_reference": approval_reference, "approval_status": "EXTERNAL_UNVERIFIED",
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "combined_method_arithmetic_not_consolidation_or_minimum_basic_funds_coverage",
                   "regulatory_total_released": False}


@calculation("DIR:article-233a:3")
def group_combined_currency_exposure_2027(participation_value: float, entity_scr: float, share: float, *,
                                         qualification_reference: str, context: Context):
    """Positive holding excess for external consolidated currency scenarios.

    Amounts use the same qualified currency. This is not a currency charge and
    no equity shock applies to this holding under the cited combined-method rule.
    """
    _reference(qualification_reference)
    holding = number(participation_value, "participation_value", 0)
    scr = number(entity_scr, "entity_scr", 0)
    proportion = number(share, "share", 0, 1)
    weighted = proportion * scr
    return max(holding - weighted, 0), {"participation_value": holding, "entity_scr": scr,
                                       "share": proportion, "proportional_scr": weighted,
                                       "equity_sensitivity_under_this_rule": False,
                                       "qualification_reference": qualification_reference,
                                       "qualification_status": "EXTERNAL_UNVERIFIED",
                                       "scope": "holding_excess_for_external_currency_scenario_not_currency_charge"}


def _related_sum(parent_amount, related, value_key, minimum=None):
    """Shared weighted arithmetic, never shared legal qualification between methods."""
    _mapping(related, "related")
    parent = number(parent_amount, "parent_" + value_key, minimum)
    contributions = {}
    for label, row in related.items():
        exact_keys(row, [value_key, "share"], label)
        contributions[label] = number(row[value_key], label + "." + value_key, minimum) * number(row["share"], label + ".share", 0, 1)
    return math.fsum([parent, *contributions.values()]), parent, contributions


@calculation("DR:article-339:1-3", "DIR:article-221:1:a")
def group_consolidated_best_estimate(parent_best_estimate: float, related: Mapping,
                                     *, qualification_reference: str, context: Context):
    """Sum BE already adjusted externally for all intra-group transactions.

    Method1 Article335(1)a/c scope and consolidation shares are external. The
    receiving reinsurer excludes intra-group fulfilment cashflows; the cedant
    excludes corresponding recoverables. This function does not perform netting.
    """
    _reference(qualification_reference)
    value, parent, contributions = _related_sum(parent_best_estimate, related, "best_estimate")
    return value, {"parent_best_estimate": parent, "related_contributions": contributions,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "method1_pre_adjusted_BE_sum_not_intragroup_netting"}


@calculation("DR:article-340", "DIR:article-221:1:a")
def group_consolidated_risk_margin(parent_risk_margin: float, related: Mapping,
                                   *, qualification_reference: str, context: Context):
    """Proportionate sum of externally qualified risk margins, no added diversification."""
    _reference(qualification_reference)
    value, parent, contributions = _related_sum(parent_risk_margin, related, "risk_margin", 0)
    return value, {"parent_risk_margin": parent, "related_contributions": contributions,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "method1_risk_margin_sum_only_not_runoff_projection"}


@calculation("DR:article-339:1-3", "DIR:article-221:1:a")
def group_reinsurance_elimination(entities: Mapping, transactions: Mapping, *, parent_id: str,
                                   measure: str, other_intragroup_adjustments_complete: bool,
                                   qualification_reference: str, context: Context):
    """Remove qualified internal reinsurance values before consolidation shares.

    Entity gross BE and recoverables must include the supplied disjoint internal
    transactions, but already exclude all OTHER required intragroup adjustments.
    Assumed obligation PV and ceded recoverable need not agree: valuation bases
    and shares can differ. Neither side is inferred from the other or floored.
    This is a two-sided ledger adjustment, not a projection or legal approval.
    """
    _reference(qualification_reference)
    _mapping(entities, "entities")
    _mapping(transactions, "transactions")
    require(isinstance(parent_id, str) and parent_id in entities,
            "parent_id", "explicit parent in the entity scope required", "MISSING_INPUT")
    require(measure in ("best_estimate", "recoverables", "net_best_estimate"),
            "measure", "explicit BE/recoverables/net-BE selection required")
    require(other_intragroup_adjustments_complete is True, "other_intragroup_adjustments_complete",
            "other required adjustments and disjoint nonduplicated ledger scope must be qualified", "REVIEW_REQUIRED")
    rows, removals = {}, {}
    for key, row in entities.items():
        exact_keys(row, ("best_estimate", "recoverables", "share"), "entities." + key)
        rows[key] = {"best_estimate": number(row["best_estimate"], key + ".best_estimate"),
                     "recoverables": number(row["recoverables"], key + ".recoverables"),
                     "share": number(row["share"], key + ".share", 0, 1)}
        removals[key] = {"best_estimate": [], "recoverables": []}
    require(rows[parent_id]["share"] == 1, "parent.share", "parent contributes fully under339(1)a")
    ledger = {}
    for key, row in transactions.items():
        exact_keys(row, ("cedant", "reinsurer", "assumed_best_estimate", "recoverable", "valuation_reference"), key)
        cedant, reinsurer = row["cedant"], row["reinsurer"]
        require(isinstance(cedant, str) and isinstance(reinsurer, str)
                and cedant in rows and reinsurer in rows and cedant != reinsurer,
                key, "distinct counterparties must both belong to the consolidation scope")
        _reference(row["valuation_reference"])
        be = number(row["assumed_best_estimate"], key + ".assumed_best_estimate")
        recovery = number(row["recoverable"], key + ".recoverable")
        removals[reinsurer]["best_estimate"].append(be)
        removals[cedant]["recoverables"].append(recovery)
        ledger[key] = {**row, "assumed_best_estimate": be, "recoverable": recovery}
    adjusted = {}
    for key, row in rows.items():
        removed = {name: math.fsum(values) for name, values in removals[key].items()}
        adjusted[key] = {"share": row["share"], **{
            name: number(math.fsum((row[name], -removed[name])), key + ".adjusted_" + name)
            for name in removed}, "removed": removed}
    # Reuse the original method1 weighting, keeping the parent separate.
    be = group_consolidated_best_estimate(adjusted[parent_id]["best_estimate"],
        {key: {"best_estimate": row["best_estimate"], "share": row["share"]}
         for key, row in adjusted.items() if key != parent_id},
        qualification_reference=qualification_reference, context=context)
    recovery = math.fsum(row["recoverables"] * row["share"] for row in adjusted.values())
    totals = {"best_estimate": be.value, "recoverables": recovery,
              "net_best_estimate": math.fsum((be.value, -recovery))}
    return totals[measure], {"measure": measure, "totals": totals, "entities_before": rows,
        "entities_after": adjusted, "transactions": ledger, "parent_id": parent_id,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "other_intragroup_adjustments_complete": True, "cashflows_projected": False,
        "scope": "qualified_internal_reinsurance_elimination_not_complete_group_solvency",
        "_sources": list(be.sources)}


@calculation("DR:article-336", "DIR:article-232")
def group_consolidated_scr(components: Mapping, capital_addon: float, *, qualification_reference: str,
                           simplified_contributions: Mapping | None = None, context: Context):
    """Sum qualified Article336 amounts plus externally set group add-on.

    Contributions b/c already include proportional shares. Components d/e are
    externally determined risk amounts, not invented sums of individual SCRs.
    From 2027, only a-d belong here; separate Article336b additions must be
    explicit and disjoint from those components. Article228 sector contributions
    are outside this consolidated amount. Their valuation is not inferred.
    Apply the Article230 minimum separately. No sector/Look-through valuation
    or supervisory determination is implemented by this composition function.
    """
    _reference(qualification_reference)
    keys = ("diversified", "related_insurers", "other_financial", "other_participations", "lookthrough_funds")
    additions = {}
    if _future_rules(context):
        keys = ("diversified", "related_insurers", "other_participations", "lookthrough_funds")
        _mapping(simplified_contributions, "simplified_contributions")
        additions = {key: number(value, "simplified_contributions." + key, 0)
                     for key, value in simplified_contributions.items()}
    else:
        require(simplified_contributions is None, "simplified_contributions",
                "Article336b mapping is only available in the future profile", "UNSUPPORTED_PARAMETER")
    exact_keys(components, keys, "components")
    values = {key: number(components[key], key, 0) for key in keys}
    addon = number(capital_addon, "capital_addon", 0)
    return math.fsum([*values.values(), *additions.values(), addon]), {
        "components": values, "capital_addon": addon,
        "simplified_contributions": additions,
        "_sources": ["DR:article-336:a-d", "DR:article-336b"] if _future_rules(context) else ["DR:article-336:a-e"],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "consolidated_SCR_composition_before_group_minimum_not_full_group_valuation",
        "regulatory_total_released": False}


@calculation("DR:article-330:6:a", "DR:article-335:1:a", "DR:article-335:1:c")
def group_standard_scr_contribution(entity: str, share: float, diversified_component: float,
                                    component_scrs: Mapping, *, qualification_reference: str, context: Context):
    """Standard-formula contribution for externally qualified consolidated entities.

    Numerator uses the entity's proportional SCR; denominator is the sum of the
    supplied SCRs, without applying shares a second time. No internal-model
    allocation is inferred. Scaling preserves the formula at large magnitudes.
    """
    _reference(qualification_reference)
    _mapping(component_scrs, "component_scrs")
    require(isinstance(entity, str) and entity in component_scrs, "entity", "selected entity must be in complete component mapping")
    fraction = number(share, "share", 0, 1)
    component = number(diversified_component, "diversified_component", 0)
    values = {key: number(value, key + ".scr", 0) for key, value in component_scrs.items()}
    scale = max(values.values())
    require(scale > 0, "component_scrs", "zero denominator requires review", "REVIEW_REQUIRED")
    scaled_sum = math.fsum(value / scale for value in values.values())
    allocation_weight = fraction * (values[entity] / scale) / scaled_sum
    value = allocation_weight * component
    cap_details = {}
    # Only the future profile owns this rule. Preserve historical arithmetic.
    # Cap the equivalent monetary contribution to avoid overflowing C/sum(SCR)
    # when a very large component meets extremely small standalone SCRs.
    cap_row = effective_resource("profile.json", context)["scalars"].get("group_standard_contribution_ratio_cap")
    if cap_row is not None:
        cap = number(cap_row["value"], "group_standard_contribution_ratio_cap", 0, 1)
        maximum_contribution = fraction * values[entity] * cap
        # An exact comparison of the supplied binary numbers avoids a spurious
        # "cap applied" flag at equality from scaled-sum rounding. No epsilon
        # widens the regulatory threshold and no overflowing float sum is needed.
        cap_applied = Fraction(component) > sum(Fraction(v) for v in values.values()) * Fraction(cap)
        cap_details = {"contribution_ratio_cap": cap, "maximum_contribution": maximum_contribution,
                       "contribution_cap_applied": cap_applied,
                       "_sources": ["DR:article-330:6"]}
        value = min(value, maximum_contribution)
    return value, {
        **cap_details,
        "entity": entity, "share": fraction, "component_scrs": values,
        "diversified_component": component, "denominator_scale": scale,
        "scaled_denominator": scaled_sum, "allocation_weight": allocation_weight,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "standard_formula_contribution_only_not_own_funds_availability"}


@calculation("DR:article-342:2")
def group_method2_best_estimate_sum(parent_best_estimate: float, related: Mapping,
                                   *, qualification_reference: str, context: Context):
    """Parent plus proportionate related BE, preserving signed external valuations.

    Calculate before/after removal of intra-group transactions separately; this
    component does not invent an EOF-adjustment sign or revalue transactions.
    """
    _reference(qualification_reference)
    value, parent, contributions = _related_sum(parent_best_estimate, related, "best_estimate")
    return value, {
        "parent_best_estimate": parent, "related_contributions": contributions,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "weighted_best_estimate_sum_only_not_intragroup_valuation_or_eof_adjustment"}


def _shortfall(eof, scr, share, subsidiary, approved, approval_reference):
    eof, scr, share = number(eof, "eligible_own_funds"), number(scr, "scr", 0), number(share, "share", 0, 1)
    for key, flag in (("is_subsidiary", subsidiary), ("proportionate_deficit_approved", approved)):
        require(flag is None or isinstance(flag, bool), key, "explicit boolean required")
        require(flag is not None, key, "unknown classification/decision", "REVIEW_REQUIRED")
    if approved:
        require(subsidiary, "proportionate_deficit_approved", "exception applies only to subsidiary deficits")
        require(isinstance(approval_reference, str) and bool(approval_reference.strip()), "approval_reference",
                "external supervisory limited-liability decision required", "MISSING_INPUT")
    else:
        require(approval_reference is None, "approval_reference", "omit unused approval reference")
    deficit = max(scr - eof, 0)
    proportional = share * deficit
    required = deficit if subsidiary and not approved else proportional
    return required, {"eligible_own_funds": eof, "scr": scr, "share": share,
                      "is_subsidiary": subsidiary, "proportionate_deficit_approved": approved,
                      "approval_reference": approval_reference, "standalone_shortfall": deficit,
                      "proportional_shortfall": proportional,
                      "additional_full_deficit": required - proportional}


@calculation("DIR:article-221:1-2")
def group_required_shortfall(eligible_own_funds: float, scr: float, share: float,
                             is_subsidiary: bool | None, proportionate_deficit_approved: bool | None,
                             approval_reference: str | None = None, *, qualification_reference: str, context: Context):
    """Full subsidiary deficit unless an explicit externally approved exception applies."""
    _reference(qualification_reference)
    value, details = _shortfall(eligible_own_funds, scr, share, is_subsidiary,
                                proportionate_deficit_approved, approval_reference)
    return value, {**details, "qualification_reference": qualification_reference,
                   "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "required_deficit_component_only"}


@calculation("DIR:article-233:1-4", "DIR:article-221:1", "DIR:article-233:6")
def group_method2_component_surplus(parent_own_funds: float, parent_scr: float, related: Mapping,
                                    own_funds_adjustment: float, capital_addon: float,
                                    *, qualification_reference: str, sector_contributions: Mapping | None = None,
                                    context: Context):
    """Signed method2 aggregation component, not complete approved group solvency.

    Participation values already represent the held direct/indirect investment:
    never apply share twice. External EOF adjustments must not duplicate those
    values or the full-subsidiary-deficit correction calculated here. Group
    availability, tiers, intra-group transactions and scope are not inferred.
    Future Article228 sectors are explicit, already weighted and disjoint;
    their holding values are deducted once, not passed through insurer deficits.
    """
    _reference(qualification_reference)
    _mapping(related, "related")
    sectors = _sector_contributions(sector_contributions, context, include_holdings=True)
    require(not set(related).intersection(sectors), "sector_contributions", "entity duplicated in insurance and sector sets")
    parent_eof = number(parent_own_funds, "parent_own_funds")
    parent_requirement = number(parent_scr, "parent_scr", 0)
    adjustment = number(own_funds_adjustment, "own_funds_adjustment")
    addon = number(capital_addon, "capital_addon", 0)
    rows = {}
    for label, row in related.items():
        exact_keys(row, ["eligible_own_funds", "scr", "share", "participation_value", "is_subsidiary",
                         "proportionate_deficit_approved", "approval_reference"], label)
        required, detail = _shortfall(row["eligible_own_funds"], row["scr"], row["share"],
                                      row["is_subsidiary"], row["proportionate_deficit_approved"], row["approval_reference"])
        holding = number(row["participation_value"], label + ".participation_value", 0)
        rows[label] = {**detail, "participation_value": holding, "required_shortfall": required,
                       "weighted_own_funds": detail["share"] * detail["eligible_own_funds"],
                       "weighted_scr": detail["share"] * detail["scr"]}
    aggregate_eof = math.fsum([parent_eof, *(row["weighted_own_funds"] for row in rows.values())])
    aggregate_scr = math.fsum([parent_requirement, *(row["weighted_scr"] for row in rows.values())])
    holdings = math.fsum(row["participation_value"] for row in rows.values())
    deficit_rest = math.fsum(row["additional_full_deficit"] for row in rows.values())
    sector_eof = math.fsum(row["eligible_own_funds"] for row in sectors.values())
    sector_capital = math.fsum(row["capital_requirement"] for row in sectors.values())
    sector_holdings = math.fsum(row["participation_value"] for row in sectors.values())
    surplus = math.fsum((aggregate_eof, -holdings, -aggregate_scr, adjustment, -addon, -deficit_rest,
                         sector_eof, -sector_capital, -sector_holdings))
    return surplus, {"related": rows, "aggregate_own_funds_before_adjustments": aggregate_eof,
                     "aggregate_scr_before_addon": aggregate_scr, "participation_deduction": holdings,
                     "additional_full_deficit_deduction": deficit_rest,
                     "own_funds_adjustment": adjustment, "capital_addon": addon,
                     "sector_contributions": sectors, "sector_own_funds": sector_eof,
                     "sector_capital_requirement": sector_capital, "sector_participation_deduction": sector_holdings,
                     "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                     "scope": "method2_arithmetic_component_not_complete_group_solvency",
                     "regulatory_total_released": False}


@calculation("DIR:article-230:2", "DIR:article-221")
def group_consolidated_minimum(parent_mcr: float, related: Mapping, *, qualification_reference: str,
                               third_country: Mapping | None = None, context: Context):
    """Qualified MCR sum plus future local licence-withdrawal requirements.

    Future third-country rows are explicit, including an empty mapping. They
    must not duplicate the EU-MCR entity set; legal scope is assessed externally.
    """
    _reference(qualification_reference)
    _mapping(related, "related")
    parent = number(parent_mcr, "parent_mcr", 0)
    contributions = {}
    for label, row in related.items():
        exact_keys(row, ["mcr", "share"], label)
        contributions[label] = number(row["mcr"], label + ".mcr", 0) * number(row["share"], label + ".share", 0, 1)
    local_contributions = {}
    if _future_rules(context):
        _mapping(third_country, "third_country")
        require(not set(related).intersection(third_country), "third_country", "entity duplicated in MCR and local requirement sets")
        for label, row in third_country.items():
            exact_keys(row, ["local_requirement", "share"], label)
            local_contributions[label] = number(row["local_requirement"], label + ".local_requirement", 0) * number(row["share"], label + ".share", 0, 1)
    else:
        require(third_country is None, "third_country", "local requirement mapping is only available in the future profile",
                "UNSUPPORTED_PARAMETER")
    return math.fsum([parent, *contributions.values(), *local_contributions.values()]), {
        "parent_mcr": parent, "related_contributions": contributions,
        "third_country_contributions": local_contributions,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "consolidated_group_minimum_only_not_basic_own_funds_eligibility"}


@calculation("DIR:article-230:1-2")
def group_consolidated_surplus(eligible_own_funds: float, calculated_scr: float, minimum: float,
                               *, qualification_reference: str, sector_contributions: Mapping | None = None,
                               context: Context):
    """External consolidated eligible EOF minus SCR after its qualified minimum.

    This is not consolidation by adding individual SCRs. Input SCR must include
    externally required add-ons; EOF qualification and minimum coverage remain
    externally assessed. A negative surplus is deliberately retained.
    Future Article228 sectors must be excluded from consolidated inputs and
    added separately, after the minimum is applied to consolidated SCR only.
    """
    _reference(qualification_reference)
    eof = number(eligible_own_funds, "eligible_own_funds")
    scr = number(calculated_scr, "calculated_scr", 0)
    floor = number(minimum, "minimum", 0)
    effective = max(scr, floor)
    sectors = _sector_contributions(sector_contributions, context)
    sector_eof = math.fsum(row["eligible_own_funds"] for row in sectors.values())
    sector_capital = math.fsum(row["capital_requirement"] for row in sectors.values())
    return math.fsum((eof, -effective, sector_eof, -sector_capital)), {
                             "eligible_own_funds": eof, "calculated_scr": scr, "minimum": floor,
                             "effective_scr": effective, "minimum_applied": floor > scr,
                             "sector_contributions": sectors, "sector_own_funds": sector_eof,
                             "sector_capital_requirement": sector_capital,
                             "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                             "scope": "consolidated_arithmetic_only_not_consolidation_or_eligibility",
                             "regulatory_total_released": False}
