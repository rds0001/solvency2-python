"""Restricted typed DPM expressions with explicit externally resolved bindings.

No Python/XPath/SQL evaluation is used. Selectors are opaque, exact source text:
the caller must resolve their scope, defaults and sequence semantics. Optional
explicit dimension metadata supports dim; this() is restricted to a supplied
local-filter candidate. This component does NOT certify binding completeness,
dimension admissibility, or complete XBRL fact selection.
Unknown syntax/functions are rejected even inside an inactive branch.
"""
from dataclasses import dataclass
import re

from .reporting_arithmetic import ReportingNumber as N, aggregate, binary, custom_margin, unary
from .reporting_lei import lei_checksum
from .reporting_strings import compile_pattern, matches, substring
from .reporting_power import source_power
from .reporting_values import ReportingDate, ReportingQName, compare_atomic, expand_qname


class ExpressionError(ValueError):
    """Controlled syntax, binding or numeric support failure."""


@dataclass(frozen=True)
class Node:
    kind: str
    value: str
    children: tuple = ()


_TOKEN = re.compile(r"\s+|i(?:<=|>=|!=|=|<|>|\+|-|\*|/)|<=|>=|!=|[=<>+*/(),-]|(?:\d+(?:\.\d*)?|\.\d+)|[A-Za-z_][A-Za-z_0-9]*")
_PRECEDENCE = {"or": 10, "and": 20, **{op: 30 for op in ("=", "!=", "<", "<=", ">", ">=", "i=", "i!=", "i<", "i<=", "i>", "i>=")},
               **{op: 40 for op in ("+", "-", "i+", "i-")}, **{op: 50 for op in ("*", "/", "i*", "i/")}}
_OPERATIONS = {"+": "add", "-": "subtract", "*": "multiply", "/": "divide", "=": "equal", "!=": "equal",
               "<": "less", "<=": "less_equal", ">": "greater", ">=": "greater_equal"}
_MARGINS = {"customMarginEqual": "equal", "customMarginLessThan": "less",
            "customMarginLessThanOrEqual": "less_equal", "customMarginGreaterThan": "greater",
            "customMarginGreaterThanOrEqual": "greater_equal"}
_ARITY = {"true": (0, 0), "false": (0, 0), "emptySequence": (0, 0), "not": (1, 1),
          "isNull": (1, 1), "isnull": (1, 1), "count": (1, 1), "sum": (1, 1), "isum": (1, 1),
          "abs": (1, 1), "iabs": (1, 1), "min": (1, 100), "max": (1, 100),
          "imin": (1, 100), "imax": (1, 100), **{name: (3, 3) for name in _MARGINS}}
_ARITY.update({"localName": (1, 1), "LocalName": (1, 1)})
_ARITY["leiChecksum"] = (1, 1)
_ARITY.update({"matches": (2, 2), "substring": (2, 3)})
_ARITY.update({"this": (0, 0), "dim": (2, 2), "exp": (3, 3)})


def _tokens(text):
    result, position = [], 0
    while position < len(text):
        if text[position] == "{":
            start, depth, quote = position, 0, None
            while position < len(text):
                char = text[position]
                if quote:
                    if char == quote:
                        if position + 1 < len(text) and text[position + 1] == quote:
                            position += 2
                            continue
                        quote = None
                elif char in ("'", '"'):
                    quote = char
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                position += 1
                if depth == 0:
                    break
            if depth or quote:
                raise ExpressionError("UNSUPPORTED_SYNTAX: unclosed selector")
            result.append(text[start:position])
        elif text[position] in ("'", '"'):
            start, quote = position, text[position]
            position += 1
            while position < len(text):
                if text[position] == quote:
                    if position + 1 < len(text) and text[position + 1] == quote:
                        position += 2
                        continue
                    position += 1
                    break
                position += 1
            else:
                raise ExpressionError("UNSUPPORTED_SYNTAX: unclosed string")
            result.append(text[start:position])
        elif text[position] == "[":
            end = text.find("]", position + 1)
            if end < 0:
                raise ExpressionError("UNSUPPORTED_SYNTAX: unclosed QName")
            result.append(text[position:end + 1])
            position = end + 1
        else:
            match = _TOKEN.match(text, position)
            if match is None:
                raise ExpressionError(f"UNSUPPORTED_SYNTAX at character {position}")
            position = match.end()
            if not match[0].isspace():
                result.append(match[0])
        if len(result) > 20000:
            raise ExpressionError("TECHNICAL_LIMIT: token count")
    return result


