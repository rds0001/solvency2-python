"""Exact local market-table retrieval; bundled inputs are synthetic demos only.

The optional ``market_data`` keyword takes a user-owned JSON-compatible archive
with the same structure as ``rfr_monthly_data()``. No downloads or date rolling.
See docs/DATA.md for the schema, units and provenance contract.
"""
from datetime import date
from functools import wraps
import warnings

from .core import CalculationError, Context, calculation, effective_resource, fingerprint, load_resource, number, require
from .rfr import _reference


def _market_input_errors(function):
    """Report malformed user tables at the API boundary, without implicit defaults."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except CalculationError:
            raise  # Preserve existing machine-readable guard codes and fields.
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise CalculationError("INVALID_INPUT", "market_data", "invalid table schema: " + str(error)) from None
    return wrapped


def _market_details(dataset):
    return {"market_data_kind": dataset["data_kind"],
            "market_dataset_hash": fingerprint(dataset),
            "market_data_notice": "Invented demonstration inputs; not production market data."
            if dataset["data_kind"] == "SYNTHETIC_DEMO" else "User-supplied local inputs.",
            "source_metadata_supplied_by": "RiskDataScience GmbH" if dataset["data_kind"] == "SYNTHETIC_DEMO" else "user"}


def _corporate_cell(series_id, sector, maturity_years, credit_quality_step, metric, qualification_reference, context, market_data):
    _reference(qualification_reference)
    require(isinstance(series_id, str) and bool(series_id), "series_id", "explicit published series required")
    require(isinstance(sector, str) and sector in {"financial", "non_financial"}, "sector", "explicit published sector required")
    maturity = number(maturity_years, "maturity_years", 1, 30)
    step = number(credit_quality_step, "credit_quality_step", 0, 6)
    require(maturity.is_integer(), "maturity_years", "whole-year tenor required; no interpolation", "UNSUPPORTED_METHOD")
    require(step.is_integer(), "credit_quality_step", "integer CQS required")
    as_of, dataset = _archived_dataset(context, market_data)
    credit = dataset["corporate_credit"]
    require(series_id not in credit["blocked_series"], "series_id", "published formula-cache series not qualified", "REVIEW_REQUIRED")
    require(series_id in credit["series"], "series_id", "published series unavailable", "MISSING_INPUT")
    require(context.currency == series_id, "currency", "explicit series/context mismatch; no conversion inferred", "REVIEW_REQUIRED")
    series = credit["series"][series_id]
    table = series["sectors"][sector]["tables"][metric]
    raw = number(table["values"][int(maturity) - 1][int(step)], "published_value", 0,
                 1 if metric == "pd_probability" else None)
    result = raw if metric == "pd_probability" else raw / 100
    coordinate = table["columns"][int(step)] + str(table["row_offset"] + int(maturity))
    return result, {
        **_market_details(dataset),
        "as_of": as_of, "archive_retrieved_at": dataset["retrieved_at"], "series_id": series_id,
        "sector": sector, "table": metric, "maturity_years": int(maturity), "credit_quality_step": int(step),
        "published_value": raw, "source_unit": table["unit"], "source_id": dataset["source_id"],
        "archive_sha256": dataset["archive_sha256"], "member": credit["member"],
        "member_sha256": credit["member_sha256"], "sheet": series["sheet"], "cell": coordinate,
        "baseline_resource_sha256": load_resource("manifest.json")["sha256"]["rfr_monthly.json"],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "exact_published_corporate_cell_not_rating_assignment_or_application_approval",
        "_sources": [dataset["source_id"] + ":" + credit["member"] + ":" + series["sheet"] + "!" + coordinate]}


@calculation("DIR:article-77e:1:b", "DR:article-54:2", unit="ratio")
@_market_input_errors
def rfr_archived_corporate_pd(series_id: str, sector: str, maturity_years: float,
                              credit_quality_step: float, *, qualification_reference: str, context: Context,
                              market_data: dict | None = None):
    """Read the default probability, NOT the similarly named PD credit spread."""
    return _corporate_cell(series_id, sector, maturity_years, credit_quality_step,
                           "pd_probability", qualification_reference, context, market_data)


@calculation("DIR:article-77e:1:b", "DR:article-54:2-4", unit="rate")
@_market_input_errors
def rfr_archived_corporate_spread(series_id: str, sector: str, maturity_years: float,
                                  credit_quality_step: float, table: str, *,
                                  qualification_reference: str, context: Context, market_data: dict | None = None):
    """Read published PD/FS/downgrade spreads, converting percent to decimal rates.

    Exact published tenors only: no interpolation or automatic extension beyond
    year 30. Classification and applicability remain externally qualified.
    """
    require(isinstance(table, str) and table in {"pd_spread", "fundamental_spread", "cost_of_downgrade"},
            "table", "pd_spread, fundamental_spread or cost_of_downgrade required")
    return _corporate_cell(series_id, sector, maturity_years, credit_quality_step,
                           table, qualification_reference, context, market_data)


@calculation("DR:article-54:3", unit="rate")
@_market_input_errors
def rfr_archived_ltas(table: str, series_id: str, maturity_years: float | None = None, *,
                       qualification_reference: str, context: Context, market_data: dict | None = None):
    """Read supplemental LTAS cells with explicit original row identifiers.

    Corporate, country-relative basic-RFR and named-index axes are different;
    none is automatically assigned from context currency. The specific index
    scalar has no maturity axis. Qualification remains external.
    """
    _reference(qualification_reference)
    require(isinstance(table, str) and table in {"corporate_ltas", "basic_rfr_ltas", "specific_ltas"},
            "table", "explicit supplemental LTAS table required")
    require(isinstance(series_id, str) and bool(series_id), "series_id", "published row ID required")
    as_of, dataset = _archived_dataset(context, market_data)
    supplemental = dataset["supplemental_ltas"]
    values = supplemental["tables"][table]
    require(series_id in values["rows"], "series_id", "published row unavailable", "MISSING_INPUT")
    row = values["rows"][series_id]
    if table == "specific_ltas":
        require(maturity_years is None, "maturity_years", "named index scalar has no maturity axis")
        raw, coordinate, maturity = row["value_percent"], row["cell"], None
    else:
        maturity = number(maturity_years, "maturity_years", 1, 30)
        require(maturity.is_integer(), "maturity_years", "whole-year tenor required; no interpolation", "UNSUPPORTED_METHOD")
        maturity = int(maturity)
        raw = row["values_percent"][maturity - 1]
        coordinate = values["columns"][maturity - 1] + str(row["source_row"])
    raw = number(raw, "published_value_percent")
    return raw / 100, {
        **_market_details(dataset),
        "as_of": as_of, "archive_retrieved_at": dataset["retrieved_at"], "table": table,
        "series_id": series_id, "maturity_years": maturity, "published_value_percent": raw,
        "source_unit": "percent", "source_id": dataset["source_id"],
        "archive_sha256": dataset["archive_sha256"], "member": supplemental["member"],
        "member_sha256": supplemental["member_sha256"], "sheet": values["sheet"], "cell": coordinate,
        "baseline_resource_sha256": load_resource("manifest.json")["sha256"]["rfr_monthly.json"],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "published_ltas_not_automatic_asset_currency_classification_or_calibration",
        "_sources": [dataset["source_id"] + ":" + supplemental["member"] + ":" + values["sheet"] + "!" + coordinate]}


def _archived_dataset(context, market_data):
    if market_data is None:
        data = effective_resource("rfr_monthly.json", context)
    else:
        require(isinstance(market_data, dict), "market_data", "JSON object required")
        require(not any(o.resource == "rfr_monthly.json" for o in context.overrides),
                "market_data", "edit supplied data explicitly; bundled-market overrides cannot be combined with external tables")
        data = market_data
    require(data.get("schema_version") == 1, "market_data", "schema_version 1 required")
    require(data.get("status") in {"SYNTHETIC_DEMO", "USER_SUPPLIED"},
            "market_data", "explicit SYNTHETIC_DEMO or USER_SUPPLIED status required")
    require(isinstance(data.get("datasets"), dict), "market_data", "datasets mapping required")
    as_of = date.fromisoformat(context.as_of).isoformat()
    require(as_of in data["datasets"], "as_of", "exact archived month unavailable; no carry-forward", "MISSING_INPUT")
    dataset = data["datasets"][as_of]
    require(isinstance(dataset, dict) and dataset.get("data_kind") == data["status"],
            "market_data", "dataset data_kind must match top-level status")
    for key in ("source_id", "retrieved_at", "archive_sha256"):
        require(isinstance(dataset.get(key), str) and bool(dataset[key].strip()),
                "market_data", "nonempty " + key + " required")
    fingerprint(dataset)  # Reject non-finite/non-JSON inputs, including unused fields.
    require(date.fromisoformat(context.known_at) >= date.fromisoformat(dataset["retrieved_at"]),
            "known_at", "availability of this archive revision before retrieval is unverified", "REVIEW_REQUIRED")
    if dataset["data_kind"] == "SYNTHETIC_DEMO":
        warnings.warn("SYNTHETIC_DEMO: invented market inputs, not for production valuation.", UserWarning, stacklevel=3)
    return as_of, dataset


@calculation("DIR:article-77e:1:a-c", "DIR:article-77e:3", unit="rate")
@_market_input_errors
def rfr_archived_spot_rate(series_id: str, maturity_years: float, variant: str, *,
                            qualification_reference: str, context: Context, market_data: dict | None = None):
    """Read one published annual zero-coupon rate, preserving cell provenance.

    Archive retrieval date is a conservative knowledge bound for this exact file
    revision, not an inferred original publication date. Raw currency matches are
    necessary but not sufficient qualification; known anomalies remain blocked.
    """
    _reference(qualification_reference)
    require(isinstance(series_id, str) and bool(series_id), "series_id", "explicit published series ID required")
    require(isinstance(variant, str) and variant in {"no_va", "with_va"},
            "variant", "no_va or with_va required")
    as_of, dataset = _archived_dataset(context, market_data)
    require(series_id in dataset["series"], "series_id", "published series unavailable", "MISSING_INPUT")
    require(series_id not in dataset["blocked_series"], "series_id",
            dataset["blocked_series"].get(series_id, "series qualification unresolved"), "REVIEW_REQUIRED")
    series = dataset["series"][series_id]
    require(context.currency == series["raw_currency_metadata"], "currency",
            "context does not match published currency metadata; no conversion inferred", "REVIEW_REQUIRED")
    maturity = number(maturity_years, "maturity_years", 1)
    require(maturity.is_integer(), "maturity_years", "only published whole-year tenors; no interpolation", "UNSUPPORTED_METHOD")
    require(int(maturity) in dataset["maturities"], "maturity_years", "published tenor unavailable", "MISSING_INPUT")
    curve = series["variants"][variant]
    va = curve["raw_metadata"]["VA"]
    if variant == "with_va":
        require(isinstance(va, (int, float)) and not isinstance(va, bool), "variant",
                "published VA is unavailable for this series, despite copied curve values", "UNSUPPORTED_METHOD")
    index = dataset["maturities"].index(int(maturity))
    rate = number(curve["rates"][index], "spot_rate")
    require(rate > -1, "spot_rate", "annual zero-coupon rate must exceed -1", "REVIEW_REQUIRED")
    coordinate = series["column"] + str(dataset["rate_row_offset"] + int(maturity))
    return rate, {
        **_market_details(dataset),
        "as_of": as_of, "archive_retrieved_at": dataset["retrieved_at"],
        "series_id": series_id, "series_label": series["label"], "variant": variant,
        "maturity_years": int(maturity), "unit": dataset["unit"],
        "raw_currency_metadata": series["raw_currency_metadata"],
        "currency_metadata_status": series["currency_metadata_status"],
        "source_id": dataset["source_id"], "archive_sha256": dataset["archive_sha256"],
        "member": dataset["member"], "member_sha256": dataset["member_sha256"],
        "sheet": curve["sheet"], "cell": coordinate,
        "baseline_resource_sha256": load_resource("manifest.json")["sha256"]["rfr_monthly.json"],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "exact_archived_spot_only_not_legal_curve_application",
        "_sources": [dataset["source_id"] + ":" + dataset["member"] + ":" + curve["sheet"] + "!" + coordinate]}


@calculation("DIR:article-77e:1:b", "DIR:article-77e:3", "DR:article-54:3", unit="rate")
@_market_input_errors
def rfr_archived_government_spread(country_id: str, maturity_years: float, table: str, *,
                                   qualification_reference: str, context: Context, market_data: dict | None = None):
    """Read a published government LTAS/FS parameter and convert percent to decimal.

    Country is the published parameter axis, including the EUR aggregate; it is
    not a currency inference or automatic asset classification. Do not transfer
    spot-curve currency metadata blocks to this distinct government-table axis.
    """
    _reference(qualification_reference)
    require(isinstance(country_id, str) and bool(country_id), "country_id", "published country ID required")
    require(isinstance(table, str) and table in {"ltas", "fundamental_spread"},
            "table", "ltas or fundamental_spread required")
    as_of, dataset = _archived_dataset(context, market_data)
    government = dataset["government_spreads"]
    values = government["tables"][table]
    require(country_id in values["rows"], "country_id", "published country unavailable", "MISSING_INPUT")
    maturity = number(maturity_years, "maturity_years", 1)
    require(maturity.is_integer(), "maturity_years", "whole-year published tenor required", "UNSUPPORTED_METHOD")
    require(int(maturity) in values["maturities"], "maturity_years", "published tenor unavailable", "MISSING_INPUT")
    row = values["rows"][country_id]
    index = values["maturities"].index(int(maturity))
    percent = number(row["values_percent"][index], "published_value_percent", 0 if table == "fundamental_spread" else None)
    coordinate = values["columns"][index] + str(row["source_row"])
    return percent / 100, {
        **_market_details(dataset),
        "as_of": as_of, "archive_retrieved_at": dataset["retrieved_at"], "country_id": country_id,
        "table": table, "maturity_years": int(maturity), "published_value_percent": percent,
        "source_unit": "percent", "result_unit": "decimal_rate", "source_id": dataset["source_id"],
        "archive_sha256": dataset["archive_sha256"], "member": government["member"],
        "member_sha256": government["member_sha256"], "sheet": values["sheet"], "cell": coordinate,
        "baseline_resource_sha256": load_resource("manifest.json")["sha256"]["rfr_monthly.json"],
        "qualification_reference": qualification_reference, "qualification_status": "EXTERNAL_UNVERIFIED",
        "scope": "published_government_parameter_not_currency_inference_or_application_approval",
        "_sources": [dataset["source_id"] + ":" + government["member"] + ":" + values["sheet"] + "!" + coordinate]}
