"""Standard Article188 currency scenarios; peg adjustments and BOF valuations separate."""
import math
from collections.abc import Mapping

from .aggregation import _select_scenario
from .core import Context, calculation, effective_resource, exact_keys, number, require, scalar


@calculation("DR:article-188:6")
def currency_participation_bof_change(participations: Mapping, *, qualification_reference: str, context: Context):
    """Signed FX BOF change: deducted holdings contribute gains but not losses.

    Inputs are externally valued BOF deltas for each holding's Art68-deducted
    and non-deducted parts, not market values or deduction amounts. Apply the
    positive-part rule per holding before summation; do not net excluded losses.
    """
    value, details = _participation_bof_change(participations, qualification_reference)
    return value, {**details,
        "scope": "signed_participation_bof_delta_only_not_own_funds_deduction_or_currency_scr"}


def _participation_bof_change(participations, qualification_reference):
    """Shared positive-part rule; callers retain the appropriate risk source."""
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external participation/deduction/scenario qualification required", "MISSING_INPUT")
    require(isinstance(participations, Mapping), "participations", "explicit participation mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in participations),
            "participations", "nonempty string participation IDs required")
    amounts, excluded = {}, {}
    for identifier, row in participations.items():
        exact_keys(row, ["nondeducted_bof_change", "deducted_bof_change"], identifier)
        nondeducted = number(row["nondeducted_bof_change"], identifier + ".nondeducted_bof_change")
        deducted = number(row["deducted_bof_change"], identifier + ".deducted_bof_change")
        amounts[identifier] = number(math.fsum((nondeducted, max(deducted, 0))), identifier + ".included_change")
        excluded[identifier] = min(deducted, 0)
    return math.fsum(amounts.values()), {
        "included_bof_changes": amounts, "excluded_deducted_losses": excluded,
        "empty_population": not bool(participations), "qualification_reference": qualification_reference,
        "qualification_status": "EXTERNAL_UNVERIFIED"}


@calculation("DR:article-188:2:7", "DR:article-206:2")
def currency_scenario_charge(gross_losses: Mapping, net_losses: Mapping, *,
                             valuation_reference: str, tie_break: str | None = None, context: Context):
    """One currency: select gross charge by the largest externally valued net-FDB loss.

    Each mapping contains exactly up/down in the context's local currency.
    This does not value exposures or approve their currency classification.
    """
    require(isinstance(valuation_reference, str) and bool(valuation_reference.strip()),
            "valuation_reference", "external gross/net-FDB scenario valuation required", "MISSING_INPUT")
    exact_keys(gross_losses, ["up", "down"], "gross_losses")
    exact_keys(net_losses, ["up", "down"], "net_losses")
    charge, details = _select_scenario(gross_losses, net_losses, tie_break)
    return charge, {**details, "valuation_reference": valuation_reference,
                    "valuation_status": "EXTERNAL_UNVERIFIED",
                    "scope": "single_currency_selected_gross_charge_not_valuation_or_total_currency_risk"}


@calculation("DR:article-188:5", "ITS2015_2017:article-1-2", unit="ratio")
def currency_peg_factor(foreign_currency: str, *, qualification_reference: str, context: Context):
    """Historical document-profile pair factor, not confirmation of a current currency peg.

    All 15 unordered pairs are explicit original values, not cross-rate-derived
    estimates. External evidence must establish date-specific applicability.
    """
    require(isinstance(foreign_currency, str) and len(foreign_currency) == 3 and foreign_currency.isascii()
            and foreign_currency.isalpha() and foreign_currency.isupper(), "foreign_currency", "three uppercase ASCII currency letters required")
    require(foreign_currency != context.currency, "foreign_currency", "distinct local and foreign currencies required")
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external date-specific peg/Article188(5) qualification required", "MISSING_INPUT")
    table = effective_resource("profile.json", context)["tables"]["currency_peg_factors"]
    pair = {context.currency, foreign_currency}
    rows = [row for row in table["rows"] if set(row[:2]) == pair]
    require(len(rows) == 1, "currency_pair", "no unique supported original pair; no standard-factor fallback", "UNSUPPORTED_PARAMETER")
    factor = number(rows[0][2], "currency_peg_factor", 0, 1)
    return factor, {"local_currency": context.currency, "foreign_currency": foreign_currency,
        "original_pair": rows[0][:2], "source_version": table["version"],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "document_pair_factor_only_not_current_peg_or_currency_status_confirmation",
        "_sources": [table["source"]]}


