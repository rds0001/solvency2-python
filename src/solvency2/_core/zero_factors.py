"""Narrow zero-factor gates, never implicit exemptions from other risk modules."""
from collections.abc import Mapping
from fractions import Fraction

from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DR:article-180:2:subparagraphs-3-5")
def partial_public_guarantee_zero_amount_2027(positions: Mapping[str, dict], *, category: str,
        first_loss_cover: float, guarantee_value: float, conditions: Mapping[str, bool],
        qualification_reference: str, allocation_reference: str, context: Context):
    """Validate explicit zero-treatment allocation, not guarantee pricing or capital.

    Nominal first-loss coverage and the externally determined guarantee value
    are distinct inputs. Pool allocation is chosen by the analyst, never here.
    Article215(f) payment coverage remains part of external qualification.
    """
    require(category in ("single", "pool"), "category", "explicit single/pool classification required")
    details = _qualified_conditions(conditions, ("guarantor_qualifies_under_a_to_d", "unconditional",
        "irrevocable", "first_loss_guarantee", "article215_compliant"), qualification_reference)
    require(isinstance(allocation_reference, str) and bool(allocation_reference.strip()),
            "allocation_reference", "explicit allocation/guarantee valuation reference required", "MISSING_INPUT")
    require(isinstance(positions, Mapping) and bool(positions), "positions", "nonempty labelled positions required", "MISSING_INPUT")
    require(category != "single" or len(positions) == 1, "positions", "single exposure requires exactly one position")
    nominal_total, value_total, allocated_total = Fraction(0), Fraction(0), Fraction(0)
    normalized = {}
    for label, row in positions.items():
        require(isinstance(label, str) and bool(label.strip()), "positions", "nonempty position IDs required")
        exact_keys(row, ("nominal", "value", "zero_amount"), label)
        nominal = number(row["nominal"], f"{label}.nominal", 0)
        value = number(row["value"], f"{label}.value", 0)
        allocated = number(row["zero_amount"], f"{label}.zero_amount", 0, value)
        # Exact decimal comparison: .1 + .2 allocations equal an input .3.
        # No hidden rounding tolerance changes the required guarantee total.
        nominal_total += Fraction(str(nominal))
        value_total += Fraction(str(value))
        allocated_total += Fraction(str(allocated))
        normalized[label] = {"nominal": nominal, "value": value, "zero_amount": allocated,
            "remaining_value": float(Fraction(str(value)) - Fraction(str(allocated)))}
    require(nominal_total > 0, "positions", "strictly positive total nominal exposure required")
    first_loss = number(first_loss_cover, "first_loss_cover", 0)
    guarantee = number(guarantee_value, "guarantee_value", 0)
    nominal_cover = Fraction(str(first_loss))
    require(nominal_cover <= nominal_total, "first_loss_cover", "coverage cannot exceed nominal exposure")
    threshold = number(scalar("partial_public_guarantee_minimum_first_loss", context), "minimum_first_loss", 0, 1)
    require(nominal_cover >= Fraction(str(threshold)) * nominal_total, "first_loss_cover",
            "minimum nominal first-loss coverage not established", "REVIEW_REQUIRED")
    require(allocated_total == Fraction(str(guarantee)), "guarantee_value",
            "explicit allocated amounts must exactly equal external guarantee value")
    return float(allocated_total), {**details, "category": category, "positions": normalized,
        "nominal_total": number(float(nominal_total), "nominal_total", 0),
        "exposure_value_total": number(float(value_total), "exposure_value_total", 0),
        "first_loss_cover": first_loss, "minimum_first_loss_ratio": threshold,
        "guarantee_value": guarantee, "allocation_reference": allocation_reference,
        "remaining_exposure_value": float(value_total - allocated_total),
        "scope": "zero_treatment_eligible_exposure_amount_only_not_SCR_or_guarantee_valuation"}


PUBLIC_CONDITIONS = {
    "ecb": (), "mdb_crr117_2": (), "international_crr118": (),
    "member_state_central_government_bank": ("denominated_domestic", "funded_domestic"),
    "guaranteed_qualifying_public": ("full", "unconditional", "irrevocable", "article215_compliant",
                                     "guarantor_qualifies_under_a_to_d"),
    "guaranteed_listed_regional_local": ("full", "unconditional", "irrevocable", "article215_compliant",
                                       "listed_2015_2011", "denominated_domestic", "funded_domestic"),
}


