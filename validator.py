import re
from collections import Counter


def normalize_expression(expr):
    return expr.replace("x", "*").replace("X", "*").replace("×", "*")


def _compact(expr):
    return "".join(expr.split())


def validate_expression(expr, hand_values):
    cleaned = normalize_expression(expr.strip())
    if not cleaned:
        return False, "Expression cannot be empty.", None

    no_space = _compact(cleaned)
    allowed = set("0123456789+-*/()")
    if any(c not in allowed for c in no_space):
        return False, "Only digits and +, -, *, /, parentheses are allowed.", None

    if "**" in no_space or "//" in no_space:
        return False, "Only +, -, *, / are allowed.", None

    depth = 0
    for c in no_space:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                return False, "Unbalanced parentheses.", None
    if depth != 0:
        return False, "Unbalanced parentheses.", None

    literals = re.findall(r"\d+", no_space)
    if len(literals) != len(hand_values):
        return False, f"Use exactly {len(hand_values)} numbers.", None

    used_ints = [int(s) for s in literals]
    if Counter(used_ints) != Counter(hand_values):
        return False, "Use each card value exactly once.", None

    try:
        code = compile(no_space, "<expr>", "eval")
    except SyntaxError:
        return False, "Invalid expression syntax.", None

    try:
        result = eval(code, {"__builtins__": {}}, {})
    except ZeroDivisionError:
        return False, "Division by zero is not allowed.", None
    except Exception:
        return False, "Could not evaluate expression.", None

    if not isinstance(result, (int, float)):
        return False, "Expression must evaluate to a number.", None

    return True, "ok", float(result)
