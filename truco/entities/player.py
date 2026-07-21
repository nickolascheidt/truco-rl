from __future__ import annotations
from truco.entities.card import Card


class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.hand: list[Card] = []

    def play_card(self, card: Card) -> Card:
        if card not in self.hand:
            raise ValueError(f"{card} not in {self.name}'s hand")
        self.hand.remove(card)
        return card

    def clear_hand(self) -> None:
        self.hand = []

    def __repr__(self) -> str:
        return f"Player({self.name})"
