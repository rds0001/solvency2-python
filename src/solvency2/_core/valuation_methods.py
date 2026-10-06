"""Article16 method restrictions before forwarding externally valued positions.

This is a bounded input control, not a valuation model or a complete method
approval. Market quality and recognition remain external. Optional Article10
control checks only the declared ordinary order, not exceptions or market facts.
"""
from collections.abc import Mapping

from .core import Context, calculation, exact_keys, number, require
from .loss_given_default import _known_flag, _reference
from .valuation import valuation_liability_excluding_own_credit, valuation_short_term_deposit_cost_2027


_METHODS = frozenset({
    "fair_value", "cost", "amortised_cost", "depreciated_cost", "replacement_cost",
    "lower_of_book_and_fair_value_less_costs", "nominal", "lease_payment_pv",
    "net_realisable_value",
})
_POSITION_METHODS = {
    "financial_asset": ("fair_value",),
    "financial_liability": ("fair_value",),
    "short_term_deposit": ("fair_value", "cost", "amortised_cost"),
    "property": ("fair_value", "replacement_cost"),
    "investment_property": ("fair_value", "replacement_cost"),
    "plant_equipment": ("fair_value", "replacement_cost"),
    "finance_lease_asset": ("fair_value",),
    "finance_lease_liability": ("lease_payment_pv",),
    "inventory": ("net_realisable_value",),
    "nonmonetary_grant": ("fair_value",),
    "biological_asset": ("fair_value",),
}
_CONDITIONS = {
    "finance_lease_asset": ("market_consistent_inputs", "own_credit_adjustment_excluded"),
    "finance_lease_liability": ("market_consistent_inputs", "own_credit_adjustment_excluded"),
    "inventory": ("material_completion_and_sale_costs_addressed",),
    "biological_asset": ("material_selling_costs_addressed",),
}


