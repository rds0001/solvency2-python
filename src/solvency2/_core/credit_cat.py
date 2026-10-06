"""Article134 credit catastrophe: net exposure selection, explicit gross claims."""
import math
from typing import Mapping, Sequence

from .core import Context, calculation, exact_keys, number, require, scalar


def _reference(reference):
    require(isinstance(reference, str) and bool(reference.strip()), "qualification_reference",
            "external LOB9/21 and event-recovery qualification required", "MISSING_INPUT")


@calculation("DR:article-134:2-3")
def credit_cat_default_loss(exposures: Mapping, *, qualification_reference: str,
                            selected_exposure_ids: Sequence[str] | None = None, context: Context):
    """Select largest NET default exposures and report their gross scenario claims.

    Each recovery is externally valued against this exposure's default claim,
    not against its full insured sum. Ambiguous cutoff ties with differing gross
    amounts require explicit selection, still constrained to largest net losses.
    """
    _reference(qualification_reference)
    require(isinstance(exposures, Mapping), "exposures", "explicit mapping required", "MISSING_INPUT")
    require(all(isinstance(key, str) and key.strip() for key in exposures), "exposures", "nonempty string IDs required")
    fraction = number(scalar("credit_cat_default_fraction", context), "default_fraction", 0, 1)
    count = number(scalar("credit_cat_exposure_count", context), "exposure_count", 0)
    require(count.is_integer() and count > 0, "exposure_count", "positive whole selection count required")
    rows = {}
    for label, row in exposures.items():
        exact_keys(row, ["insured_sum", "recoverable"], label)
        insured = number(row["insured_sum"], label + ".insured_sum", 0)
        gross = number(insured * fraction, label + ".gross_loss", 0)
        recovery = number(row["recoverable"], label + ".recoverable", 0)
        require(recovery <= gross, label + ".recoverable", "recovery exceeds gross default loss", "REVIEW_REQUIRED")
        rows[label] = {"insured_sum": insured, "gross_loss": gross, "recoverable": recovery,
                       "net_loss": gross - recovery}
    ranked = sorted(rows, key=lambda key: (-rows[key]["net_loss"], key))
    n = min(int(count), len(ranked))
    boundary_ties = []
    if 0 < n < len(ranked):
        cutoff = rows[ranked[n - 1]]["net_loss"]
        boundary_ties = [key for key in ranked if rows[key]["net_loss"] == cutoff]
    if selected_exposure_ids is not None:
        require(isinstance(selected_exposure_ids, (list, tuple))
                and all(isinstance(key, str) for key in selected_exposure_ids),
                "selected_exposure_ids", "explicit ID list required")
        selected = list(selected_exposure_ids)
        require(len(selected) == n and len(set(selected)) == n and all(key in rows for key in selected),
                "selected_exposure_ids", "unique existing IDs matching selection count required")
        unselected = [key for key in ranked if key not in selected]
        if selected and unselected:
            require(min(rows[key]["net_loss"] for key in selected) >= max(rows[key]["net_loss"] for key in unselected),
                    "selected_exposure_ids", "selection must preserve largest NET default losses")
    else:
        crosses_cutoff = n > 0 and n < len(ranked) and rows[ranked[n - 1]]["net_loss"] == rows[ranked[n]]["net_loss"]
        require(not crosses_cutoff or len({rows[key]["gross_loss"] for key in boundary_ties}) <= 1,
                "selected_exposure_ids", "cutoff tie with different gross losses requires explicit choice", "REVIEW_REQUIRED")
        selected = ranked[:n]
    return math.fsum(rows[key]["gross_loss"] for key in selected), {
        "exposures": rows, "selected_ids": sorted(selected), "boundary_tie_ids": boundary_ties,
        "selected_net_loss": math.fsum(rows[key]["net_loss"] for key in selected),
        "explicit_selection": selected_exposure_ids is not None, "default_fraction": fraction,
        "required_exposure_count": int(count), "available_exposure_count": len(rows),
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "selected_gross_default_claims_not_bof_or_scr"}


@calculation("DR:article-134:4")
def credit_cat_recession_loss(gross_premium: float, *, qualification_reference: str, context: Context):
    """Sudden gross claim from next12month earned LOB9/21 premiums, not capital."""
    _reference(qualification_reference)
    premium = number(gross_premium, "gross_premium", 0)
    fraction = number(scalar("credit_cat_recession_fraction", context), "recession_fraction", 0)
    return premium * fraction, {"gross_premium": premium, "recession_fraction": fraction,
                                "qualification_reference": qualification_reference,
                                "qualification_status": "EXTERNAL_UNVERIFIED",
                                "scope": "gross_scenario_claim_before_reinsurance_not_bof_or_scr"}