@calculation("DR:article-188:3-5", "ITS2015_2017:article-1-2", unit="exchange_rate")
def currency_peg_rate_stress(exchange_rate: float, foreign_currency: str, *, direction: str,
                              qualification_reference: str, valuation_reference: str, context: Context):
    """Apply a qualified original peg factor to local currency per one foreign unit."""
    require(direction in ("up", "down"), "direction", "explicit up/down direction required", "UNSUPPORTED_METHOD")
    require(isinstance(valuation_reference, str) and bool(valuation_reference.strip()),
            "valuation_reference", "external quote/basis/valuation reference required", "MISSING_INPUT")
    rate = number(exchange_rate, "exchange_rate", 0)
    require(rate > 0, "exchange_rate", "positive local-per-foreign quote required")
    factor = currency_peg_factor(foreign_currency, qualification_reference=qualification_reference, context=context)
    value = rate * (1 + factor.value if direction == "up" else 1 - factor.value)
    return value, {"exchange_rate": rate, "direction": direction, "shock": factor.value,
        "quote_convention": "local_currency_per_one_foreign_unit", "valuation_reference": valuation_reference,
        "valuation_status": "EXTERNAL_UNVERIFIED", "factor_details": factor.details,
        "scope": "qualified_original_peg_rate_only_not_BOF_valuation", "_sources": list(factor.sources)}


@calculation("DR:article-188:3-4", unit="exchange_rate")
def currency_rate_stress(exchange_rate: float, *, direction: str, valuation_reference: str, context: Context):
    """Stress local currency per one foreign unit, not its reciprocal or a BOF amount."""
    require(direction in ("up", "down"), "direction", "explicit up/down direction required", "UNSUPPORTED_METHOD")
    require(isinstance(valuation_reference, str) and bool(valuation_reference.strip()),
            "valuation_reference", "external quote/basis/valuation reference required", "MISSING_INPUT")
    rate = number(exchange_rate, "exchange_rate", 0)
    require(rate > 0, "exchange_rate", "positive local-per-foreign quote required")
    shock = number(scalar("currency_standard", context), "currency_standard", 0, 1)
    value = rate * (1 + shock if direction == "up" else 1 - shock)
    return value, {"exchange_rate": rate, "direction": direction, "shock": shock,
        "quote_convention": "local_currency_per_one_foreign_unit", "valuation_reference": valuation_reference,
        "valuation_status": "EXTERNAL_UNVERIFIED", "scope": "standard_currency_rate_only_no_peg_relief_or_BOF_valuation"}


@calculation("DR:article-188:1-2", "DR:article-188:7")
def currency_risk(currency_charges: Mapping[str, float], *, classification_reference: str, context: Context):
    """Sum already net-scenario-selected gross charges, all valued in Context.currency."""
    require(isinstance(classification_reference, str) and bool(classification_reference.strip()),
            "classification_reference", "external complete currency allocation reference required", "MISSING_INPUT")
    require(isinstance(currency_charges, Mapping) and bool(currency_charges),
            "currency_charges", "nonempty labelled foreign-currency charges required", "MISSING_INPUT")
    charges = {}
    for currency, value in currency_charges.items():
        require(isinstance(currency, str) and len(currency) == 3 and currency.isascii()
                and currency.isalpha() and currency.isupper(), "currency", "three uppercase ASCII currency letters required")
        require(currency != context.currency, "currency", "local accounting currency is not a foreign currency")
        charges[currency] = number(value, f"currency_charges.{currency}", 0)
    return math.fsum(charges.values()), {"currency_charges": charges, "local_currency": context.currency,
        "classification_reference": classification_reference, "classification_status": "EXTERNAL_UNVERIFIED",
        "scope": "sum_of_preselected_gross_BOF_charges_no_currency_conversion"}
