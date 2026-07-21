from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.player import Player
    from truco.entities.card import Card


class Round:
    def __init__(self) -> None:
        self.plays: dict["Player", "Card"] = {}
        self.winner: "Player | None" = None
        self.resolved: bool = False

    def register_play(self, player: "Player", card: "Card") -> None:
        if player in self.plays:
            raise RuntimeError(f"{player} already played this round")
        self.plays[player] = card

    def resolve(self) -> "Player | None":
        if len(self.plays) < 2:
            raise RuntimeError("Cannot resolve round with fewer than 2 plays")
        self.resolved = True
        players = list(self.plays.keys())
        cards = [self.plays[p] for p in players]
        if cards[0].strength > cards[1].strength:
            self.winner = players[0]
        elif cards[1].strength > cards[0].strength:
            self.winner = players[1]
        else:
            self.winner = None
        return self.winner
