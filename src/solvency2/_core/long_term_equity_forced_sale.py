"""Article171c arithmetic on insurer-supplied, explicitly qualified projections.

Annual projection timing, title eligibility, prudent estimates and appropriate
solvency margin are external. Cash is allocated only once, not manufactured by
recounting initial cash or automatically recycling prior annual surpluses.
"""
import math

from .aggregation import quadratic
from .core import effective_resource, exact_keys, number, require
from .long_term_equity_future import _parameter
from .loss_given_default import _known_flag, _reference


def _history_income(record, insurance, context):
    exact_keys(record, ("amount", "history"), "history_income")
    amount = number(record["amount"], "amount", 0)
    if amount == 0 and record["history"] is None:
        return 0, None  # Electing not to count the flow needs no made-up history.
    history = record["history"]
    horizon = _parameter("history_years", context)
    require(isinstance(history, list) and 0 < len(history) <= horizon, "history",
            "chronological annual observations, at most source horizon")
    values = [number(v, "history", 0) for v in history]
    if len(values) < horizon:
        require(insurance, "history", "asset income needs the complete historical average", "REVIEW_REQUIRED")
        limit = values[-1]
    else:
        limit = math.fsum(v / len(values) for v in values)
    require(amount <= limit, "amount", "projected income exceeds source historical limit", "REVIEW_REQUIRED")
    return amount, limit


def _capital(record, later, profile):
    fields = ("market", "default", "life", "health_slt", "health_nslt", "health_catastrophe",
              "nonlife", "other_module_charges", "loss_absorption_tp", "loss_absorption_dt",
              "preceding_asset_decline_fraction")
    exact_keys(record, fields, "capital_stress")
    matrices = profile["matrices"]
    decline = number(record["preceding_asset_decline_fraction"], "preceding_asset_decline_fraction", 0, 1)
    require(later or decline == 0, "preceding_asset_decline_fraction", "no later-year reduction in first year")
    modules, audit = {}, {}
    for name in ("life", "health_slt", "health_nslt", "nonlife"):
        matrix = matrices[name]
        exact_keys(record[name], matrix["labels"], name)
        values = {k: number(v, name + "." + k, 0) for k, v in record[name].items()}
        if later:
            for excluded in ("catastrophe", "lapse"):
                if excluded in values:
                    values[excluded] = 0
        modules[name], _ = quadratic(values, matrix)
        audit[name] = values
    health_cat = number(record["health_catastrophe"], "health_catastrophe", 0)
    health, _ = quadratic({"slt": modules["health_slt"], "nslt": modules["health_nslt"],
                           "catastrophe": 0 if later else health_cat}, matrices["health"])
    major = {"market": number(record["market"], "market", 0) * (1 - decline),
             "default": number(record["default"], "default", 0) * (1 - decline),
             "life": modules["life"], "health": health, "nonlife": modules["nonlife"]}
    aggregated, _ = quadratic(major, matrices["bscr"])
    # The qualification reference fixes the ChapterV perimeter of charges
    # outside the five correlated modules; do not silently include/exclude them.
    exact_keys(record["other_module_charges"], ("operational", "intangible"), "other_module_charges")
    other = math.fsum(number(v, k, 0) for k, v in record["other_module_charges"].items())
    deductions = math.fsum(number(record[k], k, 0) for k in ("loss_absorption_tp", "loss_absorption_dt"))
    additional = number(aggregated + other - deductions, "additional_stress_outflow")
    require(additional >= 0, "loss_absorption", "deductions exceed qualified capital perimeter", "REVIEW_REQUIRED")
    return additional, {"modules": major, "underwriting_after_exclusions": audit,
        "correlated_aggregate": aggregated, "other_module_charges": other,
        "loss_absorption_deductions": deductions, "additional_outflow": additional}


def _outflows(values, later_stress, profile, context):
    keys = ("life", "nonlife", "health_nslt", "nonlife_other", "financial", "pension",
            "shareholder_distributions", "own_fund_redemptions", "other_including_contingent")
    exact_keys(values, keys, "outflows")
    amounts = [number(values[k], k, 0) for k in keys if k not in ("nonlife", "health_nslt")]
    segment_audit = {}
    multiplier = _parameter("flow_sigma_multiplier", context) if later_stress else 0
    for kind, table in (("nonlife", "nonlife_segments"), ("health_nslt", "health_segments")):
        rows = profile["tables"][table]["rows"]
        exact_keys(values[kind], [r[0] for r in rows], kind)
        segment_audit[kind] = {}
        for segment, premium_sigma, reserve_sigma in rows:
            flow = values[kind][segment]
            exact_keys(flow, ("first_coverage_year", "later_coverage_years"), kind + "." + segment)
            early = number(flow["first_coverage_year"], "first_coverage_year", 0)
            late = number(flow["later_coverage_years"], "later_coverage_years", 0)
            # Literal AnnexII/XIV sigmas, not NP/ADC/HRES/USP adjustments.
            total = early * (1 + multiplier * number(premium_sigma, "premium_sigma", 0)) + late * (
                1 + multiplier * number(reserve_sigma, "reserve_sigma", 0))
            amounts.append(total)
            segment_audit[kind][segment] = total
    return number(math.fsum(amounts), "outflows", 0), segment_audit


