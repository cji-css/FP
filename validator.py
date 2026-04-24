import ast
from collections import Counter


def normalize_expression(expr):
    return expr.replace("x", "*").replace("X", "*").replace("×", "*")


def extract_numbers_from_ast(node):
    numbers = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant):
            if isinstance(child.value, bool):
                raise ValueError("Booleans are not allowed.")
            if isinstance(child.value, (int, float)):
                numbers.append(child.value)
            else:
                raise ValueError("Only numbers are allowed.")
        elif isinstance(child, ast.BinOp):
            if not isinstance(child.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                raise ValueError("Only +, -, *, / are allowed.")
        elif isinstance(child, ast.UnaryOp):
            raise ValueError("Unary + or - is not allowed.")
        elif isinstance(child, (ast.Name, ast.Call, ast.Attribute, ast.Subscript)):
            raise ValueError("Variables and functions are not allowed.")
    return numbers


def validate_expression(expr, hand_values):
    cleaned = normalize_expression(expr.strip())
    if not cleaned:
        return False, "Expression cannot be empty.", None

    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError:
        return False, "Invalid expression syntax.", None

    try:
        used_numbers = extract_numbers_from_ast(tree)
    except ValueError as error:
        return False, str(error), None

    if len(used_numbers) != len(hand_values):
        return False, f"Use exactly {len(hand_values)} numbers.", None

    if any(not float(value).is_integer() for value in used_numbers):
        return False, "Card values must be integers.", None

    if Counter(int(value) for value in used_numbers) != Counter(hand_values):
        return False, "Use each card value exactly once.", None

    try:
        result = eval(
            compile(tree, filename="<expr>", mode="eval"),
            {"__builtins__": {}},
            {},
        )
    except ZeroDivisionError:
        return False, "Division by zero is not allowed.", None
    except Exception:
        return False, "Could not evaluate expression.", None

    return True, "ok", float(result)

