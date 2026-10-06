"""Prescribed Article300 arithmetic, never automatic publication/application."""
from fractions import Fraction
import math

from .core import Context, calculation, number, require, scalar
from .loss_given_default import _known_flag, _reference


@calculation("DIR:article-300", unit="EUR")
def regulatory_euro_amount_indexation(base_amount: float, last_published_amount: float,
        cumulative_inflation: float, inflation_since_last_adjustment: float, *,
        review_due: bool | None, qualification_reference: str, context: Context):
    """Original EUR base times HICP change since31Dec2015, rounded upward.

    Review schedule, Eurostat aggregate, original base and last publication are
    qualified inputs. The output is a calculated proposal; it never changes
    the existing ruleset's MCR/scope parameters or asserts national adoption.
    """
    _reference(qualification_reference, "qualification_reference")
    require(context.currency == "EUR", "currency", "Article300 EUR amounts required", "UNSUPPORTED_CURRENCY")
    base = number(base_amount, "base_amount", 0)
    previous = number(last_published_amount, "last_published_amount", 0)
    cumulative = number(cumulative_inflation, "cumulative_inflation")
    recent = number(inflation_since_last_adjustment, "inflation_since_last_adjustment")
    require(base > 0 and previous > 0 and cumulative > -1 and recent > -1, "indexation_basis", "positive amounts and valid inflation changes required")
    due = _known_flag(review_due, "review_due")
    step = number(scalar("euro_indexation_rounding_step", context), "rounding_step", 0)
    trigger = number(scalar("euro_indexation_change_threshold", context), "change_threshold", 0)
    require(step > 0, "rounding_step", "positive EUR grid required")
    apply = due and recent >= trigger
    value = previous
    if apply:
        grid = Fraction(str(step))
        exact = Fraction(str(base)) * (1 + Fraction(str(cumulative)))
        try:
            value = float(math.ceil(exact / grid) * grid)
        except OverflowError:
            require(False, "indexed_amount", "result outside representable range", "REVIEW_REQUIRED")
    return value, {"base_amount": base, "last_published_amount": previous,
        "cumulative_inflation": cumulative, "inflation_since_last_adjustment": recent,
        "review_due": due, "adjustment_calculated": apply, "rounding_step": step,
        "change_threshold": trigger, "review_interval_years": scalar("euro_indexation_review_years", context),
        "national_application_max_months": scalar("euro_indexation_application_months", context),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "official_publication_or_national_application_verified": False,
        "existing_rule_parameters_changed": False, "scope": "article300_proposal_not_applicable_minimum_selection"}
