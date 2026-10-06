"""Recoverables bounds; neither contract qualification nor default projection."""
import math
from fractions import Fraction
from typing import Mapping

from ._cashflows import payment_discount_factor
from .core import Context, calculation, exact_keys, number, require, scalar


@calculation("DR:article-56", "DR:article-57")
def reinsurance_recoverables_from_net(gross_best_estimate: float,
                                      unadjusted_net_best_estimate: float, *,
                                      proportionality_satisfied: bool | None,
                                      qualification_reference: str, context: Context):
    """Article57 signed gross-minus-net difference BEFORE expected default loss.

    The externally qualified net BE is based on homogeneous groups, each with
    at most one treaty/SPV unless homogeneous risks are transferred. Both BEs
    share scope/date/basis. Neither supplied BE includes the counterparty loss
    adjustment; apply the separate default-adjustment component afterwards.
    """
    _reference(qualification_reference, "qualification_reference")
    require(proportionality_satisfied is None or isinstance(proportionality_satisfied, bool),
            "proportionality_satisfied", "boolean or unresolved None required")
    require(proportionality_satisfied is not None, "proportionality_satisfied", "Article56 unresolved", "REVIEW_REQUIRED")
    require(proportionality_satisfied, "proportionality_satisfied", "Article56 not satisfied", "UNSUPPORTED_METHOD")
    gross = number(gross_best_estimate, "gross_best_estimate")
    net = number(unadjusted_net_best_estimate, "unadjusted_net_best_estimate")
    return gross - net, {"gross_best_estimate": gross, "unadjusted_net_best_estimate": net,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "counterparty_loss_adjustment_included": False, "recoverables_floored": False,
        "net_projection_model_generated": False, "scope": "article57_recoverables_before_default_adjustment"}


def _reference(value, field):
    require(isinstance(value, str) and bool(value.strip()), field,
            "nonempty external evidence reference required", "MISSING_INPUT")


@calculation("DR:article-56", "DR:article-61", "DIR:article-81")
def simplified_reinsurance_default_adjustment(probability_of_default: float, modified_duration: float,
                                               recoverables_best_estimate: float, *,
                                               proportionality_satisfied: bool | None,
                                               qualification_reference: str, context: Context):
    """Positive deduction corresponding to the printed negative Article61 AdjCD.

    One counterparty/homogeneous group; PD is next12months, duration and BE
    refer to the same recoverables. Not a counterparty-default SCR or projection.
    """
    _reference(qualification_reference, "qualification_reference")
    require(proportionality_satisfied is None or isinstance(proportionality_satisfied, bool),
            "proportionality_satisfied", "boolean or unresolved None required")
    require(proportionality_satisfied is not None, "proportionality_satisfied", "Article56 unresolved",
            "REVIEW_REQUIRED")
    require(proportionality_satisfied, "proportionality_satisfied", "Article56 conditions not satisfied",
            "UNSUPPORTED_METHOD")
    pd = number(probability_of_default, "probability_of_default", 0, 1)
    require(pd < 1, "probability_of_default", "PD1 makes printed denominator zero", "REVIEW_REQUIRED")
    duration = number(modified_duration, "modified_duration")
    be = number(recoverables_best_estimate, "recoverables_best_estimate")
    factor = number(scalar("reinsurance_simplified_default_factor", context), "factor", 0)
    fp, fd, fb, ff = map(lambda v: Fraction(str(v)), (pd, duration, be, factor))
    value = float(max(ff * fp / (1 - fp) * fd * fb, 0))
    return value, {"printed_signed_adjustment": -value, "sign_convention": "positive_deduction_from_recoverables",
                   "probability_of_default": pd, "modified_duration": duration,
                   "recoverables_best_estimate": be, "factor": factor,
                   "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
                   "scope": "article61_single_counterparty_homogeneous_group_adjustment_not_scr"}


