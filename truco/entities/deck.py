from __future__ import annotations
import random
from truco.enums import Suit
from truco.entities.card import Card

VALID_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]


class Deck:
    def __init__(self) -> None:
        self.cards: list[Card] = []

    def initialize(self) -> None:
        self.cards = [
            Card(number=n, suit=s)
            for s in Suit
            for n in VALID_NUMBERS
        ]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal_hand(self) -> list[Card]:
        hand = self.cards[:3]
        self.cards = self.cards[3:]
        return hand
