"""Solvency II reference components. No complete regulatory engine is released yet."""
from importlib.metadata import PackageNotFoundError, version

from .aggregation import (aggregate_risk, basic_scr, catastrophe_region_aggregation, catastrophe_weighted_sum,
                          catastrophe_zone_aggregation,
                          scenario_loss, select_scenario)
from .capital import (intangible_risk, lac_dt, lac_dt_stress_amount, lac_tp, mcr_absolute_floor, mcr_capital_at_risk,
                      mcr_combined, mcr_life, mcr_linear, mcr_nonlife, operational_risk, risk_margin,
                      scr_standard_formula)
from .core import CalculationError, Context, NumericOverride, Result, parameter
from .equity_position import equity_stress_amount_2027
from .future_scope import (significant_cross_border_activity_2027,
                           group_insurance_holding_conditions_2027,
                           group_long_term_equity_limit_2027,
                           public_counter_guarantee_conditions_2027,
                           proportionality_application_evidence_2027)
from .underwriting_simplified import simplified_longevity_risk, simplified_expense_risk
from .underwriting_simplified import simplified_lapse_risk
from .own_funds import own_funds_tier1_loss_absorption_trigger
from .own_funds import own_funds_tier1_mechanism_requirements
from .restricted_portfolios import restricted_portfolio_scenario_charge, restricted_portfolio_scr_sum
from .reinsurance import simplified_reinsurance_default_adjustment
from .own_funds import own_funds_step_up_limit
from .own_funds import own_funds_classification_evidence_check
from .mitigation import underwriting_currency_basis_risk
from .underwriting_simplified import (simplified_capital_at_risk, simplified_mortality_risk,
                                     simplified_disability_risk, simplified_life_catastrophe_risk)
from .reporting_catalog import reporting_catalog, reporting_data, reporting_table
from .reporting_bound_rule import reporting_bound_rule_check
from .reporting_preconditions import reporting_rule_precondition
from .reporting_closed_binding import reporting_closed_rule_check
from .reporting_validation_status import reporting_validation_status
from .reporting_metric import reporting_metric_value_check
from .reporting_instance import reporting_instance
from .sfcr_scope import sfcr_captive_disclosure_conditions_2027, sfcr_balance_sheet_audit_required_2027
from .sfcr_content import sfcr_content_evidence_check
from .sfcr_publication import sfcr_publication_evidence_check
from .rsr import rsr_long_term_equity_extra_disclosure_2027
from .capital_breach import capital_breach_requirements, capital_recovery_plan_evidence_check
from .interest_future import (interest_relative_factor_2027, interest_additive_shift_2027,
                              interest_down_floor_2027, interest_ufr_stress_2027, interest_down_stress_2027)
from .concentration import (concentration_asset_loss, concentration_excess, concentration_exposure_sum,
                            concentration_risk, concentration_single_name_quality)
from .concentration import concentration_factor, concentration_threshold
from .concentration import concentration_credit_quality
from .concentration import concentration_adjusted_exposure, concentration_assets
from .currency import currency_rate_stress, currency_risk, currency_scenario_charge, currency_participation_bof_change
from .currency import currency_peg_factor, currency_peg_rate_stress
from .zero_factors import (guaranteed_sts_securitisation_spread_stress,
                          insured_deposit_concentration_factor, public_exposure_zero_factor,
                          partial_public_guarantee_zero_amount_2027)
from .contracts import contract_boundary_exclusion, contract_recognition_due
from .contracts import obligation_derecognition_condition, contract_unilateral_right
from .prudent_deterministic import prudent_deterministic_eligibility_2027, prudent_deterministic_best_estimate_2027
from .prudent_deterministic import prudent_deterministic_non_snc_size_screen_2027
from .provisions import life_cashflow_grouping_conditions
from .usp import usp_credibility_factor, usp_nonproportional_credibility_blend, usp_excess_of_loss_estimate
from .usp import usp_excess_of_loss_group_weighting
from .usp_lognormal import usp_lognormal_sigma, usp_lognormal_credibility_blend
from .usp_fit import usp_lognormal_fit
from .captive_interest import captive_interest_duration, captive_interest_currency
from .mortgage_eligibility import mortgage_type2_eligibility_screen
from .external_models import external_model_checked_value, model_va_scr_floor_2027
from .partial_models import partial_model_bscr
from .governance import governance_evidence_check, governance_remuneration_deferral_years
from .group_reporting import group_significant_branch_screen
from .cat_simplified import catastrophe_group_weighted_sum, simplified_fire_risk
from .mitigation import simplified_single_segment_mitigation
from .reinsurance import reinsurance_recoverables_from_net
from .national_de import (de_branch_minimum_amount, de_liquidity_coverage,
                          de_cover_assets_minimum, de_cover_property_value)
