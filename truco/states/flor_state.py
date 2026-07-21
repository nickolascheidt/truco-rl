from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.team import Team


class FlorState:
    def __init__(self) -> None:
        self.who_declared: "Team | None" = None
        self.both_declared: bool = False
        self.contra_flor_pending: bool = False
        self.over: bool = False
        self.envido_cancelled: bool = False
        self._waiting: bool = False

    @property
    def waiting_for_response(self) -> bool:
        return self._waiting

    def declare(self, team: "Team") -> None:
        self.envido_cancelled = True
        if self.who_declared is None:
            self.who_declared = team
            self._waiting = True
        else:
            self.both_declared = True
            self._waiting = False

    def contra_flor(self, team: "Team") -> None:
        self.contra_flor_pending = True
        self._waiting = True

    def close(self) -> None:
        self.over = True
        self._waiting = False
