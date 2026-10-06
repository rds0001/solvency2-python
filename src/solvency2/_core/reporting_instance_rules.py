"""Reuse archived rule components on the exact facts of an assembled draft.

Selection is explicit, never disguised as exhaustive validation. Unsupported
bindings, uncertain activation and missing indicators remain review results.
"""
from .core import CalculationError
from .reporting_bound_rule import check_bound_rule
from .reporting_closed_binding import bind_rule_selectors
from .reporting_preconditions import check_module_precondition
from .reporting_validation_status import assess_archived_rule


def module_rule_codes(metadata, validation_metadata, module):
    """Union original module links and workbook duties; never only runnable rules.

    Malformed workbook module declarations remain review candidates rather than
    disappearing. Non-XBRL duties and unknown expression codes are kept too.
    """
    from .reporting_validation_status import module_severities

    codes = set()
    for record in metadata["modules"][module]["preconditions"]:
        fragment = metadata["assertions"][record["assertion_key"]]["fragment"]
        if not isinstance(fragment, str) or not fragment.startswith("s2md_") or not fragment[5:]:
            raise ValueError("Module assertion lacks an unambiguous source rule code")
        codes.add(fragment[5:])
    for entry in validation_metadata["rows"]:
        row = entry["values"]
        code = row.get("Rule code")
        if not isinstance(code, str) or not code:
            raise ValueError("Workbook row lacks an explicit rule code")
        try:
            relevant = module in module_severities(row.get("Severity and modules"))
        except ValueError:
            relevant = True
        if relevant:
            codes.add(code)
    return sorted(codes)


def check_instance_rules(codes, *, facts, reconciliation, entity, instant, indicators,
                         module, technical_version, qualification_reference, rules,
                         rule_source, metadata, validation_metadata, table_lookup):
    """No repeated rule-resource loads; source-qualified table lookup is cached.

    Only existing closed-cell selectors are auto-bound. A rule spanning distinct
    numeric units is left for review, not evaluated as dimensionless arithmetic.
    Neither unreported facts nor omitted filing indicators default to zero/false.
    """
    context = {"entity": entity["scheme"] + ":" + entity["identifier"],
               "period": instant, "unit": "EXPLICIT_PER_FACT_CHECKED_AFTER_SELECTION"}
    records = [{"cell": fact["business_code"], "context": context, "fact": fact["atom"]} for fact in facts]
    unit_by_cell = {row["cell_id"]: facts[row["input_index"]].get("unit") for row in reconciliation}
    by_code = {}
    for rule in rules:
        by_code.setdefault(rule["ValidationCode"], []).append(rule)
    tables = {}

    def lookup(code):
        if code not in tables:
            tables[code] = table_lookup(code)
        return tables[code]

    output = []
    for code in codes:
        item = {"validation_code": code, "status": "REVIEW_REQUIRED", "full_report_validated": False}
        try:
            activation = assess_archived_rule(validation_metadata, code, module)
            item["activation"] = activation
            if activation["active_in_snapshot"] is False:
                item["status"] = "NOT_ACTIVE_IN_SNAPSHOT"
            elif activation["active_in_snapshot"] is None:
                item["reason"] = activation["reason"]
            else:
                precondition = check_module_precondition(metadata, module, code, indicators)
                item["precondition"] = precondition
                if not precondition["precondition_met"]:
                    item["status"] = "FILING_PRECONDITION_FALSE"
                else:
                    selected = by_code.get(code, [])
                    if len(selected) != 1:
                        raise ValueError("No unique archived DPM rule")
                    if selected[0].get("Scope"):
                        from .reporting_scope import check_scoped_closed_rule
                        result = check_scoped_closed_rule(selected[0], lookup, records, context,
                            technical_version=technical_version, binding_reference=qualification_reference,
                            source=rule_source, namespace_loader=lambda: metadata["dictionary_namespaces"],
                            unit_by_cell=unit_by_cell)
                        item.update(status="PASS" if result["value"] else "FAIL", expression=result,
                                    scope_checks=result["scope_checks"], severity=activation["severity"])
                        output.append(item)
                        continue
                    prepared = bind_rule_selectors(selected[0], lookup, records, context)
                    selected_cells = {identifier for evidence in prepared["evidence"].values()
                                      for identifier in evidence["cell_ids"]}
                    units = {tuple(sorted(unit_by_cell[identifier].items())) for identifier in selected_cells
                             if unit_by_cell[identifier] is not None}
                    if len(units) > 1:
                        raise ValueError("Cross-unit expression requires qualified dimensional evaluation")
                    result = check_bound_rule(selected[0], prepared["bindings"], technical_version=technical_version,
                                              binding_reference=qualification_reference, source=rule_source,
                                              namespace_loader=lambda: metadata["dictionary_namespaces"])
                    item.update(status="PASS" if result["value"] else "FAIL", expression=result,
                                cell_bindings=prepared["evidence"], severity=activation["severity"])
        except CalculationError as error:
            if error.code == "RESOURCE_INTEGRITY":
                raise
            item.update(reason=str(error), error_code=error.code)
        except (ValueError, TypeError) as error:
            item["reason"] = str(error)
        output.append(item)
    return output
