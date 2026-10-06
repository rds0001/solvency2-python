"""Prescribed Article176a numeric screens; never an internal credit model."""
from fractions import Fraction
import sys
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


def _fraction(value):
    # Compare decimal representations without floating boundary drift. No
    # division by financial metrics, floors or invented rounding conventions.
    return Fraction(str(value))


def _audit(value):
    """Keep oversized/tiny exact intermediates JSON-safe rather than Inf/zero."""
    if abs(value) <= Fraction(str(sys.float_info.max)):
        converted = float(value)
        if converted != 0 or value == 0:
            return converted
    return {"exact_fraction": str(value)}


def _qualification(reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external scope, data completeness and substantive qualification required", "MISSING_INPUT")


def _parameter(name, context, maximum=None):
    return number(scalar("assigned_credit_" + name, context), name, 0, maximum)


def _years(name, context):
    value = _parameter(name, context)
    require(value >= 1 and value.is_integer(), name, "positive whole years required", "REVIEW_REQUIRED")
    return int(value)


def _provenance(context, reference, refs):
    profile = effective_resource("profile.json", context)
    return {"qualification_reference": reference, "qualification_status": "EXTERNAL_UNVERIFIED",
            "credit_quality_step_assigned": False, "internal_credit_model_developed": False,
            "substantive_conditions_verified": False, "supervisory_approval_granted_by_engine": False,
            "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":" + ref
                         for ref in refs]}


@calculation("DR:article-176a:3:g:iii-ix", unit="indicator")
def assigned_credit_issuer_financial_screen(financial_years: list, latest_financials: Mapping,
        eligible_currency_revenue_share: float, years_without_credit_event: float, *,
        qualification_reference: str, context: Context):
    """Screen seven numeric issuer criteria on qualified EUR financial values.

    Rows are oldest to newest, consecutive completed financial years. All
    supplied rows are validated; only the latest prescribed windows are used.
    EUR inputs remain EUR even if Context.currency differs. Definitions,
    chronology, latest-value alignment and currency-revenue scope are external.
    A pass does not satisfy other Article176a conditions or assign a CQS.
    """
    _qualification(qualification_reference)
    financial_count = _years("financial_history_years", context)
    size_count = _years("size_history_years", context)
    require(size_count <= financial_count, "history_years", "size window exceeds financial window",
            "REVIEW_REQUIRED")
    require(isinstance(financial_years, (list, tuple)), "financial_years", "ordered annual rows required")
    require(len(financial_years) >= financial_count, "financial_years", "full prescribed history required",
            "UNSUPPORTED_PARAMETER")
    annual_keys = ("revenue_eur", "balance_sheet_eur", "employees", "ebitda_eur", "free_cashflow_eur")
    rows = []
    for i, row in enumerate(financial_years):
        exact_keys(row, annual_keys, f"financial_years[{i}]")
        rows.append({key: _fraction(number(row[key], f"financial_years[{i}].{key}",
                                          0 if key == "employees" else None)) for key in annual_keys})
    latest_keys = ("total_debt_eur", "interest_expense_eur", "net_debt_eur", "equity_eur")
    exact_keys(latest_financials, latest_keys, "latest_financials")
    latest = {key: _fraction(number(latest_financials[key], key, 0 if key == "total_debt_eur" else None))
              for key in latest_keys}
    share = number(eligible_currency_revenue_share, "eligible_currency_revenue_share", 0, 1)
    event_years = number(years_without_credit_event, "years_without_credit_event", 0)
    parameters = {name: _parameter(name, context, 1 if name == "currency_share_min" else None)
                  for name in ("currency_share_min", "no_event_min_years", "size_amount_eur",
                               "employee_threshold", "debt_fcf_multiple", "ebitda_interest_multiple",
                               "net_debt_equity_multiple")}
    p = {key: _fraction(value) for key, value in parameters.items()}
    size_checks = [{"revenue": row["revenue_eur"] > p["size_amount_eur"],
                    "balance_sheet": row["balance_sheet_eur"] > p["size_amount_eur"],
                    "employees": row["employees"] > p["employee_threshold"]} for row in rows[-size_count:]]
    ebitda_sum = sum((row["ebitda_eur"] for row in rows[-financial_count:]), Fraction(0))
    ebitda_mean = ebitda_sum / financial_count
    fcf_mean = sum((row["free_cashflow_eur"] for row in rows[-financial_count:]), Fraction(0)) / financial_count
    debt_bound = p["debt_fcf_multiple"] * fcf_mean
    ebitda_bound = p["ebitda_interest_multiple"] * latest["interest_expense_eur"]
    net_debt_bound = p["net_debt_equity_multiple"] * latest["equity_eur"]
    criteria = {"currency_share": _fraction(share) > p["currency_share_min"],
                "no_credit_event": _fraction(event_years) >= p["no_event_min_years"],
                "every_year_size": all(any(check.values()) for check in size_checks),
                "positive_total_ebitda": ebitda_sum > 0,
                "debt_fcf": latest["total_debt_eur"] <= debt_bound,
                "ebitda_interest": ebitda_mean >= ebitda_bound,
                "net_debt_equity": latest["net_debt_eur"] <= net_debt_bound}
    return int(all(criteria.values())), {
        "criteria": criteria, "size_checks_oldest_to_newest": size_checks,
        "financial_history_years": financial_count, "size_history_years": size_count,
        "older_years_excluded": len(rows) - financial_count, "parameters": parameters,
        "intermediates_eur": {key: _audit(value) for key, value in {
            "ebitda_sum": ebitda_sum, "ebitda_mean": ebitda_mean, "fcf_mean": fcf_mean,
            "total_debt_maximum": debt_bound, "ebitda_mean_minimum": ebitda_bound,
            "net_debt_maximum": net_debt_bound}.items()},
        "financial_input_currency": "EUR", "fx_conversion_applied": False,
        "chronology_and_latest_alignment_verified": False, "zero_floors_applied": False,
        "scope": "article_176a_3g_numeric_criteria_only",
        **_provenance(context, qualification_reference, ["article-176a-3-g-iii-ix"])}