def _hierarchy_control(hierarchy):
    """Check the ordinary Article10 order, not quote quality or exceptions."""
    if hierarchy is None:
        return None
    keys = ("basis", "identical_active_quote_usable", "similar_active_quote_usable",
            "ordinary_article10_scope")
    exact_keys(hierarchy, keys, "hierarchy")
    for key in keys[1:]:
        require(hierarchy[key] is not None, key, "external hierarchy qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(hierarchy[key], bool), key, "explicit boolean required")
    require(hierarchy["ordinary_article10_scope"], "ordinary_article10_scope",
            "special valuation exceptions are outside ordinary hierarchy control", "UNSUPPORTED_METHOD")
    bases = ("identical_active_quote", "adjusted_similar_active_quote", "alternative_valuation")
    require(isinstance(hierarchy["basis"], str) and hierarchy["basis"] in bases,
            "basis", "explicit supported hierarchy basis required")
    expected = (bases[0] if hierarchy["identical_active_quote_usable"] else
                bases[1] if hierarchy["similar_active_quote_usable"] else bases[2])
    require(hierarchy["basis"] == expected, "basis", "declared usable quotes require a different basis",
            "UNSUPPORTED_METHOD")
    return dict(hierarchy)


def _own_credit_control(value, evidence, position_type, context):
    """Bind one qualified valuation technique, without a proprietary credit model."""
    if evidence is None:
        return value, None, []
    require(position_type == "financial_liability", "own_credit",
            "this own-credit path is only for financial liabilities, not leases or other positions",
            "UNSUPPORTED_METHOD")
    require(isinstance(evidence, Mapping), "own_credit", "explicit technique evidence required")
    approach = evidence.get("approach")
    require(approach in ("bottom_up", "top_down"), "own_credit.approach", "known approach required",
            "UNSUPPORTED_METHOD")
    common = ("approach", "assessment_reference", "market_changes_considered")
    extra = (("initial_credit_spreads", "applied_credit_spreads") if approach == "bottom_up" else
             ("cumulative_own_credit_change", "already_corrected"))
    exact_keys(evidence, (*common, *extra), "own_credit")
    _reference(evidence["assessment_reference"], "own_credit.assessment_reference")
    checks = evidence["market_changes_considered"]
    exact_keys(checks, ("risk_free_curve", "commodity_prices", "fx_rates", "price_or_interest_indices"),
               "market_changes_considered")
    require(all([_known_flag(v, k) for k, v in checks.items()]), "market_changes_considered",
            "remaining relevant market movements must be assessed, including non-exposure where applicable",
            "REVIEW_REQUIRED")
    audit = {"approach": approach, "assessment_reference": evidence["assessment_reference"],
             "market_changes_considered": dict(checks), "input_value": value,
             "valuation_model_verified": False}
    if approach == "bottom_up":
        initial = evidence["initial_credit_spreads"]
        require(isinstance(initial, Mapping) and bool(initial), "initial_credit_spreads",
                "nonempty comparable initial-recognition spread points required")
        require(all(isinstance(k, str) and k.strip() for k in initial), "initial_credit_spreads",
                "nonempty matching basis identifiers required")
        applied = evidence["applied_credit_spreads"]
        exact_keys(applied, tuple(initial), "applied_credit_spreads")
        pairs = {key: (number(initial[key], key), number(applied[key], key)) for key in initial}
        require(all(a == b for a, b in pairs.values()), "applied_credit_spreads",
                "initial own-credit component must remain constant on the qualified comparable basis",
                "REVIEW_REQUIRED")
        audit["spread_points"] = {key: {"initial": a, "applied": b} for key, (a, b) in pairs.items()}
        audit["additional_own_credit_deduction"] = False
    else:
        require(not _known_flag(evidence["already_corrected"], "already_corrected"), "already_corrected",
                "do not correct an already adjusted value twice", "REVIEW_REQUIRED")
        result = valuation_liability_excluding_own_credit(value, evidence["cumulative_own_credit_change"],
            qualification_reference=evidence["assessment_reference"], context=context)
        value = result.value
        audit["correction"] = result.details
    return value, audit, ["DR:article-14:1", "VALUATION_GUIDANCE:guideline-5:1.17-1.20"]


@calculation("DR:article-16:1-7")
def valuation_method_checked_value(qualified_value: float, *, position_type: str,
                                   method: str, qualification_reference: str,
                                   conditions: Mapping[str, bool] | None = None,
                                   deposit_terms: Mapping | None = None,
                                   hierarchy: Mapping | None = None,
                                   own_credit: Mapping | None = None, context: Context):
    """Forward a value only on an explicitly supported Article16 method path.

The closed method vocabulary describes this component's supported scope; a
rejected unimplemented technique is not thereby declared unlawful. Required
cost flags mean material costs were assessed and adjusted where necessary.
The future deposit exception delegates its profile, threshold and override
checks to the existing component. No zero/default substitutes for missing data.
"""
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external position/method qualification required", "MISSING_INPUT")
    value = number(qualified_value, "qualified_value")
    require(isinstance(position_type, str) and position_type in _POSITION_METHODS,
            "position_type", "explicit supported non-TP position category required")
    require(isinstance(method, str) and method in _METHODS,
            "method", "explicit known valuation method required")
    require(method in _POSITION_METHODS[position_type], "method",
            "method excluded by Article16 or outside this component's documented scope", "UNSUPPORTED_METHOD")
    required = _CONDITIONS.get(position_type, ())
    if conditions is None:
        require(not required, "conditions", "explicit position conditions required", "MISSING_INPUT")
        conditions = {}
    exact_keys(conditions, required, "conditions")
    # Validate all declarations before deciding eligibility; unknown is not false.
    for key, flag in conditions.items():
        require(flag is not None, key, "external valuation condition unresolved", "REVIEW_REQUIRED")
        require(isinstance(flag, bool), key, "explicit boolean required")
    require(all(conditions.values()), "conditions", "required valuation condition not met", "UNSUPPORTED_METHOD")
    hierarchy_details = _hierarchy_control(hierarchy)
    deposit_details = None
    if position_type == "short_term_deposit" and method in ("cost", "amortised_cost"):
        require(hierarchy is None, "hierarchy", "deposit exception is not an ordinary Article10 valuation path")
        require(deposit_terms is not None, "deposit_terms", "explicit future exception inputs required", "MISSING_INPUT")
        exact_keys(deposit_terms, ("term_years", "small_non_complex", "no_material_valuation_error",
                                  "alternative_value"), "deposit_terms")
        result = valuation_short_term_deposit_cost_2027(
            value, method=method, qualification_reference=qualification_reference,
            context=context, **deposit_terms)
        value, deposit_details = result.value, result.details
    else:
        require(deposit_terms is None, "deposit_terms", "unused deposit exception inputs must be omitted")
    value, own_credit_details, own_credit_sources = _own_credit_control(value, own_credit, position_type, context)
    return value, {
        "position_type": position_type, "method": method, "conditions": dict(conditions),
        "deposit_exception": deposit_details,
        "hierarchy": hierarchy_details,
        "hierarchy_status": "NOT_CHECKED" if hierarchy is None else "DECLARED_ORDER_CHECKED",
        "own_credit": own_credit_details,
        "own_credit_status": "NOT_CHECKED" if own_credit is None else "DECLARED_TECHNIQUE_CHECKED",
        "_sources": ([] if hierarchy is None else ["DR:article-10:1-5"]) + own_credit_sources,
        "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "article16_supported_method_controls_not_valuation_recognition_or_full_method_approval",
    }
