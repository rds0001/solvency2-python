r"""Bounded XPath 2 string components, not a general XPath/regex processor.

Local W3C F&O 2.0 sections 7.4.3/7.6 and XML Schema 2 appendix F govern
the supported grammar. Substring accepts integer positions only. Regex has
no flags, backreferences, category/name escapes or class subtraction. Unknown
constructs fail explicitly. A finite-state simulation avoids backtracking.
Unicode decimal digits use the host Unicode database (category Nd); \s is
exactly XML whitespace, not the host's broader whitespace definition.
"""
import unicodedata

MAX_STATES = 4096
MAX_STEPS = 2_000_000


def _text(value):
    if value is None or isinstance(value, (list, tuple)) and len(value) == 0:
        return ""
    if not isinstance(value, str):
        raise ValueError("TYPE_ERROR: explicit single text or empty sequence required")
    if len(value) > 100000:
        raise ValueError("TECHNICAL_LIMIT: text length")
    if any(not (c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF
                or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF) for c in value):
        raise ValueError("UNSUPPORTED_INPUT: non-XML character")
    return value


def substring(value, start, length=None):
    """One-based XPath positions, restricted to exact integer arguments.

    Fractional/double/NaN/infinite position semantics are not approximated.
    Negative starts clip after computing the endpoint, never before.
    """
    value = _text(value)
    if type(start) is not int or length is not None and type(length) is not int:
        raise ValueError("UNSUPPORTED_ARGUMENT: integer substring positions required")
    if abs(start) > 2**53 or length is not None and abs(length) > 2**53:
        raise ValueError("TECHNICAL_LIMIT: exactly representable double integer required")
    begin = max(0, min(len(value), start - 1))
    end = len(value) if length is None else max(0, min(len(value), start + length - 1))
    return value[begin:end]


class _Pattern:
    def __init__(self, text):
        if not isinstance(text, str) or len(text) > 10000:
            raise ValueError("TECHNICAL_LIMIT_OR_TYPE_ERROR: regex pattern")
        _text(text)
        if text.startswith(("one of options as per ", "ISO 8601 ", "yyyy-mm-dd pattern")):
            raise ValueError("UNSUPPORTED_PATTERN: descriptive standard reference is not a regex")
        self.text, self.position, self.depth = text, 0, 0

    def peek(self):
        return self.text[self.position:self.position + 1]

    def take(self):
        result = self.peek()
        if not result:
            raise ValueError("INVALID_PATTERN: unexpected end")
        self.position += 1
        return result

    def expression(self):
        self.depth += 1
        if self.depth > 50:
            raise ValueError("TECHNICAL_LIMIT: regex nesting")
        branches = []
        while True:
            pieces = []
            while self.peek() and self.peek() not in "|)":
                atom = self.atom()
                token = self.peek()
                if token and token in "?*+{":
                    self.take()
                    if token == "{":
                        lower = self.quantity()
                        upper = lower
                        if self.peek() == ",":
                            self.take()
                            upper = None if self.peek() == "}" else self.quantity()
                        if self.take() != "}" or upper is not None and upper < lower:
                            raise ValueError("INVALID_PATTERN: repetition range")
                    else:
                        lower, upper = {"?": (0, 1), "*": (0, None), "+": (1, None)}[token]
                    if self.peek() == "?":
                        self.take()  # Greediness does not affect boolean matches.
                    atom = ("repeat", atom, lower, upper)
                pieces.append(atom)
            branches.append(("sequence", pieces))
            if self.peek() != "|":
                break
            self.take()
        self.depth -= 1
        return ("choice", branches)

    def quantity(self):
        start = self.position
        while self.peek() and "0" <= self.peek() <= "9":
            self.take()
        digits = self.text[start:self.position]
        if not digits:
            raise ValueError("INVALID_PATTERN: missing repetition quantity")
        if len(digits) > 4 or int(digits) > 1000:
            raise ValueError("TECHNICAL_LIMIT: regex repetition")
        return int(digits)

    def escaped(self):
        char = self.take()
        if char in "nrt":
            return ("literal", {"n": "\n", "r": "\r", "t": "\t"}[char])
        if char in "\\|.?*+(){}-[]^$":
            return ("literal", char)
        if char in "sSdD":
            return ("escape", char)
        raise ValueError("UNSUPPORTED_PATTERN: escape or backreference")

    def atom(self):
        char = self.take()
        if char == "(":
            result = self.expression()
            if self.take() != ")":
                raise ValueError("INVALID_PATTERN: unclosed group")
            return result
        if char == "[":
            return self.character_class()
        if char == "\\":
            return ("character", self.escaped())
        if char in "^$":
            return ("anchor", char)
        if char == ".":
            return ("character", ("dot",))
        if char in "?*+{}])":
            raise ValueError("INVALID_PATTERN: unexpected metacharacter")
        return ("character", ("literal", char))

    def class_item(self):
        char = self.take()
        if char == "\\":
            return self.escaped()
        if char in "[]":
            raise ValueError("UNSUPPORTED_PATTERN: nested or unclosed character class")
        return ("literal", char)

    def character_class(self):
        negative = self.peek() == "^"
        if negative:
            self.take()
        items = []
        while self.peek() != "]":
            escaped = self.peek() == "\\"
            item = self.class_item()
            if not escaped and item == ("literal", "-") and items and self.peek() != "]":
                raise ValueError("INVALID_PATTERN: interior hyphen")
            if self.peek() == "-" and self.text[self.position + 1:self.position + 2] != "]":
                self.take()
                end = self.class_item()
                if item[0] != "literal" or end[0] != "literal" or item[1] > end[1]:
                    raise ValueError("INVALID_PATTERN: character range")
                item = ("range", item[1], end[1])
            items.append(item)
        self.take()
        if not items:
            raise ValueError("INVALID_PATTERN: empty character class")
        return ("character", ("class", negative, tuple(items)))