def _qualified_conditions(conditions, fields, reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external issuer/guarantee/legal classification evidence required", "MISSING_INPUT")
    exact_keys(conditions, fields, "conditions")
    for field in fields:
        require(isinstance(conditions[field], bool), f"conditions.{field}", "explicit boolean condition required")
    failed = [field for field in fields if not conditions[field]]
    require(not failed, "conditions", f"zero treatment not established: {failed}; choose applicable alternative rule explicitly",
            "REVIEW_REQUIRED")
    return {"conditions": dict(conditions), "qualification_reference": reference, "qualification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DR:article-180:2", "DR:article-187:3", unit="ratio")
def public_exposure_zero_factor(category: str, conditions: Mapping[str, bool], *,
                                qualification_reference: str, context: Context):
    """Shared public-factor rule; Art180 debt scope and Art187 scope remain distinct.

    Public-body/list classification and underlying guarantee assessment are
    external evidence, not conclusions drawn from these supplied booleans.
    The future-only308b(12) category concerns the position's inception, not
    merely the security's issue date; it does not extend public guarantees.
    """
    transition = category == "member_state_pre2023_member_currency"
    require(isinstance(category, str) and (category in PUBLIC_CONDITIONS or transition),
            "category", "supported public exposure classification required", "UNSUPPORTED_METHOD")
    if transition:
        future = effective_resource("profile.json", context).get("methods", {}).get("concentration_rules") == "2027"
        require(future, "category", "DIR308b(12) currency treatment requires the2027 profile", "UNSUPPORTED_METHOD")
        fields = ("incurred_before_2023_01_01", "denominated_member_state_currency", "funded_same_currency")
    else:
        fields = PUBLIC_CONDITIONS[category]
    details = _qualified_conditions(conditions, fields, qualification_reference)
    if transition:
        details.update({"transition_cutoff_exclusive": "2023-01-01",
                        "_sources": ["DIR:article-308b:12"]})
    value = number(scalar("public_exposure_zero_factor", context), "public_exposure_zero_factor", 0, 1)
    return value, {**details, "category": category,
        "scope": "qualified_180_2_debt_stress_or_187_3_concentration_factor_only"}


@calculation("DR:article-187:5", unit="ratio")
def insured_deposit_concentration_factor(conditions: Mapping[str, bool], *,
                                          qualification_reference: str, context: Context):
    """Deposit guarantee concentration gi only; no default/spread risk exemption."""
    details = _qualified_conditions(conditions, ("fully_eu_deposit_guaranteed", "unrestricted", "no_double_count"),
                                    qualification_reference)
    value = number(scalar("insured_deposit_concentration_factor", context), "insured_deposit_concentration_factor", 0, 1)
    return value, {**details, "scope": "insured_deposit_concentration_gi_only_not_default_or_spread_exemption"}


@calculation("DR:article-180:10", unit="ratio")
def guaranteed_sts_securitisation_spread_stress(conditions: Mapping[str, bool], *,
                                               qualification_reference: str,
                                               transition: Mapping[str, bool] | None = None,
                                               context: Context):
    """Qualified Article180(10)/(10a) factor; historical name retained for callers.

    The 2027 text no longer separately names STS; CRR243 compliance remains
    required and externally qualified, not inferred from a non-STS declaration.
    Paragraph10a requires external pre-2019 issue and exact 2018-rule assessment,
    not a current type label or an engine-generated historical classification.
    """
    future = effective_resource("profile.json", context).get("methods", {}).get("securitisation_rules") == "2027"
    if transition is not None:
        exact_keys(conditions, (), "conditions")
        details = _qualified_conditions(transition, ("issued_before_2019", "qualified_under_2018_article180_10"),
                                        qualification_reference)
        details["transition"] = details.pop("conditions")
        scope = "qualified_180_10a_historical_transition_factor_only"
    else:
        fields = ("eligible_eif_or_eib_guarantor", "full", "unconditional", "irrevocable", "article215_compliant",
                  "crr243_compliant")
        # Accept the old informational STS flag in 2027 for compatibility,
        # but do not impose an additional gate removed from that version.
        if future and isinstance(conditions, Mapping) and "sts_qualified" in conditions:
            require(isinstance(conditions["sts_qualified"], bool), "conditions.sts_qualified",
                    "optional legacy STS field must be a boolean")
            sts_declaration = conditions["sts_qualified"]
            effective = {k: v for k, v in conditions.items() if k != "sts_qualified"}
        else:
            sts_declaration = None
            effective = conditions
        details = _qualified_conditions(effective, fields if future else (*fields, "sts_qualified"),
                                        qualification_reference)
        if future:
            details["legacy_sts_declaration"] = sts_declaration
        scope = "qualified_180_10_factor_only"
    value = number(scalar("guaranteed_sts_spread_factor", context), "guaranteed_sts_spread_factor", 0, 1)
    return value, {**details, "scope": scope, "historical_classification_verified": False,
                   "separate_sts_condition_required": not future and transition is None,
                   "_sources": ["DR:article-180:10a"] if transition is not None else []}
