"""Offline DPM-to-XBRL assembly, with explicit remaining validation duties.

Technical releases are chosen explicitly. Output is a draft, never an implicit
submission approval. In particular, successful serialization cannot turn
unexecuted business rules or externally qualified scope into a PASS.
"""
from hashlib import sha256
import re

from .core import CalculationError, _resource_snapshot, fingerprint, require
from .reporting_catalog import (reporting_catalog, reporting_data, reporting_table,
                                _reporting_xbrl_preconditions, _reporting_validation_metadata)
from .reporting_instance_binding import bind_cell_fact
from .reporting_instance_xml import write_instance


def _filing_unit(template_code):
    """Archived filing checks use template families, without the variant suffix.

    E.g. DPM S.01.02.01 -> filing unit S.01.02. Source-check tests compare
    the resulting module sets against original *-find-check.xml assertions.
    This is unrelated to metric prefix spelling; no QName is normalized.
    """
    if not isinstance(template_code, str) or re.fullmatch(r"[A-Z]+\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}", template_code) is None:
        raise ValueError("Unsupported archived template variant code")
    return template_code.rsplit(".", 1)[0]


def reporting_instance(facts, *, technical_version, module, entity, instant,
                       indicators, qualification_reference, validation_codes=None, filing_overrides=()):
    """Assemble a deterministic draft and cell-to-fact reconciliation.

    Each input is {business_code, atom, open_dimensions?, unit?}. The complete
    archived BusinessCode (including braces) is mandatory. Caller-selected
    technical version/module and applicability reference are not auto-approved.
    Returns XML text, its SHA-256, source evidence and explicit pending checks.
    No network, filesystem writes or submission is performed.
    Optional validation_codes are explicitly selected archived rules; supported
    closed-cell checks use these same facts. Unselected rules remain unchecked.
    "ALL_MODULE" attempts the union of archived module links and workbook duties;
    unresolved rules stay visible and never imply full-report validation.
    filing_overrides are explicit NumericOverride objects for archived precision
    parameters; original values and reasons remain in the returned audit.
    """
    require(isinstance(qualification_reference, str) and bool(qualification_reference.strip()),
            "qualification_reference", "external reporting-scope qualification required", "MISSING_INPUT")
    require(isinstance(facts, list) and bool(facts), "facts", "nonempty explicit fact list required")
    all_module = validation_codes == "ALL_MODULE"
    codes = [] if validation_codes is None or all_module else validation_codes
    require(isinstance(codes, list) and all(isinstance(code, str) and bool(code) for code in codes)
            and len(set(codes)) == len(codes), "validation_codes", "unique explicit rule codes required")
    with _resource_snapshot():
        catalog = reporting_catalog(technical_version=technical_version)
        require(isinstance(module, str) and module in catalog["modules"],
                "module", "unknown module in selected technical version", "UNSUPPORTED_PARAMETER")
        selected = catalog["modules"][module]
        templates = {}
        for row in selected["templates"]:
            templates.setdefault(_filing_unit(row["code"]), set()).update(row["table_codes"])
        require(isinstance(indicators, dict) and bool(indicators) and all(
            key in templates and type(value) is bool for key, value in indicators.items()),
            "indicators", "explicit Boolean indicators from the selected module required")
        structure = reporting_data("structure", technical_version=technical_version)["tables"]
        cells = reporting_data("cells", technical_version=technical_version)["tables"]["mTableCell"]
        dictionary = reporting_data("dictionary", technical_version=technical_version)["tables"]
        metadata = _reporting_xbrl_preconditions(technical_version=technical_version)
        validation_metadata = None
        if all_module:
            from .reporting_instance_rules import module_rule_codes
            validation_metadata = _reporting_validation_metadata(technical_version=technical_version)
            try:
                codes = module_rule_codes(metadata, validation_metadata, module)
            except ValueError as error:
                raise CalculationError("REVIEW_REQUIRED", "validation_codes", str(error)) from error
        require(bool(metadata.get("dictionary_elements")), "resources",
                "original dictionary declarations must be built", "RESOURCE_INTEGRITY")
        table_codes = {row["TableID"]: row["TableCode"] for row in structure["mTable"]}
        module_tables = set().union(*templates.values())
        by_code = {}
        for cell in cells:
            if table_codes.get(cell["TableID"]) in module_tables:
                by_code.setdefault(cell["BusinessCode"], []).append(cell)
        bound, mapped_facts, reconciliation, represented = [], [], [], set()
        try:
            for index, fact in enumerate(facts):
                if not isinstance(fact, dict) or not {"business_code", "atom"} <= set(fact) or set(fact) - {
                    "business_code", "atom", "open_dimensions", "unit"
                }:
                    raise ValueError("Explicit business_code/atom and supported fact fields required")
                code = fact["business_code"]
                if not isinstance(code, str) or len(by_code.get(code, [])) != 1:
                    raise ValueError("Unknown or ambiguous cell in selected module")
                cell = by_code[code][0]
                table_code = table_codes[cell["TableID"]]
                owners = {key for key, codes in templates.items() if table_code in codes}
                positive = {key for key in owners if indicators.get(key) is True}
                if not positive:
                    raise ValueError("Fact is not covered by a positive filing indicator")
                represented.update(positive)
                mapped = bind_cell_fact(cell, fact["atom"], fact.get("open_dimensions", {}),
                                        unit=fact.get("unit"), tables=dictionary,
                                        namespaces=metadata["dictionary_namespaces"],
                                        declarations=metadata["dictionary_elements"])
                bound.append(mapped["fact"])
                mapped_facts.append(mapped)
                reconciliation.append({"input_index": index, "business_code": code,
                                       "cell_id": cell["CellID"], "table_code": table_code,
                                       "positive_templates": sorted(positive),
                                       "metric": mapped["fact"]["metric"],
                                       "omitted_explicit_defaults": mapped["omitted_explicit_defaults"],
                                       "schema_member": mapped["schema_declaration"]["member"],
                                       "schema_sha256": mapped["schema_declaration"]["sha256"]})
            if represented != {key for key, filed in indicators.items() if filed}:
                raise ValueError("Positive filing indicator without facts")
            namespaces = {**metadata["dictionary_namespaces"],
                          "iso4217": "http://www.xbrl.org/2003/iso4217"}
            xml = write_instance(schema_uri=selected["schema_uri"], entity=entity, instant=instant,
                                 indicators=indicators, facts=bound, namespaces=namespaces)
        except CalculationError:
            raise
        except (TypeError, ValueError) as error:
            raise CalculationError("INVALID_INPUT", "reporting_instance", str(error)) from error
        from .reporting_instance_currency import check_instance_currency
        from .reporting_instance_precision import check_instance_precision, filing_policy

        currency_checks = check_instance_currency(mapped_facts, tables=dictionary)
        try:
            policy, override_audit, policy_hash = filing_policy(catalog, filing_overrides)
            precision_checks = check_instance_precision(mapped_facts, policy=policy)
        except (TypeError, ValueError) as error:
            raise CalculationError("INVALID_INPUT", "filing_overrides", str(error)) from error
        checks = []
        if codes:
            from .reporting_instance_rules import check_instance_rules

            rules = reporting_data("rules", technical_version=technical_version)
            checks = check_instance_rules(
                codes, facts=facts, reconciliation=reconciliation, entity=entity, instant=instant,
                indicators=indicators, module=module, technical_version=technical_version,
                qualification_reference=qualification_reference,
                rules=rules["tables"]["vValidationRuleExpressions"], rule_source=rules["source"],
                metadata=metadata, validation_metadata=(validation_metadata if validation_metadata is not None
                    else _reporting_validation_metadata(technical_version=technical_version)),
                table_lookup=lambda code: reporting_table(code, technical_version=technical_version))
        return {"status": "DRAFT_XBRL_INSTANCE", "technical_version": technical_version, "module": module,
                "xml": xml.decode("utf-8"), "xml_sha256": sha256(xml).hexdigest(),
                "source": catalog["source"], "xbrl_source_id": metadata["source_id"],
                "xbrl_archive_sha256": metadata["archive_sha256"], "reconciliation": reconciliation,
                "qualification_reference": qualification_reference,
                "input_hash": fingerprint({"facts": facts, "technical_version": technical_version,
                                           "module": module, "entity": entity, "instant": instant,
                                           "indicators": indicators, "qualification_reference": qualification_reference,
                                           "validation_codes": codes, "validation_selection": "ALL_MODULE" if all_module else "EXPLICIT",
                                           "filing_policy_hash": policy_hash}),
                "selected_rule_checks": checks, "all_archived_rules_executed": False,
                "rule_selection": {"mode": "ALL_MODULE" if all_module else "EXPLICIT",
                                   "codes": codes, "all_module_candidates_attempted": all_module,
                                   "attempted_count": len(checks),
                                   "unresolved_codes": [r["validation_code"] for r in checks if r["status"] == "REVIEW_REQUIRED"]},
                "currency_checks": currency_checks,
                "precision_checks": precision_checks, "filing_policy_hash": policy_hash,
                "filing_parameter_overrides": override_audit,
                "filing_policy_status": "ANALYST_OVERRIDE_NOT_APPROVED" if override_audit else "ARCHIVED_SOURCE_PARAMETERS",
                "xml_well_formed": True, "cell_metric_datatypes_checked": True,
                "full_report_validated": False, "submission_ready": False,
                "pending_checks": ["LEGAL_AND_TEMPLATE_COMPLETENESS", "ENTITY_IDENTIFIER_QUALIFICATION",
                                   "REPORTING_CURRENCY_AND_PRECISION", "ROW_KEYS_AND_OPEN_AXIS_HIERARCHIES",
                                   "XML_SCHEMA_AND_XBRL_DIMENSIONS", "BUSINESS_RULES_AND_DEACTIVATIONS",
                                   "NATIONAL_FILING_REQUIREMENTS"]}
