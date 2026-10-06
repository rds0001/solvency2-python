"""Technical-provision components from explicitly external projections and method decisions."""
import math
from typing import Mapping

from ._cashflows import payment_discount_factor
from .core import Context, calculation, effective_resource, exact_keys, number, require


def _directive_source(context, article):
    """Bind unchanged arithmetic to the explicitly selected directive version."""
    profile = effective_resource("profile.json", context)
    return context.profile_id + ":" + profile["sources"]["DIR"]["sha256"] + ":" + article


@calculation("DR:article-35", unit="indicator")
def life_cashflow_grouping_conditions(conditions: Mapping[str, bool], *,
                                      qualification_reference: str, context: Context):
    """Check declared Article35 grouping safeguards, not a clustering model.

    Individual-contract projection is the default. The insurer assesses undue
    burden, risk similarity, faithful expenses/risks and comparable best estimates
    including guarantees/options. No quantitative materiality cutoff is invented.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external actuarial qualification reference required", "MISSING_INPUT")
    keys = ("individual_projection_unduly_burdensome", "risk_nature_complexity_not_materially_different",
            "risks_and_expenses_not_misrepresented", "best_estimates_approximately_equivalent_including_options")
    exact_keys(conditions, keys, "conditions")
    for key in keys:
        require(conditions[key] is not None, key, "actuarial qualification unresolved", "REVIEW_REQUIRED")
        require(isinstance(conditions[key], bool), key, "explicit boolean required")
    profile = effective_resource("profile.json", context)
    return int(all(conditions.values())), {
        "conditions": dict(conditions), "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "groups_generated": False,
        "default_projection_basis": "INDIVIDUAL_CONTRACT", "materiality_threshold_invented": False,
        "scope": "declared_article35_grouping_conditions_not_projection_or_approval",
        "_sources": [context.profile_id + ":" + profile["sources"]["DR"]["sha256"] + ":article-35"]}


@calculation("DR:article-40:2-4", "DIR:article-77:4")
def replicated_cashflow_value(market_values: Mapping[str, float], *,
                               cashflow_features: Mapping[str, bool | None],
                               replication_reference: str | None = None,
                               market_reference: str | None = None, context: Context):
    """Market-value arithmetic with mandatory exclusions, not replication approval.

    Features concern the selected cashflows. References to all-scenario and
    market evidence are retained but their substantive adequacy is external.
    """
    keys = ("policyholder_options", "biometric_dependency", "future_servicing_expenses")
    exact_keys(cashflow_features, keys, "cashflow_features")
    for key in keys:
        require(cashflow_features[key] is None or isinstance(cashflow_features[key], bool),
                key, "explicit boolean or None required")
    excluded = [key for key in keys if cashflow_features[key] is True]
    require(not excluded, "cashflow_features", f"Article 40(2) exclusions: {excluded}",
            "REPLICATION_EXCLUDED")
    unknown = [key for key in keys if cashflow_features[key] is None]
    require(not unknown, "cashflow_features", f"unresolved cashflow features: {unknown}", "REVIEW_REQUIRED")
    for key, reference in (("replication_reference", replication_reference), ("market_reference", market_reference)):
        require(isinstance(reference, str) and bool(reference.strip()), key,
                "nonempty external qualification reference required", "MISSING_INPUT")
    require(isinstance(market_values, Mapping), "market_values", "position-labelled mapping required")
    require(bool(market_values), "market_values", "explicit positions required", "MISSING_INPUT")
    values = {}
    for key, value in market_values.items():
        require(isinstance(key, str) and bool(key.strip()), "market_values", "nonempty position identifier required")
        values[key] = number(value, f"market_values.{key}")
    return math.fsum(values.values()), {
        "market_values": values, "cashflow_features": dict(cashflow_features),
        "replication_reference": replication_reference, "market_reference": market_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED", "scope": "market_value_arithmetic_only"}


@calculation("DIR:article-77:2")
def best_estimate_cashflows(cashflows: Mapping[str, dict], *, runoff_complete: bool,
                            cashflow_reference: str, curve_reference: str, context: Context):
    """Discount already probability-weighted, gross-of-reinsurance cashflows.

    No projection model, curve interpolation or compounding convention is
    invented here. Discount factors must match the payment dates and currency.
    Inflows include premiums, not separately valued reinsurance recoverables.
    """
    require(runoff_complete is True, "runoff_complete", "explicit complete runoff declaration required",
            "MISSING_INPUT")
    for key, reference in (("cashflow_reference", cashflow_reference), ("curve_reference", curve_reference)):
        require(isinstance(reference, str) and bool(reference.strip()), key,
                "nonempty external reference required", "MISSING_INPUT")
    require(isinstance(cashflows, Mapping), "cashflows", "date-labelled mapping required")
    require(bool(cashflows), "cashflows", "explicit cashflow or zero row required", "MISSING_INPUT")
    details = {}
    for label, row in cashflows.items():
        exact_keys(row, ("expected_inflows", "expected_outflows", "discount_factor"), label)
        inflow = number(row["expected_inflows"], f"{label}.expected_inflows", 0)
        outflow = number(row["expected_outflows"], f"{label}.expected_outflows", 0)
        factor = payment_discount_factor(label, row["discount_factor"], context)
        net = outflow - inflow
        discounted = number(net * factor, f"{label}.discounted_cashflow")
        details[label] = {"net_expected_outflow": net, "discount_factor": factor,
                          "discounted_cashflow": discounted}
    return math.fsum(row["discounted_cashflow"] for row in details.values()), {
        "cashflows": details, "cashflow_reference": cashflow_reference, "curve_reference": curve_reference,
        "projection_and_curve_status": "EXTERNAL_UNVERIFIED",
        "_sources": [_directive_source(context, "article-77-2")],
        "scope": "expected_gross_cashflows_only_recoverables_separate"}


@calculation("DIR:article-77:1", "DIR:article-77:4")
def technical_provisions_sum(best_estimate: float, risk_margin: float, *,
                              replication_applies: bool, context: Context):
    """Separate BE/RM method only; negative best estimates/total provisions are not floored."""
    require(isinstance(replication_applies, bool), "replication_applies", "explicit method decision required")
    require(not replication_applies, "replication_applies", "use replicated_cashflow_value for the replication method, not BE+RM",
            "UNSUPPORTED_METHOD")
    be = number(best_estimate, "best_estimate")
    margin = number(risk_margin, "risk_margin", 0)
    return math.fsum((be, margin)), {"best_estimate": be, "risk_margin": margin,
                                    "_sources": [_directive_source(context, "article-77-1-4")],
                                    "valuation_method": "SEPARATE_BE_AND_RM",
                                    "method_applicability": "EXTERNAL_UNVERIFIED"}
