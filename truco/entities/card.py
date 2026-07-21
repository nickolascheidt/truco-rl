from __future__ import annotations
from truco.enums import Suit


def _calc_strength(number: int, suit: Suit) -> int:
    if number == 4 and suit == Suit.ESPADAS:
        return 14
    if number == 7 and suit == Suit.ESPADAS:
        return 13
    if number == 1 and suit == Suit.ESPADAS:
        return 12
    if number == 7 and suit == Suit.OUROS:
        return 11
    if number == 3:
        return 10
    if number == 2:
        return 9
    if number == 1:
        return 8
    if number == 12:
        return 7
    if number == 11:
        return 6
    if number == 10:
        return 5
    if number == 7:
        return 4
    if number == 6:
        return 3
    if number == 5:
        return 2
    return 1  # number == 4, suit != ESPADAS


class Card:
    def __init__(self, number: int, suit: Suit) -> None:
        self.number = number
        self.suit = suit
        self.strength = _calc_strength(number, suit)
        self.envido_value = number if number <= 7 else 0

    def __repr__(self) -> str:
        return f"Card({self.number} de {self.suit.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.number == other.number and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.number, self.suit))
