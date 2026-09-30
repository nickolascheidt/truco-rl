from __future__ import annotations
from typing import TYPE_CHECKING
from truco.enums import BetStatus, BetType

if TYPE_CHECKING:
    from truco.entities.player import Player

# Position of each call in the raise chain; a raise may never go down.
_RANK = {
    BetType.ENVIDO: 0,
    BetType.ENVIDO_ENVIDO: 0,
    BetType.REAL_ENVIDO: 1,
    BetType.FALTA_ENVIDO: 2,
}


class EnvidoState:
    def __init__(self) -> None:
        self.value_accepted: int = 0
        self.value_if_refused: int = 0
        self.bet_type: BetType | None = None
        self.who_asked: "Player | None" = None
        self.status: BetStatus = BetStatus.NONE
        self.chain: list[BetType] = []

    def can_raise(self, bet_type: BetType) -> bool:
        """
        Whether `bet_type` may be called now. The chain only goes up:
        Envido at most twice, then Real Envido once, then Falta Envido, which ends it.
        """
        if bet_type not in _RANK:
            return False
        if not self.chain:
            return True
        if _RANK[bet_type] < _RANK[self.chain[-1]]:
            return False
        if _RANK[bet_type] == 0:
            return sum(_RANK[b] == 0 for b in self.chain) < 2
        return bet_type not in self.chain

    def ask(self, player: "Player", bet_type: BetType, points_to_win: int = 0) -> None:
        if not self.can_raise(bet_type):
            chain = ", ".join(b.value for b in self.chain)
            raise RuntimeError(f"{bet_type.value} cannot follow [{chain}]")
        self.chain.append(bet_type)
        prev_accepted = self.value_accepted

        # Envido and Real Envido add to what is already on the table; Falta Envido
        # replaces it with the points the opponent still needs to win.
        # Refusing costs the value on the table before this call (1 if nothing was).
        if bet_type == BetType.FALTA_ENVIDO:
            new_accepted = points_to_win
        elif bet_type == BetType.REAL_ENVIDO:
            new_accepted = prev_accepted + 3
        else:  # ENVIDO or ENVIDO_ENVIDO
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
