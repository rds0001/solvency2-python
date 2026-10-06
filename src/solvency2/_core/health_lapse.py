"""SLT health lapse assumptions; no automatic extension to NSLT article150."""
from typing import Mapping

from .aggregation import _select_scenario
from .core import Context, calculation, exact_keys, number, require, scalar
from .life_lapse import _option_stress, _reference


@calculation("DR:article-159:2-5", unit="probability")
def health_lapse_option_stress(exercise_rate: float, direction: str, *, option_kind: str,
                               selected: bool | None, selection_reference: str, context: Context):
    """Stress relevant exercise/non-exercise probability with health-specific parameters."""
    return _option_stress(exercise_rate, direction, option_kind, selected, selection_reference,
                          "health_lapse_relative", "health_lapse_down_cap", "slt_health_option_assumption_only_not_scr", context)


@calculation("DR:article-159:6", unit="ratio")
def health_mass_lapse_factor(category: str, *, qualification_reference: str, context: Context):
    """Return the40% event share, not proportional capital or life special-category70%.

    Uniform joint events, underlying reinsurance contracts and the worst
    termination form require external qualification in either reference profile.
    """
    require(category in ("termination_159_6_a", "future_159_6_b"), "category",
            "explicit supported SLT health category required", "UNSUPPORTED_METHOD")
    _reference(qualification_reference, "qualification_reference")
    return number(scalar("health_mass_lapse", context), "health_mass_lapse", 0, 1), {
        "category": category, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "required_joint_events": ["termination_159_6_a", "future_159_6_b"],
        "scope": "slt_health_event_share_only_not_scr"}


@calculation("DR:article-159:1", "DR:article-159:7", "DR:article-206:2")
def health_lapse_risk(gross_losses: Mapping, net_losses: Mapping, *, valuation_reference: str,
                      tie_break: str | None = None, context: Context):
    """Select the gross SLT health lapse charge corresponding to maximum net loss."""
    exact_keys(gross_losses, ["up", "down", "mass"], "gross_losses")
    exact_keys(net_losses, ["up", "down", "mass"], "net_losses")
    _reference(valuation_reference, "valuation_reference")
    value, details = _select_scenario(gross_losses, net_losses, tie_break)
    return value, {**details, "valuation_reference": valuation_reference,
                   "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "supplied_slt_health_lapse_scenarios_only"}
