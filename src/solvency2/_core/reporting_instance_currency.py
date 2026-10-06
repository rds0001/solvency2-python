"""Filing Rules III.8 currency/unit reconciliation, without conversion.

SRC-0467/SRC-0430: ei1930 declares reporting currency, nonmonetary numbers
use xbrli:pure. AF=x1/OC identifies semi-open original-currency facts. Open MD
currency pairing uses the archived derivative UI join when supported; other
pairings remain review, never silently forced to reporting currency.
"""
import re


ISO = "http://www.xbrl.org/2003/iso4217"
INSTANCE = "http://www.xbrl.org/2003/instance"
DIM = "http://eiopa.europa.eu/xbrl/s2c/dict/dim"
CU = "http://eiopa.europa.eu/xbrl/s2c/dict/dom/CU"
CA = "http://eiopa.europa.eu/xbrl/s2c/dict/dom/CA"


def _derivative_key(fact):
    """Actual UI typed value/domain plus SU; no positional or fuzzy row join."""
    dimensions = {(d["dimension"]["namespace"], d["dimension"]["local_name"]): d for d in fact["dimensions"]}
    ui, scope = dimensions.get((DIM, "UI")), dimensions.get((DIM, "SU"))
    if (not ui or "domain" not in ui or not isinstance(ui.get("text"), str) or not ui["text"].strip()
            or not scope or "member" not in scope):
        return None
    return (ui["domain"]["namespace"], ui["domain"]["local_name"], ui["text"],
            scope["member"]["namespace"], scope["member"]["local_name"])


def _derivative_currency_index(mapped):
    """One index per draft; thousands of rows must not cause quadratic joins."""
    index = {}
    for row in mapped:
        parts = row["business_code"].strip("{}").split(",")
        if (row["fact"]["metric"]["local_name"] != "ei1024" or "C0370" not in parts
                or re.fullmatch(r"S\.08\.01\.(01|04)\.02", parts[0]) is None):
            continue
        key = _derivative_key(row["fact"])
        if key is not None:
            index.setdefault((parts[0], key), []).append(row)
    return index


def _open_currency_pair(row, index):
    """III.8 comparison identified by original TV1002_1/2, not full assertion execution.

    Original archives bind mi2822 to ei1024 by UI, with SU=x169. Source DPM
    binding already excludes dimensions outside the exact cells. Missing or
    ambiguous counterpart facts remain review rather than defaulting currency.
    """
    parts = row["business_code"].strip("{}").split(",")
    match = re.fullmatch(r"S\.08\.01\.(01|04)\.01", parts[0])
    key = _derivative_key(row["fact"])
    if (row["fact"]["metric"]["local_name"] != "mi2822" or not match or "C0131" not in parts
            or key is None or key[-2:] != ("http://eiopa.europa.eu/xbrl/s2c/dict/dom/MC", "x169")):
        return {"status": "REVIEW_REQUIRED", "reason": "OPEN_MD_CURRENCY_PAIRING_ASSERTION_REQUIRED"}
    candidates = index.get((parts[0][:-2] + "02", key), [])
    if len(candidates) != 1:
        return {"status": "REVIEW_REQUIRED", "reason": "NO_UNIQUE_OPEN_CURRENCY_COUNTERPART"}
    counterpart = candidates[0]
    currency = counterpart["fact"]["atom"].get("qname")
    agrees = (isinstance(currency, dict) and currency.get("namespace") == CU
              and currency.get("local_name") == row["fact"]["unit"]["local_name"])
    return {"status": "PASS" if agrees else "FAIL",
            "reason": "OPEN_CURRENCY_PAIR_MATCH" if agrees else "OPEN_CURRENCY_PAIR_MISMATCH",
            "currency_cell": counterpart["business_code"], "join_dimension": "s2c_dim:UI",
            "source_comparison": "TV1002_1" if match[1] == "01" else "TV1002_2",
            "full_xbrl_assertion_executed": False}


