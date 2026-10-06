"""Life lapse assumptions and supplied-scenario selection, not contract valuation."""
from typing import Mapping

from .aggregation import _select_scenario
from .core import Context, calculation, exact_keys, number, require, scalar
from .market import _lapse_rate


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "external qualification or valuation reference required", "MISSING_INPUT")


@calculation("DR:article-142:2-5", unit="probability")
def life_lapse_option_stress(exercise_rate: float, direction: str, *, option_kind: str,
                             selected: bool | None, selection_reference: str, context: Context):
    """Return exercise probability, stressing non-exercise for extension options.

    Selection depends on the relevant technical-provision effect, not merely
    the option label. Underlying/reinsurance rights are classified externally.
    """
    return _option_stress(exercise_rate, direction, option_kind, selected, selection_reference,
                          "lapse_relative", "lapse_down_cap", "option_assumption_only_not_scr", context)


def _option_stress(exercise_rate, direction, option_kind, selected, selection_reference,
                   relative_key, cap_key, scope, context):
    """Shared selection/complement logic with explicitly supplied parameter identities."""
    base = number(exercise_rate, "exercise_rate", 0, 1)
    require(option_kind in ("termination", "extension"), "option_kind", "termination or extension required")
    require(direction in ("up", "down"), "direction", "up or down required")
    require(selected is None or isinstance(selected, bool), "selected", "boolean or None required")
    require(selected is not None, "selected", "selection unresolved", "REVIEW_REQUIRED")
    _reference(selection_reference, "selection_reference")
    relevant = 1 - base if option_kind == "extension" else base
    stressed = _lapse_rate(relevant, direction, scalar(relative_key, context), scalar(cap_key, context)) if selected else relevant
    value = (1 - stressed if option_kind == "extension" else stressed) if selected else base
    return value, {"base_exercise_rate": base, "relevant_base_rate": relevant,
                   "relevant_stressed_rate": stressed, "option_kind": option_kind,
                   "direction": direction, "selected": selected, "selection_reference": selection_reference,
                   "selection_status": "EXTERNAL_UNVERIFIED", "scope": scope}


@calculation("DR:article-142:6", unit="ratio")
def life_mass_lapse_factor(category: str, *, qualification_reference: str, context: Context):
    """Return event share, never a proportional BOF/TP loss or standalone mass SCR.

    Categories a/b are disjoint and a/b/c apply jointly where relevant. Special
    category qualification and worst termination form remain external.
    In2027, uniform application to affected contracts and application to the
    underlying insurance contracts for reinsurance a/b must also be qualified.
    """
    keys = {"special_142_6_a": "mass_lapse_special", "standard_142_6_b": "mass_lapse_standard",
            "future_142_6_c": "mass_lapse_standard"}
    require(isinstance(category, str) and category in keys, "category", "explicit supported category required",
            "UNSUPPORTED_METHOD")
    _reference(qualification_reference, "qualification_reference")
    key = keys[category]
    value = number(scalar(key, context), key, 0, 1)
    return value, {"category": category, "parameter_id": "scalars/" + key,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "required_joint_events": ["special_142_6_a", "standard_142_6_b", "future_142_6_c"],
                   "scope": "event_share_only_not_scr"}


@calculation("DR:article-142:1", "DR:article-142:7", "DR:article-206:2")
def life_lapse_risk(gross_losses: Mapping, net_losses: Mapping, *, valuation_reference: str,
                    tie_break: str | None = None, context: Context):
    """Select gross capital using all three externally valued net scenarios."""
    exact_keys(gross_losses, ["up", "down", "mass"], "gross_losses")
    exact_keys(net_losses, ["up", "down", "mass"], "net_losses")
    _reference(valuation_reference, "valuation_reference")
    value, details = _select_scenario(gross_losses, net_losses, tie_break)
    return value, {**details, "valuation_reference": valuation_reference,
                   "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "supplied_lapse_scenarios_only"}