from .group_availability import (group_model_scr_contribution, group_nonavailable_own_funds_cap, group_minority_excess_2027,
                                group_own_funds_transfer_timing_screen,
                                group_pre_acquisition_scr_exception_2027)
from .groups import group_reinsurance_elimination
from .usp_reserve2 import usp_reserve2_estimate, usp_reserve2_credibility_blend
from .usp_revision import usp_revision_moments, usp_revision_credibility_blend
from .usp_revision_quantile import usp_revision_compound_quantile
from .counterparty_ratio import counterparty_solvency_ratio
from .default_type import default_exposure_type
from .default_grouping import default_single_name_count
from .derivative_netting import default_derivative_netting_value
from .mass_lapse_special import life_mass_lapse_special_eligibility
from .lac_dt_profit import lac_dt_profit_assumptions_check
from .life_selection import health_biometric_selection, life_biometric_selection
from .macroregions import premium_reserve_geographic_region
from .protected_pd import default_protected_probability
from .clearing_conditions import default_clearing_conditions
from .premium_future import premium_future_component
from .assigned_credit_eligibility import assigned_credit_eligibility_screen
from .coinvestment_numeric import coinvestment_numeric_screen
from .unlisted_equity import unlisted_equity_beta, unlisted_equity_portfolio_screen
from .premium_netting import premium_net_of_reinsurance
from .health_module_scope import health_module_scope
from .natural_cat_diversification import natural_cat_other_diversification
from .premium_reserve_parameters import premium_reserve_parameterised_risk
from .assigned_credit_numeric import assigned_credit_issuer_financial_screen, assigned_credit_yield_screen
from .infrastructure_corporate import infrastructure_corporate_eligibility_screen
from .infrastructure_project import infrastructure_project_eligibility_screen
from .future_profit import own_funds_expected_future_premium_profit, own_funds_expected_future_fee_profit_2027
from .usp_governance import (usp_parameter_scope_check, usp_reinsurance_contract_conditions,
                             usp_standard_method_selection, usp_data_evidence_check,
                             usp_method_data_evidence_check)
from .default import default_probability, default_single_name_pd, default_type1, default_type2_shock
from .default import default_type2_shock_2027
from .default import default_ccp_fund_lgd_2027, default_defaulted_loan_lgd_2027
from .loss_given_default import default_securities_financing_lgd_2027
from .loss_given_default import default_risk_adjusted_collateral, default_risk_adjusted_mortgage
from .default_pools import default_pool_member_ratio, default_pool_solvency_ratio, default_pool_type_a_lgd
from .engine import Engine, calculate, coverage, export_resources, reference_cases, reference_portfolios
from .engine import rfr_monthly_data
from .geography import catastrophe_zone_ordinal
from .nonlife_lapse import health_nslt_lapse_factor, nonlife_lapse_factor
from .nonlife_cat_premium import nonprop_property_cat_loss, other_nonlife_cat_loss
from .motor_cat import motor_assumed_limit, motor_cat_loss, motor_vehicle_count
from .manmade_concentration import catastrophe_effective_sum, manmade_concentration_loss
from .liability_cat import liability_cat_claim_count, liability_cat_loss
from .credit_cat import credit_cat_default_loss, credit_cat_recession_loss
from .rfr import rfr_credit_risk_adjustment, rfr_currency_risk_adjustment, rfr_market_rate_adjustment
from .transitional import rfr_transitional_spot_rate, technical_provisions_transitional_value
from .capital import capital_add_on_amount
from .proportionality_scope import small_non_complex_annual_conditions_2027, non_snc_proportionality_size_screen_2027
from .rfr_future import rfr_risk_correction_2027
from .rfr_future import rfr_credit_spread_sensitivity
from .rfr_future import rfr_volatility_adjustment_2027
from .rfr_future import rfr_macro_country_factor
from .rfr_future import rfr_macro_volatility_adjustment
from .rfr_future import rfr_va_pvbp, rfr_pegged_credit_spread_sensitivity
from .own_funds import own_funds_financial_deduction_tier
from .own_funds import own_funds_financial_exemption_screen
from .own_funds_distributions import (own_funds_distribution_policy_ratio, own_funds_distribution_policy_amount,
                                      own_funds_foreseeable_distributions_2027)
