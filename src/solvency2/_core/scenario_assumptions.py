"""Optional observable gross-scenario checks; no insurer valuation certification."""
from .core import exact_keys, number, require
from .loss_given_default import _known_flag, _reference


def _check_gross_assumptions(checks):
    """Check each frozen component separately, never net deferred tax positions.

    The controls distinguish actions DURING stress from qualifying future
    actions AFTER it. These are declared assessments, not an Article23 model.
    Net-FDB scenarios used for Article206 are outside this optional contract.
    """
    components = ("risk_margin", "deferred_tax_assets", "deferred_tax_liabilities",
                  "future_discretionary_benefits")
    required_true = ("post_scenario_management_article23_qualified",
                     "adverse_policyholder_option_effects_included",
                     "qualifying_risk_mitigation_effects_included")
    exact_keys(checks, (*components, "management_actions_during_scenario", *required_true,
                       "valuation_reference"), "assumption_checks")
    _reference(checks["valuation_reference"], "assumption_checks.valuation_reference")
    observed = {}
    for field in components:
        row = checks[field]
        exact_keys(row, ("base", "stressed"), "assumption_checks." + field)
        base = number(row["base"], field + ".base")
        stressed = number(row["stressed"], field + ".stressed")
        require(base == stressed, field, "Article83 gross scenario component must remain constant",
                "REVIEW_REQUIRED")
        observed[field] = {"base": base, "stressed": stressed, "unchanged": True}
    during = _known_flag(checks["management_actions_during_scenario"], "management_actions_during_scenario")
    require(not during, "management_actions_during_scenario", "no management actions during83 stress",
            "REVIEW_REQUIRED")
    declared = {"management_actions_during_scenario": during}
    for field in required_true:
        declared[field] = _known_flag(checks[field], field)
        require(declared[field], field, "gross scenario qualification not established", "REVIEW_REQUIRED")
    return {"component_constancy": observed, "declared_controls": declared,
            "valuation_reference": checks["valuation_reference"],
            "qualification_status": "EXTERNAL_UNVERIFIED",
            "bof_reconciliation_verified": False,
            "simplification_eligibility_verified": False,
            "scope": "gross_article83_only_not_net_fdb_or_lac_tp"}
