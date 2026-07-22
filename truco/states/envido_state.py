from __future__ import annotations
from typing import TYPE_CHECKING
from truco.enums import BetStatus, BetType

if TYPE_CHECKING:
    from truco.entities.player import Player


class EnvidoState:
    def __init__(self) -> None:
        self.value_accepted: int = 0
        self.value_if_refused: int = 0
        self.bet_type: BetType | None = None
        self.who_asked: "Player | None" = None
        self.status: BetStatus = BetStatus.NONE

    def ask(self, player: "Player", bet_type: BetType, points_to_win: int = 0) -> None:
        prev_accepted = self.value_accepted

        # Accepted value is NOT cumulative for REAL_ENVIDO/FALTA_ENVIDO:
        # the winner always gets the declared total, not prev + increment.
        # Refused value IS the previous pending value (what you lose by folding).
        if bet_type == BetType.FALTA_ENVIDO:
            new_accepted = points_to_win
        elif bet_type == BetType.REAL_ENVIDO:
            new_accepted = prev_accepted + 3
        elif bet_type == BetType.ENVIDO_ENVIDO:
            new_accepted = prev_accepted + 2
        else:  # ENVIDO
            new_accepted = prev_accepted + 2

        self.value_accepted = new_accepted
        self.value_if_refused = prev_accepted if prev_accepted > 0 else 1
        self.bet_type = bet_type
        self.who_asked = player
        self.status = BetStatus.PENDING

    def accept(self) -> None:
        self.status = BetStatus.ACCEPTED

    def refuse(self) -> None:
        self.status = BetStatus.REFUSED