@calculation("DR:article-176a:4-9", unit="indicator")
def assigned_credit_yield_screen(yield_observations: Mapping, index_yields: Mapping, *,
        current_issue_id: str, target_cqs: str, qualification_reference: str, context: Context):
    """Check every qualified issue against both prescribed yield ceilings.

    Index keys are 2/4 or 3/4, not sorted by observed yield. All rates are
    absolute decimal rates, allowing negative yields. Complete comparable own
    issues, issue-date indices, maturity/currency and any adjustments under
    paragraphs8/9 must be supplied and qualified externally.
    """
    _qualification(qualification_reference)
    require(isinstance(target_cqs, str) and target_cqs in {"2", "3"}, "target_cqs", "string2 or3 required")
    exact_keys(index_yields, (target_cqs, "4"), "index_yields")
    indices = {key: _fraction(number(value, "index_yields." + key)) for key, value in index_yields.items()}
    require(isinstance(current_issue_id, str) and bool(current_issue_id.strip()), "current_issue_id",
            "nonempty current issue identifier required")
    require(isinstance(yield_observations, Mapping), "yield_observations", "issue-to-yield mapping required")
    require(current_issue_id in yield_observations, "current_issue_id", "current issue yield required", "MISSING_INPUT")
    require(all(isinstance(key, str) and bool(key.strip()) for key in yield_observations),
            "yield_observations", "nonempty string issue identifiers required")
    observations = {key: _fraction(number(value, "yield_observations." + key))
                    for key, value in yield_observations.items()}
    margin = _parameter("yield_margin", context)
    lookback = _years("comparable_years", context)
    mean_bound = (indices[target_cqs] + indices["4"]) / 2
    margin_bound = indices[target_cqs] + _fraction(margin)
    checks = {key: {"mean_limit_met": value <= mean_bound, "margin_limit_met": value <= margin_bound}
              for key, value in observations.items()}
    return int(all(all(check.values()) for check in checks.values())), {
        "target_cqs": target_cqs, "current_issue_id": current_issue_id, "issue_checks": checks,
        "mean_yield_ceiling": _audit(mean_bound), "margin_yield_ceiling": _audit(margin_bound),
        "absolute_yield_margin": margin, "comparable_financial_years": lookback,
        "index_qualification_verified": False, "comparable_issue_completeness_verified": False,
        "yield_adjustments_verified": False, "issue_dates_verified": False,
        "scope": "article_176a_yield_limits_not_credit_assignment",
        **_provenance(context, qualification_reference, ["article-176a-4-9"])}
