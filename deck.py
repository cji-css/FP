import random

try:
    from .constants import RANK_VALUES, SUITS
except ImportError:
    from constants import RANK_VALUES, SUITS


def build_deck():
    deck = []
    for suit in SUITS:
        for rank, value in RANK_VALUES.items():
            deck.append({"rank": rank, "suit": suit, "value": value})
    random.shuffle(deck)
    return deck


def hand_size_from_pick(number_pick):
    # Interpreting "67(2)" as 67*2 = 134.
    if number_pick <= 67:
        return 4
    if number_pick <= 134:
        return 5
    return 6

