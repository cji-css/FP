import os
import shutil
from itertools import zip_longest

try:
    from .constants import RED_SUITS, SUIT_SYMBOLS
    from .deck import build_deck, hand_size_from_pick
    from .solver import solve_all_expressions
    from .validator import validate_expression
except ImportError:
    from constants import RED_SUITS, SUIT_SYMBOLS
    from deck import build_deck, hand_size_from_pick
    from solver import solve_all_expressions
    from validator import validate_expression


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def terminal_width():
    return shutil.get_terminal_size((100, 30)).columns


def centered(text):
    width = terminal_width()
    return text.center(width)


def horizontal_rule(char="═", tone=Color.DIM):
    return f"{tone}{char * min(96, terminal_width() - 2)}{Color.RESET}"


def panel(title, lines):
    content_width = max(len(title) + 2, *(len(line) for line in lines), 30)
    top = f"╔{'═' * (content_width + 2)}╗"
    mid = f"╠{'═' * (content_width + 2)}╣"
    bottom = f"╚{'═' * (content_width + 2)}╝"
    print(f"{Color.DIM}{top}{Color.RESET}")
    print(f"{Color.DIM}║{Color.RESET} {Color.BOLD}{title.ljust(content_width)}{Color.RESET} {Color.DIM}║{Color.RESET}")
    print(f"{Color.DIM}{mid}{Color.RESET}")
    for line in lines:
        print(f"{Color.DIM}║{Color.RESET} {line.ljust(content_width)} {Color.DIM}║{Color.RESET}")
    print(f"{Color.DIM}{bottom}{Color.RESET}")


def banner():
    title = f"{Color.BOLD}{Color.CYAN}♠ GAME 67 - TERMINAL ARENA ♥{Color.RESET}"
    print(horizontal_rule())
    print(centered(title))
    print(centered("Pick a number -> that becomes your target"))
    print(centered("Use each card exactly once with +, -, *, /"))
    print(horizontal_rule())


def card_block(card):
    rank = str(card["rank"])
    suit = card["suit"]
    symbol = SUIT_SYMBOLS[suit]
    value = card["value"]
    accent = Color.RED if suit in RED_SUITS else Color.BLUE
    colored_symbol = f"{accent}{symbol}{Color.RESET}"
    colored_rank = f"{accent}{rank}{Color.RESET}"
    colored_value = f"{Color.WHITE}{value}{Color.RESET}"

    inside = 13
    top_left = f"{colored_rank}".ljust(inside + len(accent) + len(Color.RESET))
    bottom_right = f"{colored_rank}".rjust(inside + len(accent) + len(Color.RESET))
    middle = colored_symbol.center(inside + len(accent) + len(Color.RESET))
    value_line = f"value:{colored_value}".center(inside + len(Color.WHITE) + len(Color.RESET))
    return [
        "┌───────────────┐",
        f"│ {top_left} │",
        f"│ {middle} │",
        f"│ {value_line} │",
        f"│ {bottom_right} │",
        "└───────────────┘",
    ]


def print_cards(cards):
    print(f"\n{Color.BOLD}{Color.WHITE}Your cards{Color.RESET}")
    blocks = [card_block(card) for card in cards]
    for row in zip_longest(*blocks, fillvalue=""):
        print("  ".join(row))


def print_help():
    panel(
        "Commands",
        [
            "Type an expression using every card value exactly once.",
            "`restart`  restart math attempts for current hand",
            "`show`     reveal all valid results for current hand",
            "`new`      draw a new hand",
            "`reset`    reset score and rounds",
            "`quit`     exit game",
        ],
    )


def draw_hand(deck, size):
    if len(deck) < size:
        deck[:] = build_deck()
    return [deck.pop() for _ in range(size)]


def prompt_number():
    while True:
        raw = input("\nPick a number (1-200), or type `quit`: ").strip().lower()
        if raw == "quit":
            return None
        try:
            number = int(raw)
        except ValueError:
            print(f"{Color.RED}Please enter a valid integer.{Color.RESET}")
            continue
        if 1 <= number <= 200:
            return number
        print(f"{Color.RED}Number must be between 1 and 200.{Color.RESET}")


def print_solutions(solutions, target):
    print(f"\n{Color.BOLD}{Color.MAGENTA}All valid solutions for target {target} ({len(solutions)}):{Color.RESET}")
    if not solutions:
        print(f"{Color.YELLOW}No solution found for this hand.{Color.RESET}")
        return
    for idx, expression in enumerate(solutions, start=1):
        print(f"{idx:>3}. {expression} = {target}")


def run():
    deck = build_deck()
    score = 0
    rounds = 0

    clear_screen()
    banner()
    print_help()

    while True:
        print(
            f"\n{Color.DIM}Round Meter -> Score: {Color.GREEN}{score}{Color.DIM} | "
            f"Rounds: {Color.CYAN}{rounds}{Color.RESET}"
        )
        picked = prompt_number()
        if picked is None:
            print(f"\n{Color.CYAN}Thanks for playing Game 67!{Color.RESET}")
            return

        target = picked
        size = hand_size_from_pick(picked)
        rounds += 1
        hand = draw_hand(deck, size)
        values = [card["value"] for card in hand]
        attempts = 0
        solved = False
        solutions_cache = None

        clear_screen()
        banner()
        panel(
            "Round Setup",
            [
                f"You picked: {picked}",
                f"Target number: {target}",
                f"Cards this round: {size}",
            ],
        )
        print_cards(hand)
        print_help()

        while True:
            raw = input(f"\n{Color.BOLD}{Color.WHITE}Expression > {Color.RESET}").strip()
            cmd = raw.lower()

            if cmd == "quit":
                print(f"\n{Color.CYAN}Thanks for playing Game 67!{Color.RESET}")
                return
            if cmd == "restart":
                attempts = 0
                solved = False
                print(f"{Color.BLUE}Math process restarted for current hand.{Color.RESET}")
                continue
            if cmd == "reset":
                score = 0
                rounds = 0
                print(f"{Color.BLUE}Game reset. Starting over.{Color.RESET}")
                break
            if cmd == "new":
                print(f"{Color.BLUE}Drawing a new hand...{Color.RESET}")
                break
            if cmd == "show":
                if solutions_cache is None:
                    print(f"{Color.DIM}Calculating all solutions...{Color.RESET}")
                    solutions_cache = solve_all_expressions(values, target=target)
                print_solutions(solutions_cache, target)
                if not solved:
                    print(f"{Color.YELLOW}Round ended after showing all results.{Color.RESET}")
                    break
                continue
            if not raw:
                print(f"{Color.RED}Please type an expression or command.{Color.RESET}")
                continue

            attempts += 1
            valid, message, result = validate_expression(raw, values)
            if not valid:
                print(f"{Color.RED}Invalid: {message}{Color.RESET}")
                continue

            if abs(result - target) < 1e-9:
                score += 1
                solved = True
                print(
                    f"{Color.GREEN}Correct! {raw} = {target}. "
                    "Type `show` to view all valid combinations, or `new` for next hand."
                    f"{Color.RESET}"
                )
                continue

            print(f"{Color.YELLOW}Result is {result:g}, not {target}. Try again.{Color.RESET}")

