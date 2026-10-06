"""Equal daily index weights on an externally selected and qualified window."""
from datetime import date
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, number, require, scalar
from .loss_given_default import _known_flag, _reference


@calculation("DR:article-172:2:b", "DR:article-172:3", unit="index_level")
def symmetric_adjustment_average(daily_indices: Mapping[str, float | None], *,
                                 window_months: int, complete_window: bool | None,
                                 index_qualified: bool | None, qualification_reference: str,
                                 context: Context):
    """Average determined daily levels, not dates, months or carried-forward values.

    None declares that no index was determined that day; it is not permission
    to hide missing observations. Exact endpoint selection and completeness
    remain externally qualified. Never fetch or manufacture market data.
    """
    _reference(qualification_reference, "qualification_reference")
    complete = _known_flag(complete_window, "complete_window")
    qualified = _known_flag(index_qualified, "index_qualified")
    require(complete and qualified, "qualification", "complete selected window and eligible index required",
            "REVIEW_REQUIRED")
    required = number(scalar("sa_window_months", context), "sa_window_months", 1)
    months = number(window_months, "window_months", 1)
    require(required.is_integer() and months.is_integer(), "window_months", "whole months required")
    require(months == required, "window_months", "selected period differs from profile window", "REVIEW_REQUIRED")
    require(isinstance(daily_indices, Mapping), "daily_indices", "date-to-index mapping required")
    require(bool(daily_indices), "daily_indices", "nonempty daily observation mapping required", "MISSING_INPUT")
    observations, excluded, total, count = {}, [], Fraction(0), 0
    valuation_date = date.fromisoformat(context.as_of)
    for day, raw in daily_indices.items():
        require(isinstance(day, str), "observation_date", "strict ISO calendar date required")
        try:
            observed = date.fromisoformat(day)
        except ValueError:
            require(False, "observation_date", "invalid calendar date")
        require(observed.isoformat() == day and observed <= valuation_date,
                "observation_date", "strict ISO date no later than valuation date required")
        month_distance = (valuation_date.year - observed.year) * 12 + valuation_date.month - observed.month
        require(month_distance <= months, "observation_date",
                "observation precedes even the earliest month of the declared window", "INVALID_INPUT")
        if raw is None:
            observations[day] = None
            excluded.append(day)
            continue
        value = number(raw, "daily_indices." + day, 0)
        require(value > 0, "daily_indices." + day, "determined index levels must be positive")
        observations[day] = value
        total += Fraction(str(value))
        count += 1
    require(count > 0, "daily_indices", "no determined daily index in supplied window", "REVIEW_REQUIRED")
    average = float(total / count)
    require(average > 0, "average", "positive daily average underflows", "REVIEW_REQUIRED")
    dates = sorted(observations)
    return average, {"daily_indices": dict(sorted(observations.items())),
        "included_days": count, "excluded_undetermined_days": sorted(excluded),
        "excluded_day_count": len(excluded), "first_supplied_date": dates[0], "last_supplied_date": dates[-1],
        "window_months": int(months), "required_window_months": int(required),
        "complete_window_declared": complete, "index_qualified_declared": qualified,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "calendar_endpoints_selected": False, "window_completeness_verified": False,
        "clearly_outside_window_months_rejected": True,
        "missing_values_imputed": False, "method": "equal_weight_determined_daily_levels",
        "scope": "qualified_selected_period_average_not_official_index_reproduction"}
