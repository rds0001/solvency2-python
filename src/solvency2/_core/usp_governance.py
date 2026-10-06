"""Declared USP scope, treaty conditions, method selection and evidence inventory."""
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar
from .risk_mitigation import _finite_ids
from .evidence import _declared_bool, _evidence_inventory


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external qualification reference required", "MISSING_INPUT")


def _source(profile, context, locator):
    return context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":" + locator


@calculation("DR:article-218:1", "DR:article-218:4", "DIR:article-104:7", unit="indicator")
def usp_parameter_scope_check(replacements: list[str], *, risk_module: str, segment: str | None = None,
                               qualified_reinsurance: bool | None = None,
                               material_inflation_risk: bool | None = None,
                               qualification_reference: str, context: Context):
    """Check declared replacement scope, not data/method fitness or authorization.

    Gross-premium sigma and the NP factor cannot both be replaced in one
    segment. Revision is available only absent material inflation risk;
    materiality follows decision relevance, not an invented numeric cutoff.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(replacements, list) and bool(replacements), "replacements", "nonempty parameter list required")
    require(all(isinstance(p, str) for p in replacements) and len(set(replacements)) == len(replacements),
            "replacements", "unique string parameter names required")
    require(isinstance(risk_module, str) and risk_module in {"nonlife", "health_nslt", "life", "health_slt"},
            "risk_module", "eligible risk module required", "UNSUPPORTED_METHOD")
    selected = set(replacements)
    reasons = []
    if risk_module in {"nonlife", "health_nslt"}:
        limit = 12 if risk_module == "nonlife" else 4
        require(isinstance(segment, str) and segment in {str(i) for i in range(1, limit + 1)},
                "segment", "explicit eligible segment required", "UNSUPPORTED_PARAMETER")
        require(selected <= {"premium_sigma", "gross_premium_sigma", "nonproportional_factor", "reserve_sigma"},
                "replacements", "parameter outside prescribed premium/reserve subset", "UNSUPPORTED_PARAMETER")
        require(material_inflation_risk is None, "material_inflation_risk", "inflation condition is revision-only")
        if "nonproportional_factor" in selected:
            eligible = _declared_bool(qualified_reinsurance, "qualified_reinsurance")
            if not eligible:
                reasons.append("nonproportional_factor_requires_qualified_reinsurance")
        else:
            require(qualified_reinsurance is None, "qualified_reinsurance", "inactive condition must be None")
        if {"gross_premium_sigma", "nonproportional_factor"} <= selected:
            reasons.append("gross_premium_sigma_and_NP_factor_cannot_both_be_replaced")
    else:
        require(segment is None, "segment", "revision has no premium/reserve segment")
        require(selected == {"revision_shock"}, "replacements", "only revision shock eligible here",
                "UNSUPPORTED_PARAMETER")
        require(qualified_reinsurance is None, "qualified_reinsurance", "reinsurance condition is not revision scope")
        if _declared_bool(material_inflation_risk, "material_inflation_risk"):
            reasons.append("revision_USP_excluded_by_material_inflation_risk")
    profile = effective_resource("profile.json", context)
    return int(not reasons), {
        "replacements": sorted(selected), "risk_module": risk_module, "segment": segment,
        "qualified_reinsurance": qualified_reinsurance, "material_inflation_risk": material_inflation_risk,
        "ineligibility_reasons": reasons, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "data_and_method_qualified": False,
        "standard_parameter_replaced": False, "supervisory_approval_granted_by_engine": False,
        "scope": "declared_article218_parameter_subset_only_not_USP_authorization",
        "_sources": [_source(profile, context, "article-218")]}


@calculation("DR:article-218:2", "DR:article-218:3", "DR:article-208:2", unit="indicator")
def usp_reinsurance_contract_conditions(coverage_conditions: Mapping[str, bool],
                                         contract_requirements: Mapping[str, bool], *, contract_type: str,
                                         qualification_reference: str, finite_reinsurance_ids: list[str] | tuple = (),
                                         context: Context):
    """Check collective coverage and each contract's declared209/210/211/213 compliance.

    For multiple contracts the coverage conditions apply collectively, whereas
    every individual contract must satisfy the cross-article requirements.
    Qualified equivalent SPV arrangements are included; equivalent transfer is
    externally assessed, never inferred from the name or number of contracts.
    Finite/similar transfers invalidate this submitted contract set for USP;
    omit none from the declaration (empty means all are qualified non-finite).
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(contract_type, str) and contract_type in {"excess_of_loss", "aggregate_excess_of_loss"},
            "contract_type", "XL or aggregate XL contract type required", "UNSUPPORTED_METHOD")
    keys = ("full_cover_above_retention_to_limit_or_unlimited", "all_claims_over_horizon",
            "sufficient_reinstatements_over_horizon")
    exact_keys(coverage_conditions, keys, "coverage_conditions")
    require(isinstance(contract_requirements, Mapping) and bool(contract_requirements), "contract_requirements",
            "nonempty contract-labelled Article209/210/211/213 declarations required")
    require(all(isinstance(k, str) and bool(k.strip()) for k in contract_requirements), "contracts",
            "nonempty string contract labels required")
    for key, value in coverage_conditions.items():
        _declared_bool(value, "coverage_conditions." + key)
    for key, value in contract_requirements.items():
        _declared_bool(value, "contract_requirements." + key)
    finite = _finite_ids(finite_reinsurance_ids, contract_requirements)
    horizon = number(scalar("usp_reinsurance_horizon_months", context), "horizon_months", 1)
    require(horizon == int(horizon), "horizon_months", "whole-month horizon required", "REVIEW_REQUIRED")
    profile = effective_resource("profile.json", context)
    return int(not finite and all(coverage_conditions.values()) and all(contract_requirements.values())), {
        "finite_reinsurance_ids": sorted(finite), "article208_finite_exclusion_satisfied": not finite,
        "contract_type": contract_type, "coverage_conditions": dict(coverage_conditions),
        "contract_requirements": dict(contract_requirements), "contract_count": len(contract_requirements),
        "horizon_months": int(horizon), "coverage_assessment": "collective",
        "article209_210_211_213_assessment": "each_individual_contract",
        "equivalent_SPV_transfer_qualification": "EXTERNAL_UNVERIFIED",
        "source_reference_note": "218(3) literally references2(a,b,c); aggregate(aa) qualification external",
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "contract_content_verified": False, "supervisory_approval_granted_by_engine": False,
        "scope": "declared_USP_reinsurance_conditions_not_legal_contract_review",
        "_sources": [_source(profile, context, "article-218-2-3")]}


