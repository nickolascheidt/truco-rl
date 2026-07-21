from __future__ import annotations
from typing import TYPE_CHECKING
from truco.enums import BetStatus

if TYPE_CHECKING:
    from truco.entities.team import Team


class TrucoState:
    def __init__(self) -> None:
        self.current_value: int = 1
        self.value_if_refused: int = 0
        self.who_asked: "Team | None" = None
        self.status: BetStatus = BetStatus.NONE

    def can_ask(self, team: "Team") -> bool:
        if self.status == BetStatus.PENDING:
            return False
        if self.current_value >= 4:
            return False
        if self.who_asked == team and self.status == BetStatus.ACCEPTED:
            return False
        return True

    def ask(self, team: "Team") -> None:
        next_value = self.current_value + 1
        self.value_if_refused = self.current_value if self.current_value > 1 else 1
        self.current_value = next_value
        self.who_asked = team
        self.status = BetStatus.PENDING

    def accept(self) -> None:
        self.status = BetStatus.ACCEPTED

    def refuse(self) -> None:
        self.status = BetStatus.REFUSED

    def raise_bet(self, team: "Team") -> None:
        self.ask(team)
