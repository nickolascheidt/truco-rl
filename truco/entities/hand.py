from __future__ import annotations
from collections import defaultdict
from typing import TYPE_CHECKING
from truco.entities.round import Round
from truco.states.truco_state import TrucoState
from truco.states.envido_state import EnvidoState
from truco.states.flor_state import FlorState
from truco.enums import BetStatus

if TYPE_CHECKING:
    from truco.entities.player import Player
    from truco.entities.team import Team
    from truco.entities.card import Card


class Hand:
    def __init__(self, mano_player: "Player", players: list["Player"]) -> None:
        self.mano_player = mano_player
        self.players = players
        self.current_player: "Player" = mano_player
        self.rounds: list[Round] = [Round()]
        self.truco = TrucoState()
        self.envido = EnvidoState()
        self.flor = FlorState()
        # Snapshot hands at deal time so envido is calculated on 3 cards even after one is played
        self._initial_hands: dict["Player", list["Card"]] = {p: list(p.hand) for p in players}

    @property
    def round_number(self) -> int:
        return len(self.rounds)

    @property
    def _current_round(self) -> Round:
        return self.rounds[-1]

    def register_play(self, player: "Player", card: "Card", all_players: list["Player"]) -> "Player | None":
        self._current_round.register_play(player, card)
        if len(self._current_round.plays) == 2:
            winner = self._current_round.resolve()
            self._advance_round(winner)
            return winner
        self._set_next_player(all_players)
        return None

    def _set_next_player(self, all_players: list["Player"]) -> None:
        idx = all_players.index(self.current_player)
        self.current_player = all_players[(idx + 1) % len(all_players)]

    def _advance_round(self, round_winner: "Player | None") -> None:
        if round_winner is not None:
            self.current_player = round_winner
        else:
            self.current_player = self.mano_player
        if len(self.rounds) < 3:
            self.rounds.append(Round())

    def resolve(self, teams: list["Team"]) -> "Team | None":
        winners = [r.winner for r in self.rounds if r.resolved]

        def player_team(p: "Player | None") -> "Team | None":
            if p is None:
                return None
            for t in teams:
                if p in t.players:
                    return t
            return None

        round_teams = [player_team(w) for w in winners]
        mano_team = player_team(self.mano_player)

        if len(round_teams) >= 2:
            r1, r2 = round_teams[0], round_teams[1]
            if r1 is not None and r1 == r2:
                return r1                    # won 2 in a row
            if r1 is None and r2 is not None:
                return r2                    # tie r1 → win r2
            if r1 is not None and r2 is None:
                return r1                    # win r1 → tie r2
            if r1 is None and r2 is None:
                # tie r1 + tie r2 → r3 decides; all-3-tie → mano
                if len(round_teams) >= 3:
                    r3 = round_teams[2]
                    return r3 if r3 is not None else mano_team
                return None                  # undecided, need r3
            # split (r1 != r2): r3 decides; r3 tie → r1 winner wins
            if len(round_teams) >= 3:
                r3 = round_teams[2]
                return r3 if r3 is not None else r1
            return None                      # undecided, need r3
        if len(round_teams) == 1 and round_teams[0] is not None:
            return round_teams[0]
        return None

    def _no_cards_played(self) -> bool:
        return len(self.rounds) == 1 and len(self.rounds[0].plays) == 0

    def can_envido(self, player: "Player") -> bool:
        initial = self._initial_hands.get(player, player.hand)
        if Hand.has_flor(initial):
            return False
        if self.flor.envido_cancelled:
            return False
        if self.envido.status in (BetStatus.REFUSED, BetStatus.ACCEPTED):
            return False
        # Envido is valid in round 1 as long as the requesting player hasn't played yet.
        # The mano is allowed to play a card first; the second player can still call envido.
        in_round_one = len(self.rounds) == 1 and not self.rounds[0].resolved
        player_hasnt_played = player not in self.rounds[0].plays
        return in_round_one and player_hasnt_played

    def can_flor(self, player: "Player") -> bool:
        initial = self._initial_hands.get(player, player.hand)
        if not Hand.has_flor(initial):
            return False
        if self.flor.over:
            return False
        return self._no_cards_played()

    def envido_value(self, player: "Player") -> int:
        cards = self._initial_hands.get(player, player.hand)
        by_suit: dict = defaultdict(list)
        for c in cards:
            by_suit[c.suit].append(c.envido_value)
        for suit_vals in by_suit.values():
            if len(suit_vals) >= 2:
                top2 = sorted(suit_vals, reverse=True)[:2]
                return 20 + sum(top2)
        return max(c.envido_value for c in cards)

    def flor_value(self, player: "Player") -> int:
        cards = self._initial_hands.get(player, player.hand)
        return 20 + sum(c.envido_value for c in cards)

    @staticmethod
    def has_flor(cards: list["Card"]) -> bool:
        if len(cards) != 3:
            return False
        return len({c.suit for c in cards}) == 1