class _Parser:
    def __init__(self, tokens):
        self.tokens, self.position, self.depth = tokens, 0, 0

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def take(self, expected=None):
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise ExpressionError(f"UNSUPPORTED_SYNTAX: expected {expected or 'operand'}")
        self.position += 1
        return token

    def expression(self, minimum=0):
        self.depth += 1
        if self.depth > 100:
            raise ExpressionError("TECHNICAL_LIMIT: expression nesting")
        try:
            token = self.take()
            if token == "if":
                condition = self.expression()
                self.take("then")
                yes = self.expression()
                self.take("else")
                left = Node("if", "", (condition, yes, self.expression()))
            elif token in ("+", "-", "i-", "i+"):
                left = Node("unary", token, (self.expression(60),))
            elif token == "(":
                left = self.expression()
                self.take(")")
            elif token.startswith("{"):
                left = Node("selector", token)
            elif token.startswith(("'", '"')):
                left = Node("string", token[1:-1].replace(token[0] * 2, token[0]))
            elif re.fullmatch(r"\[(?:[A-Za-z_][A-Za-z_0-9.-]*:[A-Za-z_][A-Za-z_0-9.-]*|Default)\]", token):
                left = Node("qname", token[1:-1])
            elif re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)", token):
                left = Node("number", token)
            elif token in _ARITY:
                self.take("(")
                args = []
                if self.peek() != ")":
                    args.append(self.expression())
                    while self.peek() == ",":
                        self.take(",")
                        args.append(self.expression())
                self.take(")")
                lower, upper = _ARITY[token]
                if not lower <= len(args) <= upper:
                    raise ExpressionError("UNSUPPORTED_ARITY: " + token)
                left = Node("call", token, tuple(args))
            else:
                raise ExpressionError("UNSUPPORTED_SYNTAX_OR_FUNCTION: " + token)
            compared = False
            while self.peek() in _PRECEDENCE and _PRECEDENCE[self.peek()] >= minimum:
                operator = self.take()
                precedence = _PRECEDENCE[operator]
                if precedence == 30 and compared:
                    raise ExpressionError("UNSUPPORTED_SYNTAX: chained comparison")
                if precedence == 30:
                    compared = True
                left = Node("binary", operator, (left, self.expression(precedence + 1)))
            return left
        finally:
            self.depth -= 1


def parse(text):
    """Parse the supported numeric/typed subset; no executable host code."""
    if not isinstance(text, str) or not text.strip() or len(text) > 100000:
        raise ExpressionError("TECHNICAL_LIMIT_OR_INVALID_INPUT: expression text")
    parser = _Parser(_tokens(text))
    node = parser.expression()
    if parser.peek() is not None:
        raise ExpressionError("UNSUPPORTED_SYNTAX: trailing token")
    pending = [(node, 1)]
    while pending:
        current, depth = pending.pop()
        if depth > 100:
            raise ExpressionError("TECHNICAL_LIMIT: evaluation nesting")
        if current.kind == "call" and current.value == "matches" and current.children[1].kind == "string":
            try:
                compile_pattern(current.children[1].value)
            except ValueError as error:
                raise ExpressionError(str(error)) from error
        pending.extend((child, depth + 1) for child in current.children)
    return node


def _boolean(value):
    if not isinstance(value, bool):
        raise ExpressionError("TYPE_ERROR: boolean required")
    return value


def _number(value, interval=True):
    if not isinstance(value, N):
        raise ExpressionError("TYPE_ERROR: explicit numeric binding required")
    return value if interval else N(value.value)


def _sequence(value):
    values = value if isinstance(value, (list, tuple)) else [value]
    return [_number(item) for item in values]


