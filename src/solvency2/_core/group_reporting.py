"""Group reporting supplements and significant-branch arithmetic, not filings."""
from fractions import Fraction

from .core import Context, calculation, number, require, scalar
from .evidence import _evidence_inventory, _reference


def group_reporting_check(profile, kind, scope, evidence, assessment_reference):
    require(isinstance(scope, str) and scope in ("solo", "group", "single_group"),
            "reporting_scope", "solo, group or single_group required")
    if scope == "solo":
        require(evidence is None, "group_evidence", "group evidence unused in solo scope")
        return True, {"status": "NOT_APPLICABLE_SOLO"}, []
    future = profile["profile_id"] == "EU-S2-DOCUMENTS-2027-v0.1"
    require(kind in ("sfcr", "rsr"), "report_kind", "group supplements require full SFCR/RSR scope", "UNSUPPORTED_PARAMETER")
    require(not (kind == "rsr" and scope == "single_group" and not future), "reporting_scope",
            "single RSR regime is only established in future profile", "UNSUPPORTED_RULESET")
    require(evidence is not None, "group_evidence", "explicit group supplementary references required", "MISSING_INPUT")
    rows = [r[:3] for r in profile["tables"]["group_reporting_controls"]["rows"]
            if r[3] == kind and r[4] in ("both", scope)]
    value, details = _evidence_inventory(evidence, {"rows": rows}, assessment_reference)
    sources = details.pop("_sources", [])
    interval = number(profile["scalars"]["group_structure_publication_years"]["value"],
                      "group_structure_publication_years", 0) if kind == "sfcr" else None
    require(interval is None or interval > 0, "group_structure_publication_years", "positive interval required")
    return bool(value), {**details, "status": "DECLARED_GROUP_SUPPLEMENT_INVENTORY",
        "group_structure_publication_years": interval, "calendar_deadlines_monitored": False,
        "reporting_scope": scope, "subsidiary_report_contents_verified": False,
        "supervisory_consent_verified": False, "actual_language_or_publication_verified": False,
        "source_wording_cautions": (["DR372(2)(c)(iv) prints iii/vii exception references",
                                     "DR374(1) names SFCR in the supervisory-reporting chapter"] if future and kind == "rsr" else [])}, sources


@calculation("DR:article-354:1", "DR:article-359:a:i", "DR:article-372:2:a", unit="indicator")
def group_significant_branch_screen(branch_gross_premiums: float, group_gross_premiums: float,
                                    host_market_gross_premiums: float, *,
                                    qualification_reference: str, context: Context):
    """Strict 5% group OR host-market test used by group reporting definitions.

    Latest applicable accounts, currency, host-market life/nonlife scope and
    branch perimeter are externally qualified. No college invitation or broad
    materiality judgement follows automatically from this numeric indicator.
    """
    _reference(qualification_reference, "qualification_reference")
    branch = number(branch_gross_premiums, "branch_gross_premiums", 0)
    group = number(group_gross_premiums, "group_gross_premiums", 0)
    market = number(host_market_gross_premiums, "host_market_gross_premiums", 0)
    require(group > 0 and market > 0, "premium_denominators", "zero denominator requires scope review", "REVIEW_REQUIRED")
    limit = number(scalar("group_significant_branch_share_limit", context), "significance_limit", 0, 1)
    group_test = Fraction(str(branch)) > Fraction(str(limit)) * Fraction(str(group))
    market_test = Fraction(str(branch)) > Fraction(str(limit)) * Fraction(str(market))
    return int(group_test or market_test), {"group_threshold_exceeded": group_test,
        "host_market_threshold_exceeded": market_test, "strict_share_limit": limit,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "college_participation_determined": False, "scope": "article354_numeric_significant_branch_test_only"}
