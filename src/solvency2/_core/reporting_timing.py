"""Versioned solo/group reporting periods; no calendar, filing or format approval."""
from .core import Context, calculation, effective_resource, number, require, scalar
from .evidence import _declared_bool, _reference


def _rows(context, scope="solo"):
    require(isinstance(scope, str) and scope in {"solo", "group"}, "scope", "explicit solo/group scope required")
    table = "group_reporting_periods" if scope == "group" else "supervisory_reporting_periods"
    return {r[0]: r[1:] for r in effective_resource("profile.json", context)["tables"][table]["rows"]}


def _positive(row, expected_unit):
    value, unit, source, origin = row
    require(unit == expected_unit, "reporting_period", "inconsistent parameter unit", "REVIEW_REQUIRED")
    value = number(value, "reporting_period", 0)
    require(value > 0, "reporting_period", "positive reporting period required", "REVIEW_REQUIRED")
    return value, source, origin


@calculation(unit="weeks")
def supervisory_reporting_deadline_weeks(report_kind: str, *, qualification_reference: str,
                                         scope: str = "solo", context: Context,
                                         exceptional_extension_weeks: float = 0,
                                         delegated_act_reference: str | None = None):
    """Select an archived deadline length for an externally qualified type/scope.

    Historical rows are post-transition. Future ORSA has no inherited two-week
    row. The returned length is not a legally determined calendar date.
    Explicit group scope uses separate254/256/256b or historical373 rules.
    Group sfcr/single_sfcr entries include public disclosure, not just filing.
    Optional304e extension requires an externally qualified delegated act;
    an extreme event alone never creates an extension. ORSA/SPV are excluded.
    """
    _reference(qualification_reference, "qualification_reference")
    require(isinstance(report_kind, str) and bool(report_kind.strip()), "report_kind", "nonempty report kind required")
    row = _rows(context, scope).get("deadline_" + report_kind)
    if scope == "solo" and report_kind == "sfcr":
        periods = effective_resource("profile.json", context)["tables"]["sfcr_periods"]["rows"]
        publication = next(r for r in periods if r[0] == "publication_deadline")
        row = [*publication[1:], "financial_year_end"]
    require(row is not None, "report_kind", "deadline not established for this report kind/profile", "UNSUPPORTED_PARAMETER")
    value, source, origin = _positive(row, "weeks")
    extension = number(exceptional_extension_weeks, "exceptional_extension_weeks", 0)
    extension_sources = []
    if extension:
        require(context.profile_id == "EU-S2-DOCUMENTS-2027-v0.1", "exceptional_extension_weeks",
                "Article304e extension unavailable in historical profile", "UNSUPPORTED_RULESET")
        require(report_kind in {"regular_supervisory_report", "annual_quantitative", "quarterly_quantitative", "sfcr", "single_sfcr"},
                "report_kind", "Article304e does not extend this deadline", "UNSUPPORTED_METHOD")
        _reference(delegated_act_reference, "delegated_act_reference")
        maximum = number(scalar("reporting_exceptional_max_extension_weeks", context), "maximum_extension", 0)
        require(extension <= maximum, "exceptional_extension_weeks", "extension exceeds Article304e limit", "UNSUPPORTED_METHOD")
        extension_sources = ["DIR:article-304e:2"]
    else:
        require(delegated_act_reference is None, "delegated_act_reference", "unused reference without extension")
    return value + extension, {"report_kind": report_kind, "period_origin": origin,
        "ordinary_deadline_weeks": value, "exceptional_extension_weeks": extension,
        "delegated_act_reference": delegated_act_reference, "delegated_act_applicability_verified": False,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "calendar_deadline_calculated": False, "actual_submission_verified": False,
        "groups_or_public_disclosure_included": scope == "group" or report_kind in {"sfcr", "single_sfcr"},
        "reporting_scope": scope, "public_disclosure": report_kind in {"sfcr", "single_sfcr"},
        "scope": "archived_reporting_deadline_length_only", "_sources": [source] + extension_sources}


@calculation(unit="years")
def regular_supervisory_report_interval(small_non_complex: bool, *,
                                         supervisory_interval_years: float | None = None,
                                         supervisory_reference: str | None = None,
                                         non_snc_approval_reference: str | None = None,
                                         scope: str = "solo",
                                         qualification_reference: str, context: Context):
    """Select declared RSR periodicity without waiving other reporting duties.

    None explicitly declares no additional supervisory decision. Classification
    and authenticity of instructions/approval remain external qualifications.
    non_snc_approval_reference enables the separately approved29d/327b route;
    a size-screen result is never substituted for this supervisory decision.
    """
    _reference(qualification_reference, "qualification_reference")
    snc = _declared_bool(small_non_complex, "small_non_complex")
    rows = _rows(context, scope)
    default, source, _ = _positive(rows["rsr_default_maximum_years"], "years")
    future = "rsr_snc_approved_maximum_years" in rows
    approved_non_snc = non_snc_approval_reference is not None
    if approved_non_snc:
        _reference(non_snc_approval_reference, "non_snc_approval_reference")
        require(future and not snc, "non_snc_approval_reference", "prior Article29d/327b non-SNC approval requires2027 non-SNC route",
                "UNSUPPORTED_METHOD")
        require(supervisory_interval_years is not None, "supervisory_interval_years", "specific approved interval required", "MISSING_INPUT")
    require(future or not snc, "small_non_complex", "new SNC reporting regime not available in historical profile", "UNSUPPORTED_METHOD")
    maximum = default
    if future and (snc or approved_non_snc):
        maximum, _, _ = _positive(rows["rsr_snc_approved_maximum_years"], "years")
        require(maximum >= default, "rsr_snc_approved_maximum_years", "approved maximum below default", "REVIEW_REQUIRED")
    selected = default
    sources = [source] + ((["DIR:article-213a:5", "DIR:article-29d"] if scope == "group" else
                          ["DIR:article-29d", "DR:article-327b"]) if approved_non_snc else [])
    if supervisory_interval_years is None:
        require(supervisory_reference is None, "supervisory_reference", "unused reference without declared supervisory interval")
    else:
        _reference(supervisory_reference, "supervisory_reference")
        selected = number(supervisory_interval_years, "supervisory_interval_years", 0)
        require(selected > 0, "supervisory_interval_years", "strictly positive interval required")
        require(selected <= maximum, "supervisory_interval_years", "interval exceeds implemented regulatory scope", "UNSUPPORTED_METHOD")
        if future and snc:
            require(selected >= default, "supervisory_interval_years",
                    "shorter SNC intervals are not established by the implemented Article35(5a)(a) extension", "UNSUPPORTED_METHOD")
        if not future:
            annual, annual_source, _ = _positive(rows["rsr_supervisor_annual_years"], "years")
            require(annual <= default, "rsr_supervisor_annual_years", "annual request exceeds default", "REVIEW_REQUIRED")
            require(selected in (annual, default), "supervisory_interval_years",
                    "only default or annual request established for historical profile", "UNSUPPORTED_METHOD")
            sources.append(annual_source)
    return selected, {"small_non_complex": snc, "default_interval_years": default,
        "reporting_scope": scope,
        "non_snc_approval_reference": non_snc_approval_reference,
        "maximum_with_required_approval_years": maximum,
        "supervisory_interval_years": supervisory_interval_years, "supervisory_reference": supervisory_reference,
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "classification_or_approval_verified": False, "other_reporting_duties_waived": False,
        "actual_due_date_calculated": False, "scope": "declared_RSR_interval_only",
        "_sources": sources}
