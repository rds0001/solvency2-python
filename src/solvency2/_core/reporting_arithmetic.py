"""Exact central-value/tolerance arithmetic matching archived Eurofiling CFI.

Internal numeric component. This module does not select facts, evaluate DPM expressions,
infer filing duties or make missing facts equal zero. See the source contract.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction


def rational(value):
    """Convert a finite declared number with explicit operational size limits.

    Limits prevent huge declared exponents from allocating unbounded integers.
    These are technical support limits, not regulatory amount restrictions.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal, Fraction)):
        raise ValueError("Finite numeric value required")
    if isinstance(value, Fraction):
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > 100000:
            raise ValueError("TECHNICAL_LIMIT: reporting rational size")
        return value
    if isinstance(value, str) and len(value) > 10000:
        raise ValueError("TECHNICAL_LIMIT: reporting numeric text length")
    if isinstance(value, int) and value.bit_length() > 14000:
        raise ValueError("TECHNICAL_LIMIT: reporting integer size")
    try:
        decimal = Decimal(str(value))
        if not decimal.is_finite():
            raise ValueError("Finite numeric value required")
        parts = decimal.as_tuple()
        if len(parts.digits) > 4000 or abs(parts.exponent) > 4000:
            raise ValueError("TECHNICAL_LIMIT: reporting decimal digits/exponent")
        return Fraction(decimal)
    except InvalidOperation as error:
        raise ValueError("Finite numeric value required") from error


@dataclass(frozen=True)
class ReportingNumber:
    """A central value and symmetric tolerance, not generic interval arithmetic."""
    value: Fraction
    tolerance: Fraction = Fraction(0)

    def __post_init__(self):
        object.__setattr__(self, "value", rational(self.value))
        object.__setattr__(self, "tolerance", rational(self.tolerance))
        if self.tolerance < 0:
            raise ValueError("Tolerance must be nonnegative")

    @classmethod
    def reported(cls, value, decimals):
        if decimals == "INF":
            return cls(value)
        if isinstance(decimals, bool) or not isinstance(decimals, int):
            raise ValueError("Explicit integer decimals or INF required")
        if abs(decimals) > 1000:
            raise ValueError("Decimals outside technical support range [-1000,1000]")
        return cls(value, Fraction(10) ** (-decimals) / 2)

    @property
    def lower(self):
        return self.value - self.tolerance

    @property
    def upper(self):
        return self.value + self.tolerance


def binary(operation, left, right):
    if not isinstance(left, ReportingNumber) or not isinstance(right, ReportingNumber):
        raise ValueError("Explicit ReportingNumber operands required")
    a, b, ta, tb = left.value, right.value, left.tolerance, right.tolerance
    if operation == "add":
        return ReportingNumber(a + b, ta + tb)
    if operation == "subtract":
        return ReportingNumber(a - b, ta + tb)
    if operation == "multiply":
        return ReportingNumber(a * b, abs(a) * tb + abs(b) * ta + ta * tb)
    if operation == "divide":
        if right.lower <= 0 <= right.upper:
            raise ValueError("REVIEW_REQUIRED: denominator interval contains zero")
        central = a / b
        endpoints = [x / y for x in (left.lower, left.upper) for y in (right.lower, right.upper)]
        return ReportingNumber(central, max(abs(central - point) for point in endpoints))
    if operation == "equal":
        return abs(a - b) <= ta + tb
    if operation == "less":
        return a - b < ta + tb
    if operation == "less_equal":
        return a - b <= ta + tb
    if operation == "greater":
        return b - a < ta + tb
    if operation == "greater_equal":
        return b - a <= ta + tb
    raise ValueError("Unsupported arithmetic operation")


def unary(operation, operand):
    if not isinstance(operand, ReportingNumber):
        raise ValueError("Explicit ReportingNumber operand required")
    if operation == "abs":
        return ReportingNumber(abs(operand.value), operand.tolerance)
    if operation == "negate":
        return ReportingNumber(-operand.value, operand.tolerance)
    raise ValueError("Unsupported unary operation")


def custom_margin(operation, left, right, margin):
    """Compare central values with the rule's explicit nonnegative margin.

    Archived cmf:numeric-equal uses <=, including when a calling rule supplies
    abs(0.01 * rhs). No division by rhs or extra decimals tolerance is inferred.
    The rule evaluator must supply the actual margin expression's result.
    """
    if operation not in ("equal", "less", "less_equal", "greater", "greater_equal"):
        raise ValueError("Unsupported margin comparison")
    return binary(operation, ReportingNumber(left, margin), ReportingNumber(right))


def aggregate(operation, operands):
    if not isinstance(operands, (list, tuple)) or not all(isinstance(x, ReportingNumber) for x in operands):
        raise ValueError("Explicit sequence of ReportingNumber operands required")
    if operation not in ("sum", "min", "max", "multiply"):
        raise ValueError("Unsupported aggregate operation")
    if not operands:
        return ReportingNumber(0)
    if operation == "sum":
        return ReportingNumber(sum(x.value for x in operands), sum(x.tolerance for x in operands))
    if operation in ("min", "max"):
        select = min if operation == "min" else max
        return select(operands, key=lambda x: x.value)
    result = operands[0]
    for operand in operands[1:]:
        result = binary("multiply", result, operand)
    return result