def _inflows(values, context):
    keys = ("asset_sales_direct_or_controlled", "asset_sales_other_funds", "maturity_and_contractual_income",
            "noncontractual_asset_income", "life_within_boundary", "life_outside_boundary",
            "life_accepted_reinsurance", "nonlife_within_boundary", "nonlife_outside_boundary",
            "nonlife_accepted_reinsurance")
    exact_keys(values, keys, "inflows")
    historical = ("noncontractual_asset_income", "life_outside_boundary", "nonlife_outside_boundary")
    amounts = [number(values[k], k, 0) for k in keys if k not in historical]
    limits = {}
    for key in historical:
        amount, limits[key] = _history_income(values[key], key != "noncontractual_asset_income", context)
        amounts.append(amount)
    return number(math.fsum(amounts), "inflows", 0), limits


def forced_sale_qualification(inputs, context):
    fields = ("initial_cash", "cash_allocations", "other_fund_asset_value_eur", "assumptions",
              "projection_reference", "capital_perimeter_reference", "cash_allocation_reference",
              "baseline", "stressed", "capital_stress")
    exact_keys(inputs, fields, "avoidance_inputs")
    for key in ("projection_reference", "capital_perimeter_reference", "cash_allocation_reference"):
        _reference(inputs[key], key)
    assumptions = ("risk_tolerance_complied", "appropriate_scr_margin_without_transitions",
        "medium_term_capital_plan_considered", "baseline_markets_unchanged",
        "policy_and_article23_consistent", "negative_outlooks_reflected",
        "eligible_sales_and_control_rights_qualified", "matching_adjustment_assets_excluded",
        "va_sales_conditions_if_applicable", "all_outflow_categories_complete",
        "life_and_slt_lapse_consistent", "nonlife_and_nslt_lapse_consistent",
        "financial_outflows_and_past_practices_consistent", "contingent_and_off_balance_triggered",
        "reinvestment_rfr_va_and_stress_curve_consistent", "within_year_liquidity_sufficient",
        "no_double_counting_cash_sales_and_reinvestment", "capital_perimeter_and_decline_basis_qualified")
    exact_keys(inputs["assumptions"], assumptions, "assumptions")
    require(all([_known_flag(inputs["assumptions"][k], k) for k in assumptions]), "assumptions",
            "material171c projection assumptions unresolved or unmet", "REVIEW_REQUIRED")
    horizon = _parameter("projection_years", context)
    require(horizon == int(horizon) and horizon > 0, "projection_years", "positive integer required")
    years = [str(i) for i in range(1, int(horizon) + 1)]
    for key in ("baseline", "stressed", "capital_stress"):
        exact_keys(inputs[key], years, key)
    initial_cash = number(inputs["initial_cash"], "initial_cash", 0)
    exact_keys(inputs["cash_allocations"], ("baseline", "stressed"), "cash_allocations")
    allocations = {}
    for scenario in ("baseline", "stressed"):
        exact_keys(inputs["cash_allocations"][scenario], years, "cash_allocations." + scenario)
        allocations[scenario] = {year: number(inputs["cash_allocations"][scenario][year], "cash_allocation", 0)
                                 for year in years}
        require(math.fsum(allocations[scenario].values()) <= initial_cash, "cash_allocations",
                "reference-date cash cannot be counted repeatedly within a scenario", "REVIEW_REQUIRED")
    funds = number(inputs["other_fund_asset_value_eur"], "other_fund_asset_value_eur", 0)
    require(funds <= _parameter("forced_sale_fund_cap_eur", context), "other_fund_asset_value_eur",
            "non-controlled fund assets exceed source cap", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    capital = {year: _capital(inputs["capital_stress"][year], year != "1", profile) for year in years}
    result = {}
    for scenario in ("baseline", "stressed"):
        annual = {}
        for year in years:
            row = inputs[scenario][year]
            exact_keys(row, ("inflows", "outflows", "reinvestment"), scenario + "." + year)
            incoming, history_limits = _inflows(row["inflows"], context)
            outgoing, segment_audit = _outflows(row["outflows"], scenario == "stressed" and year != "1", profile, context)
            reinvestment = row["reinvestment"]
            income = 0
            if reinvestment is not None:
                exact_keys(reinvestment, ("principal", "accumulation_factor", "valuation_reference"), "reinvestment")
                _reference(reinvestment["valuation_reference"], "reinvestment.valuation_reference")
                principal = number(reinvestment["principal"], "reinvestment.principal", 0)
                require(principal <= max(incoming - outgoing, 0), "reinvestment.principal",
                        "principal exceeds qualified171c(3)a-d inflows less(4)outflows", "REVIEW_REQUIRED")
                factor = number(reinvestment["accumulation_factor"], "reinvestment.accumulation_factor", 0)
                income = number(principal * (factor - 1), "reinvestment_income")
            additional = capital[year][0] if scenario == "stressed" else 0
            surplus = number(math.fsum((allocations[scenario][year], incoming, income, -outgoing, -additional)), "annual_surplus")
            annual[year] = {"inflows_without_initial_cash": incoming, "allocated_initial_cash": allocations[scenario][year],
                "reinvestment_income": income, "ordinary_outflows": outgoing, "additional_capital_outflow": additional,
                "surplus": surplus, "passes": surplus > 0, "history_limits": history_limits,
                "segment_outflows": segment_audit}
        result[scenario] = annual
    passed = all(row["passes"] for scenario in result.values() for row in scenario.values())
    return passed, {"annual": result, "capital": {year: capital[year][1] for year in years},
        "initial_cash_used": {s: math.fsum(a.values()) for s, a in allocations.items()}, "automatic_surplus_carry_forward": False,
        "projection_and_within_year_liquidity_verified": False,
        "scope": "source_arithmetic_on_qualified_annual_projections_not_an_insurer_projection_model"}