def _accepts(predicate, char):
    kind = predicate[0]
    if kind == "literal":
        return char == predicate[1]
    if kind == "range":
        return predicate[1] <= char <= predicate[2]
    if kind == "dot":
        return char != "\n"  # F&O 7.6.1.1, absent s flag.
    if kind == "escape":
        escape = predicate[1]
        found = char in " \t\n\r" if escape.lower() == "s" else unicodedata.category(char) == "Nd"
        return not found if escape.isupper() else found
    if kind == "class":
        found = any(_accepts(item, char) for item in predicate[2])
        return not found if predicate[1] else found
    raise ValueError("UNSUPPORTED_PATTERN: predicate")


def compile_pattern(pattern):
    """Compile only the documented finite-state subset; no host regex engine."""
    parser = _Pattern(pattern)
    tree = parser.expression()
    if parser.peek():
        raise ValueError("INVALID_PATTERN: trailing input")
    states = []

    def state():
        if len(states) >= MAX_STATES:
            raise ValueError("TECHNICAL_LIMIT: regex states")
        states.append([])
        return len(states) - 1

    def edge(start, end, kind="empty", value=None):
        states[start].append((kind, value, end))

    def build(node, start, end):
        kind = node[0]
        if kind in ("character", "anchor"):
            edge(start, end, kind, node[1])
        elif kind == "choice":
            for child in node[1]:
                branch_start, branch_end = state(), state()
                edge(start, branch_start)
                build(child, branch_start, branch_end)
                edge(branch_end, end)
        elif kind == "sequence":
            current = start
            for child in node[1]:
                following = state()
                build(child, current, following)
                current = following
            edge(current, end)
        elif kind == "repeat":
            child, lower, upper = node[1:]
            current = start
            for _ in range(lower):
                following = state()
                build(child, current, following)
                current = following
            if upper is None:
                edge(current, end)
                following = state()
                build(child, current, following)
                edge(following, current)
            else:
                for _ in range(upper - lower):
                    edge(current, end)
                    following = state()
                    build(child, current, following)
                    current = following
                edge(current, end)
        else:
            raise ValueError("UNSUPPORTED_PATTERN: node")

    start, end = state(), state()
    build(tree, start, end)
    return states, start, end


def matches(value, pattern):
    """Unanchored existential match; anchors apply only where actually written."""
    value = _text(value)
    states, start, end = compile_pattern(pattern)
    active, steps = set(), 0
    for position in range(len(value) + 1):
        pending, closure = list(active | {start}), set()
        while pending:
            index = pending.pop()
            if index in closure:
                continue
            closure.add(index)
            for kind, predicate, target in states[index]:
                steps += 1
                if steps > MAX_STEPS:
                    raise ValueError("TECHNICAL_LIMIT: regex transitions")
                if kind == "empty" or kind == "anchor" and (
                    predicate == "^" and position == 0 or predicate == "$" and position == len(value)
                ):
                    pending.append(target)
        if end in closure:
            return True
        active = set()
        if position < len(value):
            for index in closure:
                for kind, predicate, target in states[index]:
                    steps += 1 + (len(predicate[2]) if kind == "character" and predicate[0] == "class" else 0)
                    if steps > MAX_STEPS:
                        raise ValueError("TECHNICAL_LIMIT: regex transitions")
                    if kind == "character" and _accepts(predicate, value[position]):
                        active.add(target)
    return False
