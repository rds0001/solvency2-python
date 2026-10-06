"""Separate life/SLT-health sources sharing strict TP-increase selection arithmetic."""
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require
from .loss_given_default import _known_flag, _reference


def _biometric_selection(shock: str, valuations: Mapping, *, valuation_basis: str,
        grouping_mode: str, grouping_qualified: bool | None = None,
        valuation_reference: str, article: str):
    """Count strictly TP-increasing units and retain the complete selection mask.

    TP excludes risk margin in both scenarios. Under reinsurance this comparison
    concerns underlying insurance, never a net reinsurance-treaty valuation.
    Qualifying group formation and equivalence are externally assessed, not
    inferred from summed TP or a common label. Count means units, not contracts.
    """
    require(isinstance(shock, str) and shock in ("mortality", "longevity"), "shock",
            "mortality or longevity selection rule required", "UNSUPPORTED_METHOD")
    require(isinstance(valuation_basis, str) and valuation_basis in
            ("direct_insurance_contracts", "underlying_insurance_contracts"), "valuation_basis",
            "direct or underlying insurance contracts required; not reinsurance treaties", "UNSUPPORTED_METHOD")
    require(isinstance(grouping_mode, str) and grouping_mode in ("individual", "same_insured", "article35"),
            "grouping_mode", "explicit permitted grouping basis required", "UNSUPPORTED_METHOD")
    _reference(valuation_reference, "valuation_reference")
    if grouping_mode == "individual":
        require(grouping_qualified is None, "grouping_qualified", "unused for individual contracts; omit")
    else:
        require(_known_flag(grouping_qualified, "grouping_qualified"), "grouping_qualified",
                "same-insured or Article35/equivalent-selection grouping must be externally qualified",
                "REVIEW_REQUIRED")
    require(isinstance(valuations, Mapping), "valuations", "labelled valuation-unit mapping required")
    require(bool(valuations), "valuations", "explicit nonempty valuation-unit set required", "MISSING_INPUT")
    values, selected = {}, {}
    for label, row in valuations.items():
        require(isinstance(label, str) and bool(label.strip()), "valuation_unit", "nonempty unit ID required")
        exact_keys(row, ("base_tp_excluding_risk_margin", "stressed_tp_excluding_risk_margin"), label)
        base = number(row["base_tp_excluding_risk_margin"], label + ".base_tp_excluding_risk_margin")
        stressed = number(row["stressed_tp_excluding_risk_margin"], label + ".stressed_tp_excluding_risk_margin")
        values[label] = {"base_tp_excluding_risk_margin": base, "stressed_tp_excluding_risk_margin": stressed}
        # Compare finite signed values directly: even a representable pair can
        # have an unrepresentable difference, and zero tolerance is intentional.
        selected[label] = stressed > base
    return sum(selected.values()), {
        "shock": shock, "valuation_basis": valuation_basis, "grouping_mode": grouping_mode,
        "grouping_qualified": grouping_qualified, "valuation_unit_count": len(values),
        "valuations": dict(sorted(values.items())), "selection_mask": dict(sorted(selected.items())),
        "selected_units": sorted(label for label, flag in selected.items() if flag),
        "excluded_units": sorted(label for label, flag in selected.items() if not flag),
        "valuation_reference": valuation_reference, "valuation_status": "EXTERNAL_UNVERIFIED",
        "group_membership_or_equivalence_verified": False, "contract_count_inferred": False,
        "tp_valuation_performed": False, "capital_charge_computed": False,
        "scope": "strict_TP_increase_selection_on_declared_qualified_units_only",
        "_sources": ["DR:article-" + article + ":2", "DR:article-" + article + ":3"]}


@calculation("DR:articles-137-138:2-3", unit="selection_units")
def life_biometric_selection(shock: str, valuations: Mapping, *, valuation_basis: str,
        grouping_mode: str, grouping_qualified: bool | None = None,
        valuation_reference: str, context: Context):
    """Select qualified life units by strictly increased TP excluding risk margin.

    Direct/underlying basis, grouping and external TP valuation requirements
    are unchanged; the shared private helper does not contribute health sources.
    """
    return _biometric_selection(shock, valuations, valuation_basis=valuation_basis,
        grouping_mode=grouping_mode, grouping_qualified=grouping_qualified,
        valuation_reference=valuation_reference, article="137" if shock == "mortality" else "138")


@calculation("DR:articles-152-153:2-3", unit="selection_units")
def health_biometric_selection(shock: str, valuations: Mapping, *, valuation_basis: str,
        grouping_mode: str, grouping_qualified: bool | None = None,
        valuation_reference: str, context: Context):
    """Select already qualified SLT-health units; no health TP projection or SCR.

    Under reinsurance, units represent underlying insurance, not treaty TP.
    The result counts valuation units, never infers the number of contracts.
    """
    return _biometric_selection(shock, valuations, valuation_basis=valuation_basis,
        grouping_mode=grouping_mode, grouping_qualified=grouping_qualified,
        valuation_reference=valuation_reference, article="152" if shock == "mortality" else "153")
