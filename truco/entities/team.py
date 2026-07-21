from __future__ import annotations
from truco.entities.player import Player


class Team:
    def __init__(self, name: str, players: list[Player]) -> None:
        self.name = name
        self.players = players
        self.points = 0

    def add_points(self, value: int) -> None:
        if value <= 0:
            raise ValueError(f"Points must be positive, got {value}")
        self.points += value

    def __repr__(self) -> str:
        return f"Team({self.name}, {self.points}pts)"
