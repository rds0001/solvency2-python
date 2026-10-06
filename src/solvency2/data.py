"""Explicit local discount curves; no downloads, interpolation or archive fallback."""
from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from datetime import date
import json
from pathlib import Path
import re
from typing import Mapping

from ._core import Context, Result, best_estimate_cashflows, rfr_spot_discount_factor
from ._core.core import CalculationError, exact_keys, fingerprint, number, require

__all__ = ["DiscountCurve", "load_discount_curve_json", "load_discount_curve_csv",
           "best_estimate_with_curve", "discount_curve_from_spot_rates"]


def _iso_date(value, field):
    require(isinstance(value, str), field, "ISO YYYY-MM-DD string required")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise CalculationError("INVALID_INPUT", field, "ISO YYYY-MM-DD date required") from None
    require(parsed.isoformat() == value, field, "canonical YYYY-MM-DD date required")
    return parsed


def _local_path(path):
    require(isinstance(path, (str, Path)), "path", "explicit local path required")
    text = str(path)
    # Windows drive paths are local; URL schemes, including file://, are not inputs.
    is_drive = re.match(r"^[A-Za-z]:[\\/]", text)
    require(not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", text) or bool(is_drive),
            "path", "URLs are not supported; obtain the file yourself", "UNSUPPORTED_INPUT")
    return Path(path)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "json", "duplicate object key")
        result[key] = value
    return result


@dataclass(frozen=True)
class DiscountCurve:
    """Immutable external factors keyed by payment date, with content provenance.

    Factors above one are valid. No curve is considered an official or approved
    curve merely because its format is valid. Values are never interpolated.
    """

    curve_id: str
    as_of: str
    currency: str
    curve_kind: str
    source_reference: str
    points: tuple[tuple[str, float], ...]

    def __post_init__(self):
        for field in ("curve_id", "source_reference"):
            value = getattr(self, field)
            require(isinstance(value, str) and bool(value.strip()), field, "nonempty reference required")
        valuation_date = _iso_date(self.as_of, "as_of")
        require(isinstance(self.currency, str) and re.fullmatch(r"[A-Z]{3}", self.currency) is not None,
                "currency", "uppercase three-letter currency required")
        require(self.curve_kind in ("base", "va", "ma", "stress", "custom"),
                "curve_kind", "explicit base/va/ma/stress/custom required")
        require(isinstance(self.points, (tuple, list)) and bool(self.points), "points", "nonempty points required")
        normalized = []
        dates = set()
        for point in self.points:
            require(isinstance(point, (tuple, list)) and len(point) == 2,
                    "points", "each point requires a date and a discount factor")
            label, raw = point
            payment_date = _iso_date(label, "points.date")
            require(label not in dates, "points.date", "duplicate payment date")
            require(payment_date >= valuation_date, "points.date", "point precedes curve valuation date")
            factor = number(raw, "points.discount_factor")
            require(factor > 0, "points.discount_factor", "strictly positive discount factor required")
            require(payment_date != valuation_date or factor == 1,
                    "points.discount_factor", "valuation-date discount factor must be one")
            dates.add(label)
            normalized.append((label, factor))
        object.__setattr__(self, "points", tuple(sorted(normalized)))

    @classmethod
    def from_dict(cls, payload: Mapping) -> DiscountCurve:
        """Read the exact version-1 schema also accepted by the JSON loader."""
        keys = ("schema_version", "curve_id", "as_of", "currency", "curve_kind", "source_reference",
                "value_type", "unit", "points")
        exact_keys(payload, keys, "curve")
        require(type(payload["schema_version"]) is int and payload["schema_version"] == 1,
                "schema_version", "only schema version 1 is supported", "UNSUPPORTED_INPUT")
        require(payload["value_type"] == "discount_factor" and payload["unit"] == "dimensionless",
                "value_type/unit", "explicit dimensionless discount factors required")
        require(isinstance(payload["points"], list), "points", "point list required")
        points = []
        for row in payload["points"]:
            exact_keys(row, ("date", "discount_factor"), "points")
            points.append((row["date"], row["discount_factor"]))
        return cls(**{k: payload[k] for k in keys[1:6]}, points=tuple(points))

    def to_dict(self) -> dict:
        """Return an independent, JSON-serializable version-1 payload."""
        return {"schema_version": 1, "curve_id": self.curve_id, "as_of": self.as_of,
                "currency": self.currency, "curve_kind": self.curve_kind,
                "source_reference": self.source_reference, "value_type": "discount_factor",
                "unit": "dimensionless",
                "points": [{"date": label, "discount_factor": value} for label, value in self.points]}

    @property
    def input_hash(self) -> str:
        """Fingerprint canonical values AND metadata, independent of file path/order."""
        return fingerprint(self.to_dict())

    def factor(self, payment_date: str) -> float:
        """Exact date lookup; missing points are not zeros or interpolated values."""
        _iso_date(payment_date, "payment_date")
        points = dict(self.points)
        require(payment_date in points, "payment_date", "explicit discount factor missing", "MISSING_INPUT")
        return points[payment_date]


def _read_local_json(path):
    try:
        with _local_path(path).open(encoding="utf-8") as stream:
            payload = json.load(stream, object_pairs_hook=_unique_object)
    except (OSError, UnicodeError):
        raise CalculationError("INPUT_IO_ERROR", "path", "cannot read local UTF-8 JSON file") from None
    except json.JSONDecodeError:
        raise CalculationError("INVALID_INPUT", "json", "invalid JSON document") from None
    return payload