from .rfr import rfr_fundamental_spread
from .rfr import rfr_downgrade_expected_loss
from .rfr_smith_wilson import rfr_smith_wilson_spot
from .rfr_ufr import rfr_ultimate_forward_rate
from .rfr_curve_2027 import rfr_curve_spot_2027
from .rfr_extrapolation import rfr_fsp_currency_percentage_2027
from .risk_mitigation import risk_mitigation_recognition_factor, reinsurance_counterparty_recognition_factor
from .proportionality_scope import small_non_complex_group_annual_conditions_2027
from .indexation import regulatory_euro_amount_indexation
from .contract_cashflows import best_estimate_contract_cashflows
from .rfr import rfr_matching_adjustment
from .rfr import rfr_equivalent_annual_rate
from .rfr import rfr_spot_discount_factor
from .rfr_monthly import rfr_archived_spot_rate
from .rfr_monthly import rfr_archived_government_spread
from .rfr_monthly import rfr_archived_corporate_pd, rfr_archived_corporate_spread
from .rfr_monthly import rfr_archived_ltas
from .capital import mcr_notional_scr, mcr_notional_requirement
from .rfr import rfr_matching_mortality_selected_be
from .rfr import rfr_matching_mortality_stress, rfr_default_loss_on_market_value, rfr_matching_mortality_headroom
from .rfr import rfr_reference_portfolio_spread, rfr_risk_corrected_spread, rfr_volatility_adjustment
from .rfr import rfr_portfolio_risk_correction
from .rfr import rfr_default_adjusted_cashflow, rfr_fundamental_spread_other_than_pd
from .rfr_extrapolation import (rfr_extrapolation_alpha_2027, rfr_extrapolated_forward_2027,
                                rfr_extrapolated_spot_2027, rfr_last_liquid_forward_2027)
from .groups import (group_consolidated_minimum, group_consolidated_surplus,
                     group_sector_capital_requirement_2027, group_sector_contribution_2027,
                     group_combined_component_surplus_2027, group_combined_currency_exposure_2027,
                     group_immaterial_participation_screen_2027, group_simplified_participation_scr_2027,
                     group_consolidated_best_estimate, group_consolidated_risk_margin, group_consolidated_scr,
                     group_method2_best_estimate_sum, group_method2_component_surplus,
                     group_required_shortfall, group_standard_scr_contribution)
from .scope import scope_volume_conditions, scope_ancillary_risk_conditions
from .scope import scope_volume_entry_trigger, scope_volume_release_history
from .valuation import valuation_participation_value, valuation_contingent_liability
from .valuation import valuation_short_term_deposit_cost_2027
from .valuation import valuation_balance_sheet_excess
from .valuation import valuation_accounts_method_conditions
from .valuation_methods import valuation_method_checked_value
from .reinsurance_reconciliation import reinsurance_adjusted_recoverable
from .symmetric_average import symmetric_adjustment_average
from .lookthrough_exposure import lookthrough_exposure_amount
from .lookthrough import lookthrough_fallback_conditions, lookthrough_grouping_limit
from .simplifications import simplification_share_screen_2027, simplified_immaterial_risk_2027
from .captive import captive_simplification_conditions, captive_nonlife_segment, captive_nonlife_aggregation
from .simplified_market import simplified_bond_spread_stress, simplified_bond_spread_risk
from .proportionality import simplification_proportionality_conditions, unrated_bond_simplification_conditions
from .mitigation import (simplified_reinsurance_mitigation, simplified_proportional_mitigation,
                         simplified_ead_mitigation_2027, simplified_default_group_pd, simplified_submodule_mitigation,
                         simplified_pool_member_best_estimate, simplified_pool_external_best_estimate,
                         simplified_pool_external_mitigation)
