"""Article168a arithmetic on explicitly qualified formula units and issuer inputs."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .loss_given_default import _known_flag, _reference


def _fraction(value):
    return Fraction(str(value))


def _finite(value, field):
    try:
        result = float(value)
    except OverflowError:
        require(False, field, "unlisted-equity result outside finite range", "REVIEW_REQUIRED")
    require(result != 0 or value == 0, field, "nonzero result underflows", "REVIEW_REQUIRED")
    return result


def _parameters(context):
    profile = effective_resource("profile.json", context)
    names = ("beta_intercept", "beta_gm_coefficient", "beta_leverage_coefficient",
             "beta_return_coefficient", "mean_history_years", "size_history_years",
             "revenue_currency_min", "employee_share_min", "turnover_min",
             "balance_sheet_min", "employees_min", "investment_share_max", "portfolio_beta_max")
    values = {name: number(profile["scalars"]["unlisted_equity_" + name]["value"], name)
              for name in names}
    for name in ("mean_history_years", "size_history_years"):
        require(values[name] >= 1 and values[name].is_integer(), name,
                "positive whole financial-year count required", "RESOURCE_INTEGRITY")
    for name in ("revenue_currency_min", "employee_share_min", "investment_share_max"):
        require(0 <= values[name] <= 1, name, "profile share must lie in[0,1]", "RESOURCE_INTEGRITY")
    for name in ("turnover_min", "balance_sheet_min", "employees_min"):
        require(values[name] >= 0, name, "nonnegative profile size threshold required", "RESOURCE_INTEGRITY")
    return values, profile["tables"]["unlisted_equity_conditions"]


@calculation("DR:article-168a:2", unit="beta")
def unlisted_equity_beta(gross_margin_mean: float, debt: float, cashflow_mean: float,
                         equity_return_mean: float, *, formula_units_qualified: bool | None,
                         input_basis_reference: str, context: Context):
    """Literal formula; never infer percentage-point/fraction scaling of GM/ROCE.

    The archived DE definitions do not explicitly resolve that scaling. Means,
    accounting equity definition and formula-native units need external review.
    Debt/CFO is signed; no regulatory beta floor/cap is added.
    """
    _reference(input_basis_reference, "input_basis_reference")
    qualified = _known_flag(formula_units_qualified, "formula_units_qualified")
    require(qualified, "formula_units_qualified", "formula-native input units must be externally qualified",
            "REVIEW_REQUIRED")
    gm = number(gross_margin_mean, "gross_margin_mean")
    debt = number(debt, "debt", 0)
    cfo = number(cashflow_mean, "cashflow_mean")
    roe = number(equity_return_mean, "equity_return_mean")
    require(cfo != 0, "cashflow_mean", "zero mean cashflow makes formula undefined", "REVIEW_REQUIRED")
    parameters, _ = _parameters(context)
    coefficients = {name: parameters[name] for name in
                    ("beta_intercept", "beta_gm_coefficient", "beta_leverage_coefficient", "beta_return_coefficient")}
    beta = (_fraction(coefficients["beta_intercept"]) + _fraction(coefficients["beta_gm_coefficient"]) * _fraction(gm)
            + _fraction(coefficients["beta_leverage_coefficient"]) * _fraction(debt) / _fraction(cfo)
            + _fraction(coefficients["beta_return_coefficient"]) * _fraction(roe))
    return _finite(beta, "beta"), {"gross_margin_mean": gm, "debt": debt, "cashflow_mean": cfo,
        "equity_return_mean": roe, "coefficients": coefficients,
        "required_mean_history_years": int(parameters["mean_history_years"]),
        "input_basis_reference": input_basis_reference, "formula_units_qualified": qualified,
        "formula_unit_status": "EXTERNAL_QUALIFICATION_REQUIRED_ARCHIVED_DE_SCALING_NOT_RESOLVED",
        "units_converted": False, "historical_means_computed": False,
        "beta_floored_or_capped": False, "scope": "literal168a2_formula_not_portfolio_or_type1_approval"}


@calculation("DR:article-168a:1", "DR:article-168a:2", unit="indicator")
def unlisted_equity_portfolio_screen(investments: Mapping, *, qualification_reference: str, context: Context):
    """Check all supplied issuers; book weights differ from concentration values.

    Input completeness, company consolidation, fiscal periods, FX conversion and
    beta methodology are externally qualified. A failed condition yields0, an
    unresolved condition raises REVIEW_REQUIRED instead of being treated asFalse.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(investments, Mapping), "investments", "labelled issuer mapping required")
    require(bool(investments), "investments", "nonempty investment group required", "MISSING_INPUT")
    parameters, table = _parameters(context)
    condition_names = [row[0] for row in table["rows"]]
    require(len(set(condition_names)) == len(condition_names), "unlisted_equity_conditions",
            "duplicate condition keys", "RESOURCE_INTEGRITY")
    total_value, total_book, weighted_beta = Fraction(0), Fraction(0), Fraction(0)
    audit = {}
    for label, row in investments.items():
        require(isinstance(label, str) and bool(label.strip()), "issuer_id", "nonempty issuer ID required")
        exact_keys(row, ("investment_value", "book_value", "beta", "revenue_currency_share", "eea_employee_share",
                         "financial_years", "conditions", "beta_basis_reference"), label)
        _reference(row["beta_basis_reference"], label + ".beta_basis_reference")
        value = number(row["investment_value"], label + ".investment_value", 0)
        book = number(row["book_value"], label + ".book_value", 0)
        beta = number(row["beta"], label + ".beta")
        revenue = number(row["revenue_currency_share"], label + ".revenue_currency_share", 0, 1)
        employees = number(row["eea_employee_share"], label + ".eea_employee_share", 0, 1)
        exact_keys(row["conditions"], condition_names, label + ".conditions")
        controls = {key: _known_flag(row["conditions"][key], label + "." + key) for key in condition_names}
        years = row["financial_years"]
        require(isinstance(years, (list, tuple)), label + ".financial_years", "ordered fiscal-year rows required")
        require(len(years) == int(parameters["size_history_years"]), label + ".financial_years",
                "exact profile number of preceding fiscal years required", "MISSING_INPUT")
        year_audit = []
        for index, year in enumerate(years):
            field = label + ".financial_years." + str(index)
            exact_keys(year, ("turnover_eur", "balance_sheet_total_eur", "employees"), field)
            figures = {key: number(year[key], field + "." + key, 0) for key in year}
            routes = {"turnover": figures["turnover_eur"] > parameters["turnover_min"],
                      "balance_sheet": figures["balance_sheet_total_eur"] > parameters["balance_sheet_min"],
                      "employees": figures["employees"] > parameters["employees_min"]}
            year_audit.append({**figures, "size_routes": routes, "size_met": any(routes.values())})
        total_value += _fraction(value)
        total_book += _fraction(book)
        weighted_beta += _fraction(book) * _fraction(beta)
        audit[label] = {"investment_value": value, "book_value": book, "beta": beta,
                        "beta_basis_reference": row["beta_basis_reference"], "conditions": controls,
                        "revenue_currency_share": revenue, "eea_employee_share": employees,
                        "revenue_share_met": revenue > parameters["revenue_currency_min"],
                        "employee_share_met": employees > parameters["employee_share_min"],
                        "financial_years": year_audit}
    require(total_value > 0 and total_book > 0, "investments", "positive value and book-weight totals required",
            "REVIEW_REQUIRED")
    for row in audit.values():
        fraction = _fraction(row["investment_value"]) / total_value
        row["investment_share"] = _finite(fraction, "investment_share")
        row["concentration_met"] = fraction <= _fraction(parameters["investment_share_max"])
        row["issuer_conditions_met"] = (all(row["conditions"].values()) and row["revenue_share_met"]
            and row["employee_share_met"] and all(y["size_met"] for y in row["financial_years"])
            and row["concentration_met"])
    portfolio_beta = weighted_beta / total_book
    beta_met = portfolio_beta <= _fraction(parameters["portfolio_beta_max"])
    return int(beta_met and all(row["issuer_conditions_met"] for row in audit.values())), {
        "portfolio_beta": _finite(portfolio_beta, "portfolio_beta"), "portfolio_beta_met": beta_met,
        "total_investment_value": _finite(total_value, "total_investment_value"),
        "total_book_value": _finite(total_book, "total_book_value"),
        "investments": dict(sorted(audit.items())), "parameters": parameters,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "beta_formula_units_verified": False, "company_classification_verified": False,
        "scr_charge_computed": False, "scope": "declared168a_screen_not_full_equity_module_approval"}