@calculation("DR:article-220:1", "DR:article-220:2", unit="factor")
def usp_standard_method_selection(method_results: Mapping[str, dict], *, parameter: str,
                                   superiority_demonstrated: bool, superior_method: str | None = None,
                                   qualification_reference: str, context: Context):
    """Select a qualified more accurate method, otherwise conservative capital result.

    Capital requirements must be comparable under the same qualified inputs.
    We do not assume that the largest raw parameter always gives the largest
    capital requirement. Ties use a disclosed deterministic technical ordering,
    not a claimed regulatory preference for one standardized method.
    """
    _reference(qualification_reference, "qualification_reference")
    profile = effective_resource("profile.json", context)
    require(isinstance(parameter, str), "parameter", "parameter name required", "UNSUPPORTED_PARAMETER")
    allowed = {row[1] for row in profile["tables"]["usp_parameter_methods"]["rows"] if row[0] == parameter}
    require(bool(allowed), "parameter", "no prescribed method mapping", "UNSUPPORTED_PARAMETER")
    require(isinstance(method_results, Mapping) and bool(method_results), "method_results",
            "nonempty method-labelled comparison required")
    require(all(isinstance(k, str) and k in allowed for k in method_results), "method_results",
            "candidate not permitted for selected parameter", "UNSUPPORTED_METHOD")
    values, capitals = {}, {}
    for method, row in method_results.items():
        exact_keys(row, ("parameter_value", "capital_requirement"), f"method_results.{method}")
        values[method] = number(row["parameter_value"], f"{method}.parameter_value",
                                None if parameter == "revision_shock" else 0)
        capitals[method] = number(row["capital_requirement"], f"{method}.capital_requirement", 0)
    demonstrated = _declared_bool(superiority_demonstrated, "superiority_demonstrated")
    conservative = sorted(k for k, v in capitals.items() if v == max(capitals.values()))
    if demonstrated:
        _reference(superior_method, "superior_method")
        require(superior_method in values, "superior_method", "superior method must be a supplied candidate")
        chosen, basis = superior_method, "externally_declared_accuracy_superiority"
    else:
        require(superior_method is None, "superior_method", "no superior method without declared evidence")
        chosen, basis = conservative[0], "maximum_qualified_capital_requirement"
    return values[chosen], {
        "parameter": parameter, "selected_method": chosen, "selection_basis": basis,
        "parameter_values": values, "capital_requirements": capitals,
        "equally_conservative_methods": conservative, "tie_break": "lexicographic_technical_only",
        "superiority_demonstrated": demonstrated, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "comparability_verified": False,
        "accuracy_superiority_verified": False, "standard_parameter_replaced": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "declared_standardized_method_selection_not_estimation_or_authorization",
        "_sources": [_source(profile, context, "article-220")]}


