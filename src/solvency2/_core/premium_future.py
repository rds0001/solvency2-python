"""Future earned-premium cohort selection, separate from projection and discounting."""
from fractions import Fraction
from typing import Mapping

from .core import Context, calculation, exact_keys, number, require, scalar
from .loss_given_default import _reference


def _finite_total(value, field):
    try:
        result = float(value)
    except OverflowError:
        require(False, field, "component exceeds finite range", "REVIEW_REQUIRED")
    require(result != 0 or value == 0, field, "nonzero component underflows float range", "REVIEW_REQUIRED")
    return result


@calculation("DR:article-116:3:c:d", "DR:article-147:3:c:d")
def premium_future_component(contracts: Mapping, *, component: str,
        qualification_reference: str, context: Context):
    """Sum one selected net premium PV component, without long-term weighting.

    Month coordinates encode externally qualified calendar boundaries. Premium
    rows must be split at relevant earning cutoffs; payment time is not earning
    time. Input PVs already include expectations, eligible netting and discounting.
    The downstream premium-volume APIs apply the30% long-contract factor once.
    """
    components = ("existing_future_pv", "future_short_pv", "future_long_pv")
    require(isinstance(component, str) and component in components, "component",
            "explicit unweighted premium component required", "UNSUPPORTED_METHOD")
    _reference(qualification_reference, "qualification_reference")
    window = number(scalar("premium_projection_window_months", context), "projection_window", 0)
    short_term = number(scalar("premium_short_contract_max_months", context), "short_contract_max", 0)
    exclusion = number(scalar("premium_short_earning_exclusion_months", context), "short_exclusion", 0)
    require(window > 0 and short_term > 0 and exclusion > 0, "premium_time_parameters",
            "strictly positive month boundaries required")
    require(isinstance(contracts, Mapping), "contracts", "labelled contract mapping required")
    totals = dict.fromkeys(components, Fraction(0))
    audit = {}
    for contract_id, contract in contracts.items():
        require(isinstance(contract_id, str) and bool(contract_id.strip()), "contract_id", "nonempty ID required")
        exact_keys(contract, ("recognition_month", "original_term_months", "premiums"), contract_id)
        recognition = number(contract["recognition_month"], contract_id + ".recognition_month")
        term = number(contract["original_term_months"], contract_id + ".original_term_months", 0)
        premiums = contract["premiums"]
        require(isinstance(premiums, Mapping), contract_id + ".premiums", "labelled premium mapping required")
        if recognition <= 0:
            selected_component, cutoff = "existing_future_pv", Fraction(str(window))
        elif recognition > window:
            selected_component, cutoff = None, None
        elif term <= short_term:
            selected_component = "future_short_pv"
            cutoff = Fraction(str(recognition)) + Fraction(str(exclusion))
        else:
            selected_component, cutoff = "future_long_pv", Fraction(str(window))
        entries = {}
        for premium_id, row in premiums.items():
            require(isinstance(premium_id, str) and bool(premium_id.strip()), "premium_id", "nonempty ID required")
            field = contract_id + ".premiums." + premium_id
            exact_keys(row, ("earned_month", "present_value"), field)
            earned = number(row["earned_month"], field + ".earned_month")
            pv = number(row["present_value"], field + ".present_value")
            require(recognition <= 0 or earned >= recognition, field,
                    "pre-recognition earning on future contracts requires separate qualification", "REVIEW_REQUIRED")
            included = selected_component is not None and Fraction(str(earned)) > cutoff
            if included:
                totals[selected_component] += Fraction(str(pv))
            entries[premium_id] = {"earned_month": earned, "present_value": pv,
                                  "selected_component": selected_component if included else None}
        audit[contract_id] = {"recognition_month": recognition, "original_term_months": term,
            "cohort_component": selected_component,
            "premiums": dict(sorted(entries.items()))}
    values = {key: _finite_total(total, key) for key, total in totals.items()}
    return values[component], {
        "component": component, "component_values": values, "contracts": dict(sorted(audit.items())),
        "projection_window_months": window, "short_contract_max_months": short_term,
        "short_earning_exclusion_months": exclusion,
        "long_contract_weight_applied": False, "negative_premiums_floored": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "premium_projection_performed": False, "discounting_performed": False,
        "calendar_conversion_performed": False, "reinsurance_eligibility_verified": False,
        "scope": "earned_time_cohort_selection_of_qualified_net_premium_PVs_only"}
