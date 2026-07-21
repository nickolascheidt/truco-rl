from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.player import Player
    from truco.entities.team import Team


@dataclass
class PlayResult:
    round_winner: "Player | None" = None
    round_over: bool = False
    hand_winner: "Team | None" = None
    hand_over: bool = False
    next_player: "Player | None" = None
    round_number: int = 1
