"""Future SFCR declaration screens, not report production or audit certification."""
from fractions import Fraction

from .core import Context, calculation, number, require, scalar
from .evidence import _declared_bool, _reference


@calculation("DIR:article-51:3-4", unit="indicator")
def sfcr_captive_disclosure_conditions_2027(captive_type: str, permitted_policyholders: bool,
                                            natural_person_tp_share: float, no_compulsory_liability: bool, *,
                                            group_loans_asset_share: float | None = None,
                                            maximum_loss_deterministic: bool | None = None,
                                            qualification_reference: str, context: Context):
    """Declared captive relief conditions, distinct from ORSA/reporting relief.

    Captive status, beneficiary qualification, loan/cash-pool scope and the
    deterministic maximum-loss assessment are external. Reinsurance liability
    exclusion concerns the underlying insurance contracts, not only the treaty.
    """
    require(captive_type in ("insurance", "reinsurance"), "captive_type",
            "externally qualified insurance or reinsurance captive required", "UNSUPPORTED_PARAMETER")
    _reference(qualification_reference, "qualification_reference")
    permitted = _declared_bool(permitted_policyholders, "permitted_policyholders")
    liability = _declared_bool(no_compulsory_liability, "no_compulsory_liability")
    share = number(natural_person_tp_share, "natural_person_tp_share", 0, 1)
    limit = number(scalar("sfcr_captive_natural_person_share_limit", context), "natural_person_share_limit", 0, 1)
    conditions = {"permitted_policyholders": permitted, "no_compulsory_liability": liability,
                  "natural_person_share_below_limit": Fraction(str(share)) < Fraction(str(limit))}
    loans = loan_limit = deterministic = None
    if captive_type == "reinsurance":
        loans = number(group_loans_asset_share, "group_loans_asset_share", 0, 1)
        loan_limit = number(scalar("sfcr_captive_reinsurance_group_loans_asset_share_limit", context),
                            "group_loans_asset_share_limit", 0, 1)
        deterministic = _declared_bool(maximum_loss_deterministic, "maximum_loss_deterministic")
        conditions["group_loans_within_limit"] = Fraction(str(loans)) <= Fraction(str(loan_limit))
        conditions["maximum_loss_deterministic"] = deterministic
    else:
        require(group_loans_asset_share is None and maximum_loss_deterministic is None,
                "reinsurance_only_inputs", "omit unused reinsurance-only inputs")
    return int(all(conditions.values())), {
        "captive_type": captive_type, "conditions": conditions,
        "natural_person_tp_share": share, "natural_person_share_limit": limit,
        "group_loans_asset_share": loans, "group_loans_asset_share_limit": loan_limit,
        "maximum_loss_deterministic": deterministic,
        "quantitative_professional_disclosure_still_required": True,
        "blanket_reporting_waiver": False, "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "declared_article51_captive_disclosure_relief_conditions_only",
        "_sources": ["DIR:article-51:4" if captive_type == "reinsurance" else "DIR:article-51:3"],
    }


@calculation("DIR:article-51a:1-3", unit="indicator")
def sfcr_balance_sheet_audit_required_2027(small_non_complex: bool, captive: bool,
                                          national_extension_applies: bool, *,
                                          qualification_reference: str, context: Context):
    """Select the balance-sheet audit duty, not the complete audit perimeter.

    Captive classification is not conditional on Article51 disclosure relief.
    The caller must qualify national extensions explicitly; no default national
    rule, automatic legal research or audit-content approval is inferred.
    """
    _reference(qualification_reference, "qualification_reference")
    snc = _declared_bool(small_non_complex, "small_non_complex")
    qualified_captive = _declared_bool(captive, "captive")
    national = _declared_bool(national_extension_applies, "national_extension_applies")
    required = not (snc or qualified_captive) or national
    return int(required), {
        "small_non_complex": snc, "captive": qualified_captive,
        "national_extension_applies": national, "balance_sheet_audit_required": required,
        "other_report_element_audit_duties_determined": False,
        "auditor_qualification_verified": False, "audit_performed_verified": False,
        "separate_audit_report_verified": False, "blanket_reporting_waiver": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "article51a_balance_sheet_audit_applicability_only",
    }
