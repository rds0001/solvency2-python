"""Article176c joins externally owned model outputs to the standard spread factor.

This is an evidence contract, not an IRB/internal model or an automatic mapping
method. The undertaking remains responsible for prudent adjustments and CQS.
"""
from .core import exact_keys, require, number, effective_resource
from .loss_given_default import _reference
from .coinvestment_numeric import coinvestment_numeric_screen


CONDITIONS = (
    "coinvestment_agreement", "qualified_coinvestor", "unrated_without_article214_collateral",
    "model_outputs_shared", "issuer_outside_own_group", "issuer_not_excluded_type",
    "issuer_eea_domiciled", "types_and_criteria_defined", "underwriting_details_shared",
    "all_applications_shared", "all_decisions_shared", "same_underwriting_process",
    "all_approved_investments_taken", "model_description_scope_and_validation_shared",
    "latest_model_output", "spread_capital_appropriate",
)
FACTORS = ("default_definition", "time_horizon", "category_meaning_and_position",
           "item_credit_quality", "long_run_default_estimate", "internal_mapping", "other_relevant_information")


def _confirmed(values, names, field):
    exact_keys(values, names, field)
    for key, value in values.items():
        require(type(value) is bool, field + "." + key, "explicit known boolean required", "REVIEW_REQUIRED")
        require(value, field + "." + key, "176c condition not met", "UNSUPPORTED_METHOD")


def coinvestment_evidence(data, target_cqs, context):
    exact_keys(data, ("route", "numeric_inputs", "conditions", "model_cqs", "model_reference",
                      "qualification_reference", "pd_mapping"), "coinvestment")
    require(data["route"] in ("bank_irb", "insurer_internal_model"), "route", "explicit176c1b route required")
    for name in ("model_reference", "qualification_reference"):
        _reference(data[name], name)
    require(isinstance(data["model_cqs"], str) and data["model_cqs"] in tuple(map(str, range(7))),
            "model_cqs", "externally assigned Solvency-II CQS0..6 required")
    require(data["model_cqs"] == target_cqs, "model_cqs", "spread CQS must equal external assigned CQS")
    _confirmed(data["conditions"], CONDITIONS, "conditions")
    exact_keys(data["numeric_inputs"], ("revenue_currency_share", "financial_years", "retentions"), "numeric_inputs")
    numeric = coinvestment_numeric_screen(**data["numeric_inputs"],
        qualification_reference=data["qualification_reference"], context=context)
    require(numeric.value == 1, "numeric_inputs", "176c quantitative criteria not met", "UNSUPPORTED_METHOD")
    mapping = None
    sources = ["DR:article-176c", *numeric.sources]
    if data["route"] == "insurer_internal_model":
        require(data["pd_mapping"] is None, "pd_mapping", "insurer CQS is adopted directly; no bank mapping")
    else:
        mapping = data["pd_mapping"]
        exact_keys(mapping, ("reported_pd", "adjusted_three_year_pd", "mapping_reference",
            "adjustment_reference", "qualitative_factor_references", "confirmations"), "pd_mapping")
        for name in ("mapping_reference", "adjustment_reference"):
            _reference(mapping[name], "pd_mapping." + name)
        for name in ("reported_pd", "adjusted_three_year_pd"):
            number(mapping[name], "pd_mapping." + name, 0, 1)
        exact_keys(mapping["qualitative_factor_references"], FACTORS, "qualitative_factor_references")
        for name, reference in mapping["qualitative_factor_references"].items():
            _reference(reference, "qualitative_factor_references." + name)
        _confirmed(mapping["confirmations"], ("mapping_documented", "annex_i_table1_basis",
            "prudent_qualitative_adjustments", "material_horizon_difference_adjusted",
            "material_default_definition_difference_adjusted"), "pd_mapping.confirmations")
        table = effective_resource("profile.json", context)["tables"]["coinvestment_pd_benchmarks"]
        mapping = {**mapping, "benchmark_table": table,
                   "mapping_status": "EXTERNAL_UNVERIFIED_NOT_AUTOMATIC_INTERVAL_ASSIGNMENT"}
        sources.extend([table["source"], "ITS2016_1799:article-4:2:4", "ITS2016_1799:article-7"])
    return {"route": data["route"], "assigned_cqs": data["model_cqs"], "conditions": data["conditions"],
            "numeric_screen": {"value": numeric.value, "details": numeric.details}, "pd_mapping": mapping,
            "model_reference": data["model_reference"], "qualification_reference": data["qualification_reference"],
            "qualification_status": "EXTERNAL_UNVERIFIED", "internal_model_computed": False,
            "pd_adjustment_or_mapping_computed": False}, sources
