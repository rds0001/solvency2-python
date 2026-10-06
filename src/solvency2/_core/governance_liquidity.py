"""2027 liquidity-plan evidence; no insurer projections or supervisory decisions."""
from .core import effective_resource, exact_keys, number, require
from .evidence import _declared_bool, _evidence_inventory, _reference


def liquidity_assessment(assessment, governance_facts, context):
    """Keep plan exemptions separate from continuing liquidity-risk management.

    A group-plan exemption requires the actual subsidiary scope and coverage
    to be externally qualified. A renewed solo-plan request overrides that
    exemption, not the supervisor's decision itself. No date expiry, plan
    adequacy, legal applicability or permission to make payments is inferred.
    """
    if assessment is None:
        return True, {"status": "NOT_ASSESSED"}
    profile = effective_resource("profile.json", context)
    require("liquidity_plan_controls" in profile["tables"], "liquidity_assessment",
            "2027 liquidity-plan contract required", "UNSUPPORTED_RULESET")
    exact_keys(assessment, ("scope", "plan_basis", "conditions", "evidence",
                            "qualification_reference"), "liquidity_assessment")
    _reference(assessment["qualification_reference"], "liquidity_assessment.qualification_reference")
    scope, basis = assessment["scope"], assessment["plan_basis"]
    require(scope in ("solo", "group"), "scope", "explicit solo or group required")
    require(basis in ("own", "small_non_complex", "approved_exemption", "group_plan"),
            "plan_basis", "explicit qualified plan basis required")
    names = ("medium_long_requested", "solo_plan_required", "liquidity_risk_notified",
             "surrender_suspended", "sector_measures_active", "combined_adjustment_plan")
    exact_keys(assessment["conditions"], names, "liquidity_assessment.conditions")
    facts = {key: _declared_bool(assessment["conditions"][key], key) for key in names}
    require(basis != "small_non_complex" or governance_facts["small_non_complex"],
            "plan_basis", "SNC exemption requires qualified SNC status")
    require(basis != "group_plan" or scope == "solo", "plan_basis",
            "group-plan subsidiary exemption is a solo route")
    require(not facts["solo_plan_required"] or scope == "solo" and basis == "own",
            "plan_basis", "supervisory solo-plan request requires own solo plan")
    require(not facts["combined_adjustment_plan"] or basis == "own" and
            (governance_facts["matching_adjustment"] or governance_facts["volatility_adjustment"]),
            "combined_adjustment_plan", "combination requires own plan and declared MA or VA")
    facts.update(own_plan=basis == "own", group_plan=basis == "group_plan",
                 exempt=basis in ("small_non_complex", "approved_exemption"),
                 medium_long_plan=basis == "own" and facts["medium_long_requested"])
    rows = profile["tables"]["liquidity_plan_controls"]["rows"]
    active = [row[:3] for row in rows if row[3] == "always" or facts[row[3]]]
    complete, details = _evidence_inventory(assessment["evidence"], {"rows": active},
                                          assessment["qualification_reference"])
    periods = {key: number(row["value"], key, 0) for key, row in profile["scalars"].items()
               if key.startswith("liquidity_supervisory_")}
    require(all(value > 0 for value in periods.values()), "supervisory_periods", "positive periods required")
    return bool(complete), {**details, "status": "DECLARED_EVIDENCE_INVENTORY",
        "scope": scope, "plan_basis": basis, "conditions": facts,
        "own_plan_required_on_declared_facts": basis == "own",
        "inactive_controls": [row[0] for row in rows if row[3] != "always" and not facts[row[3]]],
        "supervisory_periods_months": periods, "periods_apply_to_supervisor_not_company": True,
        "projection_generated": False, "supervisory_decision_verified": False,
        "payments_authorised": False, "legal_applicability_verified": False,
        "plan_update_frequency": "EXTERNAL_APPLICABLE_STANDARD_NOT_INVENTED",
        "_sources": details["_sources"] + [profile["sources"]["DIR"]["sha256"]]}
