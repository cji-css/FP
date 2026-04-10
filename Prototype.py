import ast
import random
from collections import Counter


TARGET = 24
HAND_SIZE = 4
RANK_VALUES = {
    "A": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
}
SUITS = ("Hearts", "Diamonds", "Clubs", "Spades")


def build_deck():
    deck = []
    for suit in SUITS:
        for rank, value in RANK_VALUES.items():
            deck.append((f"{rank} of {suit}", value))
    random.shuffle(deck)
    return deck


def draw_hand(deck):
    if len(deck) < HAND_SIZE:
        deck[:] = build_deck()
        print("\nDeck was low. A new shuffled deck has been created.")
    return [deck.pop() for _ in range(HAND_SIZE)]


def normalize_expression(expr):
    return expr.replace("x", "*").replace("X", "*").replace("×", "*")


def get_numbers_from_ast(node):
    numbers = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant):
            if isinstance(child.value, (int, float)):
                if isinstance(child.value, bool):
                    raise ValueError("Booleans are not allowed.")
                numbers.append(child.value)
            else:
                raise ValueError("Only numbers are allowed in the expression.")
        elif isinstance(child, ast.BinOp):
            if not isinstance(child.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                raise ValueError("Only +, -, *, / operators are allowed.")
        elif isinstance(child, ast.UnaryOp):
            # Disallow unary operators so each card maps directly to a number.
            raise ValueError("Unary + or - is not allowed.")
        elif isinstance(child, ast.Name):
            raise ValueError("Variables are not allowed.")
        elif isinstance(child, ast.Call):
            raise ValueError("Function calls are not allowed.")
    return numbers


def validate_and_eval(expr, hand_values):
    cleaned = normalize_expression(expr.strip())
    if not cleaned:
        return False, "Expression cannot be empty.", None

    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError:
        return False, "Invalid expression syntax.", None

    try:
        used_numbers = get_numbers_from_ast(tree)
    except ValueError as exc:
        return False, str(exc), None

    if len(used_numbers) != HAND_SIZE:
        return (
            False,
            f"You must use exactly {HAND_SIZE} numbers from your cards.",
            None,
        )

    if any(not float(n).is_integer() for n in used_numbers):
        return False, "Only integer card values are allowed.", None

    used_counter = Counter(int(n) for n in used_numbers)
    hand_counter = Counter(hand_values)
    if used_counter != hand_counter:
        return False, "You must use each card value exactly once.", None

    try:
        result = eval(compile(tree, filename="<expr>", mode="eval"), {"__builtins__": {}}, {})
    except ZeroDivisionError:
        return False, "Division by zero is not allowed.", None
    except Exception:
        return False, "Could not evaluate expression.", None

    return True, "OK", float(result)


def format_hand(hand):
    card_names = [card[0] for card in hand]
    values = [card[1] for card in hand]
    cards_line = " | ".join(card_names)
    values_line = " ".join(str(v) for v in values)
    return cards_line, values_line


def play_round(deck):
    hand = draw_hand(deck)
    hand_values = [card[1] for card in hand]
    cards_line, values_line = format_hand(hand)

    print("\nYour cards:")
    print(cards_line)
    print(f"Values: {values_line}")
    print(f"Goal: make {TARGET} using +, -, *, / and each value once.")
    print("You can type 'x' for multiplication, and parentheses are allowed.")
    print("Enter 'skip' to get a new hand, or 'quit' to end the game.")

    while True:
        user_input = input("\nExpression: ").strip()
        lowered = user_input.lower()

        if lowered == "quit":
            return "quit"
        if lowered == "skip":
            print("Skipping this hand.")
            return "next"

        valid, message, result = validate_and_eval(user_input, hand_values)
        if not valid:
            print(f"Invalid: {message}")
            continue

        if abs(result - TARGET) < 1e-9:
            print(f"Nice! {user_input} = 24. You solved this hand.")
            return "next"

        print(f"Close, but {user_input} = {result:g}, not {TARGET}. Try again.")


def main():
    print("Welcome to 24 (Terminal Edition)!")
    print("You'll receive 4 cards from a standard 52-card deck (no jokers).")
    print("Face cards are valued as: J=11, Q=12, K=13, and A=1.")
    print("Use each card value exactly once to make 24.")

    deck = build_deck()

    while True:
        action = play_round(deck)
        if action == "quit":
            print("\nThanks for playing 24. Goodbye!")
            break


if __name__ == "__main__":
    main()


