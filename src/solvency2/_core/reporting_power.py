"""Bounded source-compatible mfn:exp(base,1,2), NOT a general square root.

All 75 exp calls per archived DPM release use (1,2). Eurofiling math.xml
2.0.0 starts its digit search at 10^11 and performs 16 positions ending at
10^-4. It truncates, not rounds. The source resets the first step to zero
at roots >=10^12; that unsupported range is explicitly rejected here.
Do not use this technical reporting algorithm as a capital/SCR square root.
"""
from fractions import Fraction
from math import isqrt

from .reporting_arithmetic import ReportingNumber


def source_power(base, numerator, denominator):
    if not isinstance(base, ReportingNumber):
        raise ValueError("TYPE_ERROR: explicit reporting number required")
    if type(numerator) is not int or type(denominator) is not int or (numerator, denominator) != (1, 2):
        raise ValueError("UNSUPPORTED_ARGUMENT: only archived exponent (1,2) supported")
    value = base.value
    if value < 0 or value >= 10**24:
        raise ValueError("UNSUPPORTED_RANGE: source root requires 0 <= base < 10^24")
    # floor(sqrt(x)*10^4) = isqrt(floor(x*10^8)) for nonnegative x.
    # Central value only: the archived mfn function is not interval arithmetic.
    scaled = value * 10**8
    integer = scaled.numerator // scaled.denominator
    return ReportingNumber(Fraction(isqrt(integer), 10000))