def check_instance_currency(mapped, *, tables):
    """Return per-numeric-fact findings, never an overall filing approval."""
    currency_domains = {row["DomainID"] for row in tables["mDomain"] if row["DomainCode"] == "CU"}
    currency_codes = {row["MemberCode"] for row in tables["mMember"]
                      if row["DomainID"] in currency_domains
                      and re.fullmatch(r"[A-Z]{3}", row["MemberCode"])}
    labels = {row["MemberCode"]: row["MemberLabel"] for row in tables["mMember"]}
    declarations = [row["fact"]["atom"].get("qname") for row in mapped
                    if row["fact"]["metric"]["local_name"] == "ei1930"]
    currency = declarations[0] if len(declarations) == 1 else None
    valid_currency = (isinstance(currency, dict) and currency.get("namespace") == CU
                      and currency.get("local_name") in currency_codes)
    results = []
    derivative_currencies = _derivative_currency_index(mapped)
    for row in mapped:
        dtype = row["metric_check"]["data_type"]
        if dtype not in ("Monetary", "Decimal", "Percent", "Integer"):
            continue
        fact = row["fact"]
        unit = fact["unit"]
        result = {"business_code": row["business_code"], "status": "PASS", "rule": "III.8"}
        if dtype != "Monetary":
            if unit != {"namespace": INSTANCE, "local_name": "pure"}:
                result.update(status="FAIL", reason="NONMONETARY_UNIT_MUST_BE_XBRLI_PURE")
        elif unit.get("namespace") != ISO or unit.get("local_name") not in currency_codes:
            result.update(status="FAIL", reason="MONETARY_UNIT_MUST_BE_ARCHIVED_ISO_CURRENCY")
        else:
            dimensions = {(dim["dimension"]["namespace"], dim["dimension"]["local_name"]): dim.get("member")
                          for dim in fact["dimensions"]}
            approach = dimensions.get((DIM, "AF"))
            original = dimensions.get((DIM, "OC"))
            if approach == {"namespace": CA, "local_name": "x1"}:
                if (not isinstance(original, dict) or original.get("namespace") != CU
                        or original.get("local_name") != unit["local_name"]):
                    result.update(status="FAIL", reason="ORIGINAL_CURRENCY_DIMENSION_UNIT_MISMATCH")
                elif not valid_currency:
                    result.update(status="REVIEW_REQUIRED", reason="NO_UNIQUE_REPORTING_CURRENCY_DECLARATION")
            elif "|AF/Expressed in currency of denomination (not converted to reporting currency)" in (
                labels.get(fact["metric"]["local_name"]) or ""
            ):
                result.update(_open_currency_pair(row, derivative_currencies))
                if result["status"] == "PASS" and not valid_currency:
                    result.update(status="REVIEW_REQUIRED", reason="NO_UNIQUE_REPORTING_CURRENCY_DECLARATION")
            elif not valid_currency:
                result.update(status="REVIEW_REQUIRED", reason="NO_UNIQUE_REPORTING_CURRENCY_DECLARATION")
            elif original == currency:
                # III.8: an explicitly identified original currency equal to
                # reporting currency must use AF=CA:x1, even without conversion.
                # Do not infer original currency for ordinary closed facts or
                # Total/NA: those have no such denomination assertion.
                result.update(status="FAIL", reason="SAME_ORIGINAL_CURRENCY_REQUIRES_UNCONVERTED_APPROACH")
            elif unit["local_name"] != currency["local_name"]:
                result.update(status="FAIL", reason="MONETARY_UNIT_REPORTING_CURRENCY_MISMATCH")
        results.append(result)
    return {"rule_source_sections": ["III.8 / 3.1", "III.8 / 3.2(a)"],
            "reporting_currency": currency if valid_currency else None,
            "findings": results, "full_currency_validation": False,
            "open_md_pairing_and_required_conversion_approach_verified": False}
