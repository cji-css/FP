from fractions import Fraction
from functools import lru_cache


def solve_all_expressions(values, target=24, limit=300):
    nums = tuple(sorted(Fraction(v, 1) for v in values))

    @lru_cache(maxsize=None)
    def recurse(state):
        if len(state) == 1:
            return {state[0]: {fraction_to_str(state[0])}}

        outcomes = {}
        state_list = list(state)
        for i in range(len(state_list)):
            for j in range(i + 1, len(state_list)):
                a = state_list[i]
                b = state_list[j]
                remaining = [state_list[k] for k in range(len(state_list)) if k not in (i, j)]
                for result_value, expression in combine_pair(a, b):
                    next_state = tuple(sorted(remaining + [result_value]))
                    child_map = recurse(next_state)
                    for child_value, child_expressions in child_map.items():
                        bucket = outcomes.setdefault(child_value, set())
                        for child_expression in child_expressions:
                            if expression in child_expression:
                                bucket.add(child_expression)
                            else:
                                bucket.add(
                                    child_expression.replace(
                                        fraction_to_str(result_value), f"({expression})", 1
                                    )
                                )
        return outcomes

    solved = recurse(nums)
    target_fraction = Fraction(target, 1)
    expressions = solved.get(target_fraction, set())
    cleaned = sorted({compact_expression(e) for e in expressions})
    return cleaned[:limit]


def combine_pair(a, b):
    a_text = fraction_to_str(a)
    b_text = fraction_to_str(b)
    results = [(a + b, f"{a_text}+{b_text}"), (a * b, f"{a_text}*{b_text}")]
    results.append((a - b, f"{a_text}-{b_text}"))
    results.append((b - a, f"{b_text}-{a_text}"))
    if b != 0:
        results.append((a / b, f"{a_text}/{b_text}"))
    if a != 0:
        results.append((b / a, f"{b_text}/{a_text}"))
    return results


def fraction_to_str(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def compact_expression(expression):
    return expression.replace("+-", "-")