from .evidence import (orsa_core_evidence_check, orsa_climate_scenario_requirement_2027,
                       orsa_climate_scenario_structure_2027, orsa_phase_in_currency_exemption_2027,
                       orsa_biennial_captive_conditions_2027, orsa_max_assessment_interval_2027,
                       orsa_conditional_evidence_check, orsa_additional_macro_analysis_required_2027,
                       orsa_guidance_evidence_check, orsa_report_evidence_check,
                       group_orsa_method1_scr_difference, group_orsa_evidence_check,
                       risk_margin_reference_asset_balance, risk_margin_reference_evidence_check)
from .risk_margin_simplified import risk_margin_proportional_scr, risk_margin_percentage
from .risk_margin_simplified import risk_margin_duration, risk_margin_adjusted_duration_2027
from .risk_margin_simplified import risk_margin_reserve_scr
from .risk_margin_allocation import risk_margin_lob_allocation
from .evidence import risk_margin_internal_model_required
from .reporting_timing import supervisory_reporting_deadline_weeks, regular_supervisory_report_interval
from .reporting_evidence import supervisory_reporting_evidence_check, reporting_captive_itemised_exemption_2027
from .tp_validation_audit import technical_provision_validation_evidence_check
from .evidence import technical_provision_data_evidence_check, best_estimate_approximation_conditions
from .evidence import technical_provision_assumptions_evidence_check, technical_provision_projection_evidence_check
from .valuation import valuation_liability_excluding_own_credit, valuation_deferred_tax_net
from .valuation import (valuation_intangible_value, valuation_adjusted_equity_component,
                        valuation_accounting_equity_adjustment)
from .natural_cat import (natural_cat_event_loss, natural_cat_insured_sum, natural_cat_other_loss,
                          natural_cat_scenario_risk, natural_cat_weighted_cap)
from .health_accident import (health_accident_benefit_mean, health_accident_benefit_sum,
                              health_accident_concentration_loss, health_accident_country_aggregation,
                              health_mass_accident_loss)
from .health_pandemic import health_pandemic_income_exposure, health_pandemic_loss, health_pandemic_medical_cost
from .health_lapse import health_lapse_option_stress, health_lapse_risk, health_mass_lapse_factor
from .health_income import health_biometric_stress, health_income_incidence_stress, health_income_transition_stress
from .health_medical import health_expense_inflation_stress, health_expense_level_stress, health_revision_stress
from .health_medical import (health_disability_risk, health_medical_inflation_stress,
                             health_medical_payment_stress, health_medical_risk)
from .life_lapse import life_lapse_option_stress, life_lapse_risk, life_mass_lapse_factor
from .interest_selection import interest_scenario_charge, market_risk_from_interest_scenarios, interest_participation_bof_change
from .health import health_hres_mixed_sigma, health_hres_sigma_bound
from .health_adc import health_adc_recovery_2027, health_adc_reserve_factor_2027
from .nonlife_adc import nonlife_adc_recovery_2027, nonlife_adc_reserve_factor_2027
from .life import (life_biometric_stress, life_catastrophe_rate_stress, life_expense_inflation_stress, life_expense_level_stress,
                   life_revision_stress)
from .loss_given_default import (default_collateral_factor, default_derivative_lgd, default_mortgage_lgd,
                                 default_other_lgd, default_reinsurance_lgd, default_risk_mitigation,
                                 default_single_name_lgd, default_collateral_market_adjustment, default_pool_lgd)
from .market import (credit_derivative_scenario_charge, credit_spread_stress, equity_shock, interest_stress, lapse_stress,
                     property_value_stress, symmetric_adjustment)