@calculation("DR:article-41:4:a-b")
def reinsurance_nonlife_allocation(payments: Mapping[str, dict], *, target_provision: str,
                                    eligibility_reference: str, context: Context):
    """Allocate already eligible payments using their external gross-claims linkage.

    False means premium only after prior eligibility under Article 41: it is
    not permission to include settled claims, unrelated payments or deposits.
    Call separately for each date and homogeneous counterparty/LoB/type slice.
    """
    require(target_provision in ("nonlife_claims", "nonlife_premium"), "target_provision",
            "explicit nonlife claims or premium target required", "UNSUPPORTED_METHOD")
    _reference(eligibility_reference, "eligibility_reference")
    require(isinstance(payments, Mapping), "payments", "payment-labelled mapping required")
    require(bool(payments), "payments", "explicit payment or zero row required", "MISSING_INPUT")
    details, selected = {}, []
    for label, row in payments.items():
        require(isinstance(label, str) and bool(label.strip()), "payments", "nonempty payment identifier required")
        exact_keys(row, ("amount", "claim_in_gross_claims_provision"), label)
        amount = number(row["amount"], f"{label}.amount")
        linkage = row["claim_in_gross_claims_provision"]
        require(linkage is None or isinstance(linkage, bool), f"{label}.claim_in_gross_claims_provision",
                "explicit boolean or None required")
        require(linkage is not None, f"{label}.claim_in_gross_claims_provision",
                "unknown linkage cannot be assigned to premiums", "REVIEW_REQUIRED")
        provision = "nonlife_claims" if linkage else "nonlife_premium"
        included = provision == target_provision
        if included:
            selected.append(amount)
        details[label] = {"amount": amount, "claim_in_gross_claims_provision": linkage,
                          "provision_type": provision, "selected": included}
    return math.fsum(selected), {"payments": details, "target_provision": target_provision,
                                 "eligibility_reference": eligibility_reference,
                                 "eligibility_and_classification_status": "EXTERNAL_UNVERIFIED",
                                 "scope": "nonlife_allocation_only_not_payment_eligibility_or_valuation"}


def _projected_value(cashflows, partition, runoff_complete, projection_reference,
                     curve_reference, amount_key, context):
    """Value one externally classified partition; metadata is not proof of completeness."""
    exact_keys(partition, ("counterparty_id", "line_of_business", "contract_type", "provision_type"), "partition")
    for key in ("counterparty_id", "line_of_business"):
        _reference(partition[key], f"partition.{key}")
    require(partition["contract_type"] in ("spv", "finite_reinsurance", "other_reinsurance"),
            "partition.contract_type", "single supported contract type required", "UNSUPPORTED_METHOD")
    require(partition["provision_type"] in ("life", "nonlife_premium", "nonlife_claims"),
            "partition.provision_type", "single supported provision type required", "UNSUPPORTED_METHOD")
    require(runoff_complete is True, "runoff_complete", "explicit complete runoff declaration required", "MISSING_INPUT")
    _reference(projection_reference, "projection_reference")
    _reference(curve_reference, "curve_reference")
    require(isinstance(cashflows, Mapping), "cashflows", "date-labelled mapping required")
    require(bool(cashflows), "cashflows", "explicit cashflow or zero row required", "MISSING_INPUT")
    rows = {}
    for label, row in cashflows.items():
        exact_keys(row, (amount_key, "discount_factor"), label)
        amount = number(row[amount_key], f"{label}.{amount_key}")
        factor = payment_discount_factor(label, row["discount_factor"], context)
        rows[label] = {amount_key: amount, "discount_factor": factor,
                       "discounted_cashflow": number(amount * factor, f"{label}.discounted_cashflow")}
    return math.fsum(row["discounted_cashflow"] for row in rows.values()), {
        "partition": dict(partition), "cashflows": rows, "projection_reference": projection_reference,
        "curve_reference": curve_reference, "projection_curve_and_classification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DIR:article-81", "DR:article-41:2", "DR:article-41:4")
def reinsurance_recoverable_cashflows(cashflows: Mapping[str, dict], *, partition: Mapping[str, str],
                                      runoff_complete: bool, projection_reference: str,
                                      curve_reference: str, context: Context):
    """Discount externally selected expected recoveries at their own payment dates.

    Signed values remain signed. No gross-claim date substitution, default
    adjustment, SPV cap or claim/deposit qualification is performed implicitly.
    """
    value, details = _projected_value(cashflows, partition, runoff_complete, projection_reference,
                                      curve_reference, "expected_recovery", context)
    return value, {**details, "scope": "recoverable_present_value_before_default_adjustment_only"}


