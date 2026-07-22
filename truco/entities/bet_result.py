from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.team import Team
    from truco.entities.player import Player


@dataclass
class BetResult:
    bet_pending: bool = False
    hand_value: int = 1
    hand_over: bool = False
    winner_team: "Team | None" = None
    who_responds: "Player | None" = None
    points_winner: int = 0
    points_loser: int = 0
