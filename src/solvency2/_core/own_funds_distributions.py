"""2027 declared distribution policy/accrual arithmetic, not forecasts or approval."""
import math

from .core import Context, calculation, effective_resource, number, require, scalar
from .own_funds import _qualification, _version_sources

_NumericHistory = list[float] | tuple[float, ...]


def _future(context, reference):
    require(effective_resource("profile.json", context).get("methods", {}).get("foreseeable_distributions")
            == "ACCRUAL_2027", "profile_id", "2027 distribution method required", "UNSUPPORTED_RULESET")
    _qualification(reference)


def _policy_basis(policy_usable, policy_lower, policy_upper, historical_values, public_announcements,
                  qualification_reference, context):
    _future(context, qualification_reference)
    require(isinstance(policy_usable, bool), "policy_usable", "explicit usable-policy decision required")
    details = {"qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
               "scope": "qualified_policy_basis_only_no_extraordinary_year_exclusions",
               "_sources": _version_sources(context, "DR:article-70a-4-5")}
    if policy_usable:
        require(historical_values is None and public_announcements is None, "fallback_inputs",
                "omit unused fallback history/announcements when policy is usable")
        lower = number(policy_lower, "policy_lower", 0)
        upper = number(policy_upper, "policy_upper", 0)
        require(lower <= upper, "policy_range", "ordered policy range required")
        return upper, {**details, "method": "USABLE_POLICY_UPPER_END", "policy_lower": lower, "policy_upper": upper}
    require(policy_lower is None and policy_upper is None, "policy_range", "omit unused unusable-policy range")
    count = number(scalar("own_funds_distribution_history_years", context), "history_years", 1)
    require(count.is_integer(), "history_years", "whole number of history years required")
    require(isinstance(historical_values, (list, tuple)), "historical_values", "chronological annual values required", "MISSING_INPUT")
    require(len(historical_values) == int(count), "historical_values",
            "complete prescribed history required; no zero imputation or exceptional-year exclusion", "REVIEW_REQUIRED")
    history = [number(value, f"historical_values.{index}") for index, value in enumerate(historical_values)]
    require(all(value >= 0 for value in history), "historical_values",
            "negative payout history requires separate method qualification", "REVIEW_REQUIRED")
    require(isinstance(public_announcements, (list, tuple)), "public_announcements",
            "explicit list required, empty if no relevant public announcement", "MISSING_INPUT")
    announcements = [number(value, f"public_announcements.{index}", 0)
                     for index, value in enumerate(public_announcements)]
    # Divide before summing: a finite arithmetic mean need not overflow merely
    # because the sum of several large, finite amounts would overflow.
    average = math.fsum(value / count for value in history)
    basis = max(average, history[-1], *announcements)
    return basis, {**details, "method": "PRUDENT_HISTORY_AND_PUBLIC_FALLBACK", "historical_values": history,
                   "historical_mean": average, "latest_year": history[-1], "history_years": int(count),
                   "public_announcements": announcements}


@calculation("DR:article-70a:4-5", unit="ratio")
def own_funds_distribution_policy_ratio(policy_usable: bool, *, qualification_reference: str, context: Context,
                                         policy_lower: float | None = None, policy_upper: float | None = None,
                                         historical_values: _NumericHistory | None = None,
                                         public_announcements: _NumericHistory | None = None):
    """Select a qualified payout ratio; no invented cap at 100 percent."""
    return _policy_basis(policy_usable, policy_lower, policy_upper, historical_values,
                         public_announcements, qualification_reference, context)


@calculation("DR:article-70a:4-5")
def own_funds_distribution_policy_amount(policy_usable: bool, *, qualification_reference: str, context: Context,
                                          policy_lower: float | None = None, policy_upper: float | None = None,
                                          historical_values: _NumericHistory | None = None,
                                          public_announcements: _NumericHistory | None = None):
    """Select a qualified annual payout amount, in the context reporting currency."""
    return _policy_basis(policy_usable, policy_lower, policy_upper, historical_values,
                         public_announcements, qualification_reference, context)


@calculation("DR:article-70a:2-3")
def own_funds_foreseeable_distributions_2027(method: str, *, qualification_reference: str, context: Context,
                                              formal_amount: float | None = None, prior_year_distributions: float | None = None,
                                              payout_ratio: float | None = None, cumulative_interim_profit: float | None = None,
                                              estimated_annual_distribution: float | None = None,
                                              elapsed_year_fraction: float | None = None):
    """Formal amount, or one of two permitted accrual methods before that stage.

    Formal decisions/proposals, accounting profit and fiscal-year fraction are
    qualified externally. No internal profit model or day-count is invented.
    Fees under Article70(1)(b) are separate, not calculated by this function.
    """
    _future(context, qualification_reference)
    require(method in ("formal", "payout_ratio", "annual_amount"), "method", "explicit distribution method required")
    details = {"method": method, "qualification_reference": qualification_reference,
               "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "foreseeable_distributions_only_not_fees_or_approval",
               "_sources": _version_sources(context, "DR:article-70a-2-3")}
    if method == "formal":
        require(all(value is None for value in (prior_year_distributions, payout_ratio, cumulative_interim_profit,
                                                estimated_annual_distribution, elapsed_year_fraction)),
                "accrual_inputs", "omit unused accrual inputs for a qualified formal total")
        amount = number(formal_amount, "formal_amount", 0)
        return amount, {**details, "formal_amount": amount}
    require(formal_amount is None, "formal_amount", "omit unused formal amount for accrual")
    prior = number(prior_year_distributions, "prior_year_distributions", 0)
    if method == "payout_ratio":
        require(estimated_annual_distribution is None and elapsed_year_fraction is None,
                "annual_inputs", "omit unused annual-amount branch inputs")
        ratio = number(payout_ratio, "payout_ratio", 0)
        profit = number(cumulative_interim_profit, "cumulative_interim_profit")
        require(profit >= 0, "cumulative_interim_profit", "loss-period treatment requires separate qualification", "REVIEW_REQUIRED")
        current = ratio * profit
        details.update({"payout_ratio": ratio, "cumulative_interim_profit": profit})
    else:
        require(payout_ratio is None and cumulative_interim_profit is None,
                "profit_inputs", "omit unused profit-ratio branch inputs")
        annual = number(estimated_annual_distribution, "estimated_annual_distribution", 0)
        fraction = number(elapsed_year_fraction, "elapsed_year_fraction", 0, 1)
        current = annual * fraction
        details.update({"estimated_annual_distribution": annual, "elapsed_year_fraction": fraction})
    return math.fsum((prior, current)), {**details, "prior_year_distributions": prior, "current_year_accrual": current}
