"""Historical factors expressly retained by Article178a(3)/(4), not new models."""
from .contracts import _date
from .core import exact_keys, number, require
from .zero_factors import _qualified_conditions


def historical_type1_factor(duration, category, credit_quality_step, transition, reference, profile, context):
    """Keep historical eligibility, issue dates and the 2025 sunset distinct."""
    table = profile["tables"]["securitisation_legacy_2018"]
    third = category == "legacy_type1_178a_3"
    predicate = "qualified_under_2018_article177_4" if third else "qualified_under_2018_article177_5"
    exact_keys(transition, ("issue_date", predicate), "transition")
    audit = _qualified_conditions({predicate: transition[predicate]}, (predicate,), reference)
    issued = _date(transition["issue_date"], "transition.issue_date")
    entry = _date(table["entry_into_force"], "table.entry_into_force")
    if third:
        require(issued < entry, "transition.issue_date", "Article178a(3) requires issue before entry into force",
                "REVIEW_REQUIRED")
    else:
        require(entry < issued < _date(table["pre_2019_cutoff"], "table.pre_2019_cutoff"),
                "transition.issue_date", "Article177(5)/178a(4) issue window not met", "REVIEW_REQUIRED")
        require(_date(context.as_of, "as_of") <= _date(table["last_application_178a_4"], "table.last_application_178a_4"),
                "as_of", "Article178a(4) transition has expired; choose an applicable current route", "UNSUPPORTED_METHOD")
    slopes = dict(table["rows"])
    require(isinstance(credit_quality_step, str) and credit_quality_step in slopes,
            "credit_quality_step", "historical type1 table requires explicit CQS0 through3")
    raw_duration = number(duration, "modified_duration", 0)
    minimum = number(table["minimum_duration"], "minimum_duration", 0)
    effective = max(raw_duration, minimum)
    cap = number(table["maximum_stress"], "maximum_stress", 0, 1)
    slope = number(slopes[credit_quality_step], "slope", 0)
    from .spread import _duration_band_stress
    value, details = _duration_band_stress([[0, None, 0, slope, True]], effective, cap)
    return value, {**details, "category": category, "credit_quality_step": credit_quality_step,
        "modified_duration": raw_duration, "effective_duration": effective, "minimum_duration": minimum,
        "table_id": "securitisation_legacy_2018", "transition": {**audit, "issue_date": issued.isoformat()},
        "qualification_reference": reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "historical_classification_verified": False,
        "transition_last_application": None if third else table["last_application_178a_4"],
        "scope": "historical_type1_position_shock_only_not_classification_or_BOF_revaluation",
        "_sources": ["DR:article-178a:" + ("3" if third else "4"), table["source"],
                     "DR2018:article-177:" + ("4" if third else "5")]}
