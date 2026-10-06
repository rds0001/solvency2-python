"""Separate LEI checks from the archived XBRL 2020-07-02 functions.

These are internal building blocks, not an identifier-registration service or
a combined validity decision. In particular, the original checksum functions
return True for malformed identifiers to avoid duplicating a format error.
No trimming, case conversion, prefix removal or live GLEIF query is performed.
"""


def lei_format(value):
    """Exact ASCII shape: eighteen uppercase alphanumerics and two digits."""
    if not isinstance(value, str):
        raise ValueError("TYPE_ERROR: LEI functions require explicit text")
    return (len(value) == 20
            and all("A" <= c <= "Z" or "0" <= c <= "9" for c in value[:18])
            and all("0" <= c <= "9" for c in value[18:]))


def lei_checksum(value):
    """Original validate-checksum contract, NOT combined LEI validity.

    Stream the expanded base-36 decimal digits modulo 97. This is equivalent
    to the original thirteen-digit recursion and keeps intermediates bounded
    for the later native R implementation as well.
    """
    if not lei_format(value):
        return True
    remainder = 0
    for character in value:
        number = ord(character) - (48 if character <= "9" else 55)
        multiplier = 10 if number < 10 else 100
        remainder = (remainder * multiplier + number) % 97
    return remainder == 1


def lei_checksum_digits(value):
    """Original separate invalid-check-digits test; malformed text passes."""
    return not lei_format(value) or value[-2:] not in ("00", "01", "99")