@calculation("DIR:article-81", "DR:article-42:1-3")
def reinsurance_default_adjustment(cashflows: Mapping[str, dict], *, partition: Mapping[str, str],
                                    runoff_complete: bool, projection_reference: str, curve_reference: str,
                                    noncollateral_mitigation_included: bool, context: Context,
                                    separate_noncollateral_mitigation: Mapping[str, dict] | None = None):
    """PV of already probability-weighted shortfalls; positive result is a deduction.

    Payment-date differences may be negative (e.g. delayed receipts), but a
    negative total needs review. Default times, PD, litigation and collateral
    effects must already be in the external projection: never multiply PD twice.
    """
    require(isinstance(noncollateral_mitigation_included, bool), "noncollateral_mitigation_included",
            "explicit boolean declaration required")
    require(not noncollateral_mitigation_included, "noncollateral_mitigation_included",
            "noncollateral mitigation must be excluded and recorded separately", "UNSUPPORTED_METHOD")
    separate = {}
    if separate_noncollateral_mitigation is not None:
        require(isinstance(separate_noncollateral_mitigation, Mapping),
                "separate_noncollateral_mitigation", "labelled instrument mapping required")
        for identifier, instrument in separate_noncollateral_mitigation.items():
            _reference(identifier, "mitigation_instrument_id")
            exact_keys(instrument, ("technique", "separately_valued_amount", "valuation_reference"), identifier)
            _reference(instrument["technique"], "technique")
            _reference(instrument["valuation_reference"], "valuation_reference")
            separate[identifier] = {**instrument,
                "separately_valued_amount": number(instrument["separately_valued_amount"], "separately_valued_amount")}
    value, details = _projected_value(cashflows, partition, runoff_complete, projection_reference,
                                      curve_reference, "expected_shortfall", context)
    require(value >= 0, "default_adjustment", "negative total requires separate assessment", "REVIEW_REQUIRED")
    return value, {**details, "sign_convention": "positive_deduction_from_recoverables",
                   "noncollateral_mitigation_included": False,
                   "separate_noncollateral_mitigation": separate,
                   "separate_mitigation_status": ("NOT_PROVIDED" if separate_noncollateral_mitigation is None
                       else "RECORDED_EXTERNAL_UNVERIFIED" if separate else "NONE_DECLARED"),
                   "separate_mitigation_added_to_recoverables": False,
                   "scope": "expected_shortfall_present_value_only_not_default_projection"}


@calculation("DR:article-41:2")
def spv_recoverable_cap(recoverable: float, aggregate_maximum_exposure: float, *,
                        exposure_reference: str | None = None, context: Context):
    """Cap one SPV's separately valued recoverable at its external aggregate exposure.

    Do not substitute collateral or sum unrelated counterparties here. Contract
    boundaries, basis risk and the exposure evidence remain external prerequisites.
    """
    claim = number(recoverable, "recoverable")
    require(claim >= 0, "recoverable", "negative recoverable needs separate assessment", "REVIEW_REQUIRED")
    cap = number(aggregate_maximum_exposure, "aggregate_maximum_exposure", 0)
    _reference(exposure_reference, "exposure_reference")
    result = min(claim, cap)
    return result, {"uncapped_recoverable": claim, "aggregate_maximum_exposure": cap,
                    "reduction": claim - result, "exposure_reference": exposure_reference,
                    "exposure_status": "EXTERNAL_UNVERIFIED",
                    "scope": "single_spv_cap_only_not_full_recoverables_valuation"}


@calculation("DR:article-42:4", "DIR:article-81")
def reinsurance_default_loss(recoverables_before_adjustment: float, estimated_loss: float, *,
                              method: str, valuation_reference: str | None = None, context: Context):
    """Apply the loss-given-default floor or an explicitly evidenced alternative.

    The minimum is not a point estimate and is not a probability of default.
    This result must not be used as the full expected default adjustment: its
    timing, probabilities and segmentation require a separate calculation.
    """
    recoverables = number(recoverables_before_adjustment, "recoverables_before_adjustment")
    require(recoverables >= 0, "recoverables_before_adjustment",
            "negative recoverables need separate assessment", "REVIEW_REQUIRED")
    estimate = number(estimated_loss, "estimated_loss", 0)
    require(method in ("standard_floor", "alternative_valuation"), "method", "explicit supported method required",
            "UNSUPPORTED_METHOD")
    if valuation_reference is not None or method == "alternative_valuation":
        _reference(valuation_reference, "valuation_reference")
    fraction = number(scalar("reinsurance_default_loss_floor", context), "reinsurance_default_loss_floor", 0, 1)
    floor = recoverables * fraction
    value = max(estimate, floor) if method == "standard_floor" else estimate
    return value, {"recoverables_before_adjustment": recoverables, "estimated_loss": estimate,
                   "standard_floor_fraction": fraction, "standard_floor": floor,
                   "floor_applied": method == "standard_floor", "method": method,
                   "valuation_reference": valuation_reference,
                   "valuation_status": "EXTERNAL_UNVERIFIED",
                   "scope": "loss_given_default_only_not_expected_default_adjustment"}