@calculation("DR:article-219", "DR:article-19:1-4", unit="indicator")
def usp_data_evidence_check(evidence: Mapping[str, dict], *, external_data_used: bool,
                             multiple_external_sources: bool, assessment_reference: str, context: Context):
    """Inventory active USP data references, never certify their content or quality."""
    external = _declared_bool(external_data_used, "external_data_used")
    multiple = _declared_bool(multiple_external_sources, "multiple_external_sources")
    require(not multiple or external, "multiple_external_sources", "multiple external sources imply external data")
    profile = effective_resource("profile.json", context)
    rows = profile["tables"]["usp_data_controls"]["rows"]
    active = {"always": True, "external": external, "multiple": multiple}
    selected = [row[:3] for row in rows if active[row[3]]]
    value, details = _evidence_inventory(evidence, {"rows": selected}, assessment_reference)
    return value, {**details, "external_data_used": external, "multiple_external_sources": multiple,
        "inactive_controls": [r[0] for r in rows if not active[r[3]]],
        "source_reference_note": "219(1)c printed2009/13/EG retained; no editorial repair",
        "data_quality_certified": False, "method_specific_requirements_still_required": True,
        "supervisory_approval_granted_by_engine": False,
        "scope": "declared_USP_data_evidence_inventory_not_quality_or_method_approval",
        "_sources": details["_sources"] + [_source(profile, context, "article-219")]}


@calculation("DR:article-219:1:d", "DR:annex-XVII:B:1-2", "DR:annex-XVII:C:1-2",
             "DR:annex-XVII:D:1-2", "DR:annex-XVII:E:1-2",
             "DR:annex-XVII:F1:data-1-2", "DR:annex-XVII:F2:data-1-2", unit="indicator")
def usp_method_data_evidence_check(evidence: Mapping[str, dict], *, method: str, data_basis: str,
                                    assessment_reference: str, context: Context):
    """Inventory method-specific references, with explicit gross/net and year bases.

    B/C/D/E include servicing expenses; F1/F2 exclude them. A reference is
    never inspected or treated as verified data, calibration or approval.
    This inventory neither enables the blocked F2 estimator nor extends the
    square-triangle reserve2 calculator to rectangular development histories.
    """
    bases = {"premium": {"gross", "net"}, "reserve_1": {"net"}, "reserve_2": {"net"},
             "revision": {"gross"}, "nonproportional_1": {"gross", "net"},
             "nonproportional_2": {"gross", "net"}}
    require(isinstance(method, str) and method in bases, "method",
            "prescribed standardized method required", "UNSUPPORTED_METHOD")
    require(isinstance(data_basis, str) and data_basis in bases[method], "data_basis",
            "gross/net basis not supported for selected method", "UNSUPPORTED_PARAMETER")
    profile = effective_resource("profile.json", context)
    rows = [r for r in profile["tables"]["usp_method_data_controls"]["rows"] if r[0] == method]
    selected = [r[1:4] for r in rows if r[4] == "always" or r[4] == data_basis]
    value, details = _evidence_inventory(evidence, {"rows": selected}, assessment_reference)
    if method in {"premium", "reserve_1"}:
        minimum_key = "usp_lognormal_minimum_years"
    elif method == "reserve_2":
        minimum_key = "usp_reserve2_minimum_accident_years"
    elif method == "revision":
        minimum_key = "usp_revision_minimum_years"
    else:
        minimum_key = "usp_nonproportional_minimum_reporting_years"
    minimum = number(scalar(minimum_key, context), "minimum_years", 1)
    horizon = number(scalar("usp_data_representativeness_horizon_months", context), "horizon_months", 1)
    require(minimum == int(minimum) and horizon == int(horizon), "history_and_horizon",
            "whole-year and whole-month parameters required", "REVIEW_REQUIRED")
    development = None
    if method == "reserve_2":
        development = number(scalar("usp_reserve2_minimum_development_years", context), "development_years", 1)
        require(development == int(development), "development_years", "whole-year minimum required", "REVIEW_REQUIRED")
        development = int(development)
    year_basis = ("accident_years" if method in {"premium", "reserve_2"} else
                  "financial_years" if method in {"reserve_1", "revision"} else "reporting_years")
    return value, {**details, "method": method, "data_basis": data_basis,
        "inactive_controls": [r[1] for r in rows if r[4] not in {"always", data_basis}],
        "required_history": {"minimum_years": int(minimum), "basis": year_basis,
                             "consecutive": method not in {"nonproportional_1", "nonproportional_2"},
                             "minimum_oldest_year_development_years": development},
        "representativeness_horizon_months": int(horizon),
        "expense_treatment": "exclude" if method in {"nonproportional_1", "nonproportional_2"} else "include",
        "source_axis_note": ("F2 estimator indexes financial years; data and credibility require reporting years"
                             if method == "nonproportional_2" else None),
        "data_quality_certified": False, "estimator_implementation_asserted": False,
        "supervisory_approval_granted_by_engine": False,
        "scope": "declared_method_specific_data_inventory_not_estimator_qualification_or_authorization",
        "_sources": details["_sources"] + [_source(profile, context, "annex-XVII-method-data")]}
