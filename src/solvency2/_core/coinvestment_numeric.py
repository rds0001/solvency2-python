"""Article176c quantitative gates only; no IRB or insurer internal model."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, effective_resource, exact_keys, number, require
from .loss_given_default import _reference


@calculation("DR:article-176c:3:d:e", "DR:article-176c:4:e", unit="indicator")
def coinvestment_numeric_screen(revenue_currency_share: float, financial_years,
                                retentions: Mapping, *, qualification_reference: str, context: Context):
    """Check strict issuer size/revenue and inclusive retention for EACH security.

    Model approvals, contract requirements, CQS/PD mapping, consolidated issuer
    scope, fiscal-year selection and EUR conversion remain external. There is
    no averaging of retention across securities and no internal credit model.
    """
    _reference(qualification_reference, "qualification_reference")
    revenue = number(revenue_currency_share, "revenue_currency_share", 0, 1)
    source = effective_resource("profile.json", context)["scalars"]
    names = ("revenue_currency_min", "size_history_years", "turnover_min", "balance_sheet_min",
             "employees_min", "retention_min")
    parameters = {key: number(source["coinvestment_" + key]["value"], key, 0) for key in names}
    years = parameters["size_history_years"]
    require(years >= 1 and years.is_integer(), "size_history_years", "positive whole financial-year count",
            "RESOURCE_INTEGRITY")
    require(parameters["revenue_currency_min"] <= 1 and parameters["retention_min"] <= 1,
            "parameters", "profile ratio threshold outside[0,1]", "RESOURCE_INTEGRITY")
    require(isinstance(financial_years, (list, tuple)), "financial_years", "ordered fiscal-year rows required")
    require(len(financial_years) == int(years), "financial_years", "exact profile history required", "MISSING_INPUT")
    annual = []
    for index, row in enumerate(financial_years):
        field = "financial_years." + str(index)
        exact_keys(row, ("turnover_eur", "balance_sheet_total_eur", "employees"), field)
        values = {key: number(row[key], field + "." + key, 0) for key in row}
        routes = {"turnover": values["turnover_eur"] > parameters["turnover_min"],
                  "balance_sheet": values["balance_sheet_total_eur"] > parameters["balance_sheet_min"],
                  "employees": values["employees"] > parameters["employees_min"]}
        annual.append({**values, "size_routes": routes, "size_met": any(routes.values())})
    require(isinstance(retentions, Mapping), "retentions", "labelled security mapping required")
    require(bool(retentions), "retentions", "nonempty complete security set required", "MISSING_INPUT")
    audit = {}
    for label, row in retentions.items():
        require(isinstance(label, str) and bool(label.strip()), "security_id", "nonempty security ID required")
        exact_keys(row, ("nominal_value", "retained_nominal_value"), label)
        nominal = number(row["nominal_value"], label + ".nominal_value", 0)
        retained = number(row["retained_nominal_value"], label + ".retained_nominal_value", 0, nominal)
        require(nominal > 0, label + ".nominal_value", "positive nominal denominator required", "REVIEW_REQUIRED")
        ratio = Fraction(str(retained)) / Fraction(str(nominal))
        met = ratio >= Fraction(str(parameters["retention_min"]))
        display_ratio = float(ratio)
        require(display_ratio != 0 or ratio == 0, label + ".retention_share",
                "nonzero share underflows", "REVIEW_REQUIRED")
        audit[label] = {"nominal_value": nominal, "retained_nominal_value": retained,
                        "retention_share": display_ratio, "retention_met": met}
    revenue_met = revenue > parameters["revenue_currency_min"]
    return int(revenue_met and all(y["size_met"] for y in annual)
               and all(row["retention_met"] for row in audit.values())), {
        "revenue_currency_share": revenue, "revenue_share_met": revenue_met,
        "financial_years": annual, "retentions": dict(sorted(audit.items())), "parameters": parameters,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "internal_model_computed": False, "pd_or_cqs_mapping_performed": False,
        "all_article176c_conditions_verified": False,
        "scope": "quantitative176c3de4e_only_not_CQS_or_model_approval"}