from .spread import bond_spread_stress, secured_bond_spread_stress, securitisation_spread_stress, spread_risk
from .spread import specific_exposure_spread_stress
from .spread import insurer_solvency_spread_stress
from .spread import matching_fundamental_spread_increase
from .spread import financial_issuer_spread_stress
from .own_funds import own_funds_mcr_allocation, own_funds_scr_allocation
from .own_funds import own_funds_basic_before_adjustments, own_funds_reconciliation_reserve
from .own_funds import own_funds_restricted_deduction
from .own_funds import own_funds_financial_participation_deduction
from .engine import rule_profiles
from .provisions import best_estimate_cashflows, replicated_cashflow_value, technical_provisions_sum
from .reinsurance import (reinsurance_default_adjustment, reinsurance_default_loss,
                          reinsurance_nonlife_allocation, reinsurance_recoverable_cashflows, spv_recoverable_cap)
from .underwriting import (health_premium_reserve_risk, health_premium_volume, health_reserve_volume,
                           nonlife_premium_volume, nonlife_reserve_volume,
                           premium_reserve_diversification, premium_reserve_risk)

try:
    __version__ = version("solvency2")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = [
    "simplified_longevity_risk", "simplified_expense_risk",
    "simplified_capital_at_risk", "simplified_mortality_risk",
    "simplified_disability_risk", "simplified_life_catastrophe_risk",
    "simplified_lapse_risk",
    "own_funds_tier1_loss_absorption_trigger",
    "own_funds_tier1_mechanism_requirements",
    "restricted_portfolio_scenario_charge", "restricted_portfolio_scr_sum",
    "simplified_reinsurance_default_adjustment", "own_funds_step_up_limit", "underwriting_currency_basis_risk",
    "equity_stress_amount_2027",
    "reporting_catalog", "reporting_data", "reporting_table",
    "reporting_bound_rule_check",
    "reporting_rule_precondition", "reporting_closed_rule_check",
    "reporting_validation_status",
    "reporting_metric_value_check",
    "reporting_instance",
    "sfcr_captive_disclosure_conditions_2027", "sfcr_balance_sheet_audit_required_2027",
    "sfcr_content_evidence_check",
    "sfcr_publication_evidence_check",
    "rsr_long_term_equity_extra_disclosure_2027",
    "capital_breach_requirements", "capital_recovery_plan_evidence_check",
    "usp_credibility_factor", "usp_nonproportional_credibility_blend",
    "usp_excess_of_loss_estimate",
    "usp_excess_of_loss_group_weighting",
    "usp_lognormal_sigma", "usp_lognormal_credibility_blend",
    "usp_lognormal_fit",
    "captive_interest_duration", "captive_interest_currency",
    "mortgage_type2_eligibility_screen",
    "external_model_checked_value", "model_va_scr_floor_2027",
    "partial_model_bscr",
    "governance_evidence_check", "governance_remuneration_deferral_years",
    "group_significant_branch_screen",
    "significant_cross_border_activity_2027",
    "group_long_term_equity_limit_2027",
    "group_insurance_holding_conditions_2027",
    "public_counter_guarantee_conditions_2027",
    "proportionality_application_evidence_2027",
    "own_funds_classification_evidence_check",
    "catastrophe_group_weighted_sum",
    "simplified_fire_risk",
    "simplified_single_segment_mitigation",
    "reinsurance_recoverables_from_net",
    "de_branch_minimum_amount", "de_liquidity_coverage",
    "de_cover_assets_minimum", "de_cover_property_value",
    "group_model_scr_contribution", "group_nonavailable_own_funds_cap", "group_minority_excess_2027",
    "group_own_funds_transfer_timing_screen", "group_pre_acquisition_scr_exception_2027",
    "usp_reserve2_estimate", "usp_reserve2_credibility_blend",
    "usp_revision_moments", "usp_revision_credibility_blend",
    "usp_revision_compound_quantile",
    "counterparty_solvency_ratio",
    "default_exposure_type",
    "default_single_name_count", "default_derivative_netting_value",
    "life_mass_lapse_special_eligibility",
    "lac_dt_profit_assumptions_check",
    "life_biometric_selection",
    "health_biometric_selection",
    "premium_reserve_geographic_region",
    "default_protected_probability", "default_clearing_conditions",
    "premium_future_component",
    "assigned_credit_eligibility_screen",
    "lookthrough_exposure_amount",
    "symmetric_adjustment_average",
    "reinsurance_adjusted_recoverable",
    "coinvestment_numeric_screen",
    "unlisted_equity_beta",
    "unlisted_equity_portfolio_screen",
    "premium_net_of_reinsurance",
    "health_module_scope",
    "natural_cat_other_diversification",
    "premium_reserve_parameterised_risk",
    "assigned_credit_issuer_financial_screen",
    "assigned_credit_yield_screen",
    "infrastructure_corporate_eligibility_screen",
    "infrastructure_project_eligibility_screen",
    "own_funds_expected_future_premium_profit", "own_funds_expected_future_fee_profit_2027",
    "usp_parameter_scope_check", "usp_reinsurance_contract_conditions",
    "usp_standard_method_selection", "usp_data_evidence_check",
    "usp_method_data_evidence_check",
    "technical_provision_assumptions_evidence_check", "technical_provision_projection_evidence_check",
    "technical_provision_data_evidence_check", "best_estimate_approximation_conditions",
    "technical_provision_validation_evidence_check",
    "supervisory_reporting_deadline_weeks", "regular_supervisory_report_interval",
    "supervisory_reporting_evidence_check", "reporting_captive_itemised_exemption_2027",
    "life_cashflow_grouping_conditions",
    "simplification_share_screen_2027",
    "captive_simplification_conditions", "captive_nonlife_segment", "captive_nonlife_aggregation",
    "simplified_bond_spread_stress", "simplified_bond_spread_risk",
    "simplification_proportionality_conditions", "unrated_bond_simplification_conditions",
    "simplified_reinsurance_mitigation", "simplified_proportional_mitigation", "simplified_ead_mitigation_2027",
    "simplified_default_group_pd", "simplified_submodule_mitigation",
    "simplified_pool_member_best_estimate", "simplified_pool_external_best_estimate", "simplified_pool_external_mitigation",
    "orsa_core_evidence_check", "orsa_phase_in_currency_exemption_2027",
    "orsa_biennial_captive_conditions_2027", "orsa_max_assessment_interval_2027",
    "orsa_conditional_evidence_check", "orsa_additional_macro_analysis_required_2027",
    "orsa_guidance_evidence_check",
    "orsa_report_evidence_check",
    "group_orsa_method1_scr_difference", "group_orsa_evidence_check",
    "risk_margin_reference_asset_balance", "risk_margin_reference_evidence_check",
    "risk_margin_proportional_scr", "risk_margin_percentage",
    "risk_margin_duration", "risk_margin_adjusted_duration_2027",
    "risk_margin_reserve_scr",
    "risk_margin_lob_allocation",
    "risk_margin_internal_model_required",
        "orsa_climate_scenario_requirement_2027", "orsa_climate_scenario_structure_2027",
    "simplified_immaterial_risk_2027",
    "lookthrough_fallback_conditions", "lookthrough_grouping_limit",
    "valuation_accounts_method_conditions",
    "valuation_method_checked_value",
    "valuation_balance_sheet_excess",
    "valuation_liability_excluding_own_credit",
    "valuation_deferred_tax_net",
    "valuation_short_term_deposit_cost_2027",
    "valuation_participation_value",
    "valuation_contingent_liability",
    "valuation_intangible_value",
    "valuation_adjusted_equity_component",
    "valuation_accounting_equity_adjustment",
    "nonlife_adc_recovery_2027", "nonlife_adc_reserve_factor_2027",
    "health_adc_recovery_2027", "health_adc_reserve_factor_2027",
    "default_ccp_fund_lgd_2027", "default_defaulted_loan_lgd_2027",
    "default_type2_shock_2027",
    "interest_down_stress_2027",
    "interest_relative_factor_2027", "interest_additive_shift_2027", "interest_down_floor_2027", "interest_ufr_stress_2027",
    "CalculationError", "Context", "NumericOverride", "Result", "Engine", "aggregate_risk", "basic_scr",
    "contract_boundary_exclusion", "contract_recognition_due",
    "obligation_derecognition_condition", "contract_unilateral_right",
    "prudent_deterministic_eligibility_2027", "prudent_deterministic_best_estimate_2027",
    "prudent_deterministic_non_snc_size_screen_2027",
    "life_biometric_stress", "life_catastrophe_rate_stress", "life_expense_level_stress", "life_expense_inflation_stress", "life_revision_stress",
    "default_probability", "default_single_name_pd",
    "default_collateral_factor", "default_derivative_lgd", "default_mortgage_lgd",
    "default_reinsurance_lgd", "default_risk_mitigation",
    "default_other_lgd", "default_single_name_lgd",
    "default_collateral_market_adjustment",
    "default_pool_lgd",
    "default_pool_member_ratio", "default_pool_solvency_ratio", "default_pool_type_a_lgd",
    "interest_scenario_charge", "market_risk_from_interest_scenarios", "interest_participation_bof_change",
    "bond_spread_stress",
    "secured_bond_spread_stress",
    "securitisation_spread_stress",
    "specific_exposure_spread_stress",
    "insurer_solvency_spread_stress",
    "matching_fundamental_spread_increase",
    "financial_issuer_spread_stress",
    "concentration_asset_loss", "concentration_excess", "concentration_exposure_sum",
    "concentration_risk", "concentration_single_name_quality",
    "concentration_factor", "concentration_threshold",
    "concentration_credit_quality",
    "concentration_adjusted_exposure", "concentration_assets",
    "currency_rate_stress", "currency_risk", "currency_scenario_charge", "currency_participation_bof_change",
    "currency_peg_factor", "currency_peg_rate_stress",
    "guaranteed_sts_securitisation_spread_stress", "insured_deposit_concentration_factor", "public_exposure_zero_factor",
    "partial_public_guarantee_zero_amount_2027",
    "default_securities_financing_lgd_2027",
    "default_risk_adjusted_collateral", "default_risk_adjusted_mortgage",
    "credit_derivative_scenario_charge", "credit_spread_stress", "property_value_stress", "spread_risk",
    "catastrophe_zone_aggregation", "catastrophe_region_aggregation", "catastrophe_weighted_sum",
    "catastrophe_zone_ordinal",
    "scenario_loss",
    "select_scenario", "intangible_risk", "lac_tp", "mcr_absolute_floor", "mcr_combined", "mcr_life", "mcr_nonlife", "mcr_capital_at_risk",
    "operational_risk", "risk_margin", "mcr_linear", "default_type1", "default_type2_shock", "equity_shock",
    "own_funds_scr_allocation", "own_funds_mcr_allocation",
    "own_funds_basic_before_adjustments", "own_funds_reconciliation_reserve",
    "own_funds_restricted_deduction",
    "own_funds_financial_participation_deduction",
    "rule_profiles",
    "interest_stress", "lapse_stress", "symmetric_adjustment", "premium_reserve_risk",
    "nonlife_premium_volume", "nonlife_reserve_volume",
    "premium_reserve_diversification",
    "health_premium_volume", "health_reserve_volume", "health_premium_reserve_risk",
    "health_hres_sigma_bound", "health_hres_mixed_sigma",
    "lac_dt_stress_amount", "lac_dt", "scr_standard_formula",
    "best_estimate_cashflows", "technical_provisions_sum",
    "replicated_cashflow_value",
    "reinsurance_default_loss", "spv_recoverable_cap",
    "reinsurance_recoverable_cashflows", "reinsurance_default_adjustment",
    "reinsurance_nonlife_allocation",
    "parameter", "calculate", "coverage", "reference_cases", "reference_portfolios", "export_resources",
    "rfr_monthly_data",
    "life_lapse_option_stress", "life_lapse_risk", "life_mass_lapse_factor",
    "health_income_incidence_stress", "health_income_transition_stress",
    "health_biometric_stress",
    "health_nslt_lapse_factor", "nonlife_lapse_factor",
    "nonprop_property_cat_loss", "other_nonlife_cat_loss",
    "motor_assumed_limit", "motor_cat_loss", "motor_vehicle_count",
    "catastrophe_effective_sum", "manmade_concentration_loss",
    "liability_cat_claim_count", "liability_cat_loss",
    "credit_cat_default_loss", "credit_cat_recession_loss",
    "rfr_credit_risk_adjustment",
    "rfr_currency_risk_adjustment", "rfr_market_rate_adjustment",
    "rfr_transitional_spot_rate", "technical_provisions_transitional_value",
    "capital_add_on_amount",
    "small_non_complex_annual_conditions_2027", "non_snc_proportionality_size_screen_2027",
    "rfr_risk_correction_2027",
    "rfr_credit_spread_sensitivity",
    "rfr_volatility_adjustment_2027",
    "rfr_macro_country_factor",
    "rfr_macro_volatility_adjustment",
    "rfr_va_pvbp", "rfr_pegged_credit_spread_sensitivity",
    "own_funds_financial_deduction_tier",
    "own_funds_financial_exemption_screen",
    "own_funds_distribution_policy_ratio", "own_funds_distribution_policy_amount",
    "own_funds_foreseeable_distributions_2027",
    "rfr_fundamental_spread",
    "rfr_downgrade_expected_loss",
    "rfr_smith_wilson_spot",
    "rfr_ultimate_forward_rate",
    "rfr_curve_spot_2027",
    "rfr_fsp_currency_percentage_2027", "risk_mitigation_recognition_factor",
    "reinsurance_counterparty_recognition_factor",
    "small_non_complex_group_annual_conditions_2027", "regulatory_euro_amount_indexation",
    "best_estimate_contract_cashflows",
    "rfr_matching_adjustment",
    "rfr_equivalent_annual_rate",
    "rfr_spot_discount_factor",
    "rfr_archived_spot_rate",
    "rfr_archived_government_spread",
    "rfr_archived_corporate_pd", "rfr_archived_corporate_spread",
    "rfr_archived_ltas",
    "mcr_notional_scr", "mcr_notional_requirement",
    "rfr_matching_mortality_selected_be",
    "rfr_matching_mortality_stress", "rfr_default_loss_on_market_value", "rfr_matching_mortality_headroom",
    "rfr_reference_portfolio_spread", "rfr_risk_corrected_spread", "rfr_volatility_adjustment",
    "rfr_portfolio_risk_correction",
    "rfr_default_adjusted_cashflow", "rfr_fundamental_spread_other_than_pd",
    "rfr_extrapolation_alpha_2027", "rfr_extrapolated_forward_2027", "rfr_extrapolated_spot_2027",
    "rfr_last_liquid_forward_2027",
    "group_sector_capital_requirement_2027", "group_sector_contribution_2027",
    "group_combined_component_surplus_2027", "group_combined_currency_exposure_2027",
    "scope_volume_conditions",
    "scope_ancillary_risk_conditions",
    "scope_volume_entry_trigger", "scope_volume_release_history",
    "group_consolidated_minimum", "group_consolidated_surplus",
    "group_immaterial_participation_screen_2027", "group_simplified_participation_scr_2027",
    "group_method2_component_surplus", "group_required_shortfall",
    "group_method2_best_estimate_sum", "group_standard_scr_contribution",
    "group_consolidated_best_estimate", "group_consolidated_risk_margin", "group_consolidated_scr", "group_reinsurance_elimination",
    "natural_cat_event_loss", "natural_cat_insured_sum", "natural_cat_other_loss",
    "natural_cat_scenario_risk", "natural_cat_weighted_cap",
    "health_accident_benefit_mean", "health_accident_benefit_sum", "health_accident_concentration_loss",
    "health_accident_country_aggregation", "health_mass_accident_loss",
    "health_pandemic_income_exposure", "health_pandemic_loss", "health_pandemic_medical_cost",
    "health_lapse_option_stress", "health_lapse_risk", "health_mass_lapse_factor",
    "health_expense_inflation_stress", "health_expense_level_stress", "health_revision_stress",
    "health_disability_risk", "health_medical_inflation_stress", "health_medical_payment_stress", "health_medical_risk",
]
