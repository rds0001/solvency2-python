"""Joint nonlife/NSLT lapse events; no up/down/mass scenario selection applies."""
from .core import Context, calculation, number, require, scalar


def _factor(category, reference, key, scope, context):
    require(category in ("termination", "future_contracts"), "category",
            "termination or future_contracts required", "UNSUPPORTED_METHOD")
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external joint event qualification required", "MISSING_INPUT")
    return number(scalar(key, context), key, 0, 1), {
        "category": category, "qualification_reference": reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "required_joint_events": ["termination", "future_contracts"], "parameter_id": "scalars/" + key,
        "scope": scope}


@calculation("DR:article-118:1-3", unit="ratio")
def nonlife_lapse_factor(category: str, *, qualification_reference: str, context: Context):
    """Event share, not capital multiplier; underlying/worst selection external.

    Article90a permits contract-group selection for118(1)(a) only with88 and
   35(a-c) grouping qualification. The external reference must evidence this
    if used; it does not change the event share or remove joint valuation.
    """
    return _factor(category, qualification_reference, "nonlife_lapse_share", "nonlife_joint_event_share_only_not_scr", context)


@calculation("DR:article-150:1-3", unit="ratio")
def health_nslt_lapse_factor(category: str, *, qualification_reference: str, context: Context):
    """NSLT health event share; do not apply SLT's three-scenario selection here."""
    return _factor(category, qualification_reference, "health_nslt_lapse_share", "nslt_health_joint_event_share_only_not_scr", context)