def load_discount_curve_json(path: str | Path) -> DiscountCurve:
    """Load a local UTF-8 version-1 curve; reject duplicate JSON keys."""
    return DiscountCurve.from_dict(_read_local_json(path))


def load_discount_curve_csv(path: str | Path, *, curve_id: str, as_of: str, currency: str,
                            curve_kind: str, source_reference: str) -> DiscountCurve:
    """Load date,discount_factor CSV; metadata must be supplied explicitly.

    UTF-8, comma separator, decimal point, no unit or locale guessing. Source
    paths are not added to result provenance; use a suitable source reference.
    """
    points = []
    try:
        with _local_path(path).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            require(reader.fieldnames is not None and len(reader.fieldnames) == 2
                    and set(reader.fieldnames) == {"date", "discount_factor"},
                    "csv.header", "exact columns date,discount_factor required")
            for row in reader:
                exact_keys(row, ("date", "discount_factor"), "csv.row")
                try:
                    factor = float(row["discount_factor"])
                except (TypeError, ValueError):
                    raise CalculationError("INVALID_INPUT", "discount_factor", "numeric CSV value required") from None
                points.append((row["date"], factor))
    except (OSError, UnicodeError):
        raise CalculationError("INPUT_IO_ERROR", "path", "cannot read local UTF-8 curve file") from None
    except csv.Error:
        raise CalculationError("INVALID_INPUT", "csv", "invalid CSV curve document") from None
    return DiscountCurve(curve_id, as_of, currency, curve_kind, source_reference, tuple(points))


def discount_curve_from_spot_rates(points: Mapping[str, Mapping], *, curve_id: str,
                                  curve_kind: str, source_reference: str,
                                  time_basis_reference: str, context: Context) -> DiscountCurve:
    """Convert annual-effective decimal spot rates using the existing RFR formula.

    Each payment date maps to annual_effective_rate and time_years. The caller
    supplies year fractions and their convention: no calendar/day-count guess,
    percent conversion, interpolation, or extrapolation is performed. The full
    raw input and convention are fingerprinted in the source reference.
    """
    require(isinstance(context, Context), "context", "Context required", "MISSING_INPUT")
    context.validate()
    require(isinstance(points, Mapping) and bool(points), "points", "nonempty mapping required")
    for name, value in (("source_reference", source_reference), ("time_basis_reference", time_basis_reference)):
        require(isinstance(value, str) and bool(value.strip()), name, "nonempty reference required")
    normalized = {}
    valuation_date = _iso_date(context.as_of, "as_of")
    for label, row in points.items():
        payment_date = _iso_date(label, "points.date")
        require(payment_date >= valuation_date, "points.date", "point precedes valuation date")
        exact_keys(row, ("annual_effective_rate", "time_years"), "points.row")
        rate = number(row["annual_effective_rate"], "annual_effective_rate")
        time = number(row["time_years"], "time_years", 0)
        require((time == 0) == (payment_date == valuation_date), "time_years", "date/time zero mismatch")
        normalized[label] = {"annual_effective_rate": rate, "time_years": time}
    ordered = sorted(normalized)
    require(all(normalized[a]["time_years"] < normalized[b]["time_years"]
                for a, b in zip(ordered, ordered[1:])), "time_years", "times must increase with dates")
    provenance = fingerprint({"points": normalized, "time_basis_reference": time_basis_reference,
                              "compounding": "annual_effective"})
    reference = f"{source_reference}; annual_effective; time_basis:{time_basis_reference}; sha256:{provenance}"
    factors = tuple((label, rfr_spot_discount_factor(
        row["annual_effective_rate"], row["time_years"],
        qualification_reference=reference, context=context).value) for label, row in sorted(normalized.items()))
    return DiscountCurve(curve_id, context.as_of, context.currency, curve_kind, reference, factors)


def best_estimate_with_curve(cashflows: Mapping[str, Mapping], *, curve: DiscountCurve,
                             runoff_complete: bool, cashflow_reference: str, context: Context) -> Result:
    """Bind external factors to expected cashflows and call the existing BE formula.

    Rows contain expected_inflows and expected_outflows in the context currency.
    No projection, curve qualification, VA/MA addition or currency conversion.
    """
    require(isinstance(context, Context), "context", "Context required", "MISSING_INPUT")
    context.validate()
    require(isinstance(curve, DiscountCurve), "curve", "validated DiscountCurve required")
    require(curve.as_of == context.as_of, "curve.as_of", "curve/context dates differ")
    require(curve.currency == context.currency, "curve.currency", "curve/context currencies differ")
    require(isinstance(cashflows, Mapping) and bool(cashflows), "cashflows", "nonempty mapping required")
    bound = {}
    for label, row in cashflows.items():
        exact_keys(row, ("expected_inflows", "expected_outflows"), "cashflows.row")
        bound[label] = {**row, "discount_factor": curve.factor(label)}
    curve_hash = curve.input_hash
    reference = f"{curve.curve_id}; sha256:{curve_hash}; {curve.source_reference}"
    result = best_estimate_cashflows(bound, runoff_complete=runoff_complete,
                                    cashflow_reference=cashflow_reference, curve_reference=reference,
                                    context=context)
    metadata = {key: value for key, value in curve.to_dict().items() if key != "points"}
    return replace(result, details={**result.details,
                                   "user_curve": {**metadata, "input_hash": curve_hash,
                                                  "qualification_status": "EXTERNAL_UNVERIFIED"}})