def _run(node, resolver, qnames, metadata):
    if node.kind == "number":
        return N(node.value)
    if node.kind == "string":
        return node.value
    if node.kind == "qname":
        return qnames[node.value]
    if node.kind == "selector":
        try:
            return resolver(node.value)
        except KeyError as error:
            raise ExpressionError("MISSING_BINDING: " + node.value) from error
    if node.kind == "if":
        branch = 1 if _boolean(_run(node.children[0], resolver, qnames, metadata)) else 2
        return _run(node.children[branch], resolver, qnames, metadata)
    if node.kind == "unary":
        operand = _number(_run(node.children[0], resolver, qnames, metadata), node.value.startswith("i"))
        return unary("negate", operand) if node.value.endswith("-") else operand
    if node.kind == "binary":
        left = _run(node.children[0], resolver, qnames, metadata)
        if node.value == "and":
            return _boolean(left) and _boolean(_run(node.children[1], resolver, qnames, metadata))
        if node.value == "or":
            return _boolean(left) or _boolean(_run(node.children[1], resolver, qnames, metadata))
        right = _run(node.children[1], resolver, qnames, metadata)
        interval = node.value.startswith("i")
        operator = node.value[1:] if interval else node.value
        if not interval and operator in ("=", "!=", "<", "<=", ">", ">=") and not (isinstance(left, N) and isinstance(right, N)):
            return compare_atomic(operator, left, right)
        result = binary(_OPERATIONS[operator], _number(left, interval), _number(right, interval))
        return not result if operator == "!=" else result
    name = node.value
    if name == "this":
        if metadata["current_fact"] is None:
            raise ExpressionError("MISSING_FACT_CONTEXT: this() requires a filter candidate")
        return metadata["current_fact"][0]
    args = [_run(child, resolver, qnames, metadata) for child in node.children]
    if name == "dim":
        target = node.children[0]
        if args[0] is None or isinstance(args[0], (list, tuple)) or not isinstance(args[1], ReportingQName):
            raise ExpressionError("UNSUPPORTED_ARGUMENT: scalar fact and expanded dimension name required")
        if target.kind == "selector":
            dimensions = metadata["dimensions"].get(target.value)
        elif target.kind == "call" and target.value == "this":
            dimensions = metadata["current_fact"][1]
        else:
            raise ExpressionError("UNSUPPORTED_ARGUMENT: dim requires a fact selector or this()")
        if not isinstance(dimensions, dict) or args[1] not in dimensions:
            raise ExpressionError("MISSING_DIMENSION_BINDING: no implicit dimension defaults")
        return dimensions[args[1]]
    if name == "exp":
        exponents = [_number(arg, False).value for arg in args[1:]]
        if any(value.denominator != 1 for value in exponents):
            raise ExpressionError("UNSUPPORTED_ARGUMENT: integer exponent numerator/denominator required")
        return source_power(_number(args[0], False), *[int(value) for value in exponents])
    if name == "true":
        return True
    if name == "false":
        return False
    if name == "emptySequence":
        return []
    if name == "not":
        return not _boolean(args[0])
    if name in ("isNull", "isnull"):
        return args[0] is None or isinstance(args[0], (list, tuple)) and not args[0]
    if name == "count":
        values = [] if args[0] is None else args[0] if isinstance(args[0], (list, tuple)) else [args[0]]
        if not all(isinstance(value, (N, ReportingQName, ReportingDate, str, bool)) for value in values):
            raise ExpressionError("TYPE_ERROR: explicit atomic sequence required")
        return N(len(values))
    if name == "leiChecksum":
        # Archived CFI intentionally passes malformed text: the rule must
        # check format separately. This is not LEI registration/validity.
        return lei_checksum(args[0])
    if name == "matches":
        return matches(*args)
    if name == "substring":
        positions = [_number(arg, False).value for arg in args[1:]]
        if any(value.denominator != 1 for value in positions):
            raise ExpressionError("UNSUPPORTED_ARGUMENT: integer substring positions required")
        return substring(args[0], *[int(value) for value in positions])
    if name in ("localName", "LocalName"):
        if not isinstance(args[0], ReportingQName):
            raise ExpressionError("TYPE_ERROR: explicit QName required")
        return args[0].local_name
    if name in _MARGINS:
        return custom_margin(_MARGINS[name], *[_number(arg).value for arg in args])
    interval = name.startswith("i")
    function = name[1:] if interval else name
    if function == "abs":
        return unary("abs", _number(args[0], interval))
    values = [_number(item, interval) for arg in args for item in _sequence(arg)]
    return aggregate(function, values)


def evaluate(text, resolver, *, namespaces=None, current_fact=None, dimensions=None):
    """Evaluate with a caller-supplied selector resolver, not a report validator.

    Bind numeric facts as ReportingNumber, known empty sequences as [], and
    explicit absent scalar facts as None. Text, bool, ReportingDate and ReportingQName are
    distinct atomic types. QName literals require source-bound namespaces.
    No implicit nil/default/number conversion. A missing binding raises KeyError.
    Ordinary arithmetic uses central values; only i-prefixed operations carry
    tolerance. Upstream scope/units/entity/date qualification is mandatory.
    Optional current_fact is (atomic_value, dimension_mapping) for a local
    filter. dimensions maps exact source selectors to externally qualified
    expanded-QName dimension mappings; missing entries are never defaults.
    """
    node = parse(text)
    if not callable(resolver):
        raise ExpressionError("INVALID_INPUT: explicit resolver required")
    try:
        # Resolve every literal, including inactive branches, against the
        # source-bound map. An unknown prefix is never an implicit URI guess.
        pending, qnames = [node], {}
        while pending:
            current = pending.pop()
            pending.extend(current.children)
            if current.kind == "qname":
                qnames[current.value] = expand_qname(current.value, namespaces)
        if dimensions is not None and not isinstance(dimensions, dict):
            raise ExpressionError("TYPE_ERROR: explicit dimension bindings required")
        if current_fact is not None and (not isinstance(current_fact, tuple) or len(current_fact) != 2):
            raise ExpressionError("TYPE_ERROR: explicit current fact context required")
        return _run(node, resolver, qnames, {"current_fact": current_fact, "dimensions": dimensions or {}})
    except ExpressionError:
        raise
    except (ValueError, ZeroDivisionError, TypeError, OverflowError) as error:
        raise ExpressionError("NUMERIC_OR_TYPE_ERROR: " + str(error)) from error
