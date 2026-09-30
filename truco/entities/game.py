from __future__ import annotations
from truco.entities.deck import Deck
from truco.entities.hand import Hand
from truco.entities.bet_result import BetResult
from truco.entities.play_result import PlayResult
from truco.enums import BetType, BetResponse, FlorResponse, BetStatus


class Game:
    def __init__(self, team1, team2, points_to_win: int = 24) -> None:
        self.team1 = team1
        self.team2 = team2
        self.points_to_win = points_to_win
        self._deck = Deck()
        self.hand: Hand = None  # type: ignore
        self._mano_index = 0  # 0 = team1's player is mano first

    @property
    def _all_players(self):
        return [self.team1.players[0], self.team2.players[0]]

    @property
    def _mano_player(self):
        return self._all_players[self._mano_index]

    def start_hand(self) -> None:
        self._deck.initialize()
        self._deck.shuffle()
        for player in self._all_players:
            player.clear_hand()
            player.hand = self._deck.deal_hand()
        self.hand = Hand(mano_player=self._mano_player, players=self._all_players)
        self._mano_index = 1 - self._mano_index

    def _deal_to_players(self, cards1, cards2) -> None:
        """Inject specific hands (used in tests)."""
        p1, p2 = self._all_players
        p1.hand = list(cards1)
        p2.hand = list(cards2)
        self.hand = Hand(mano_player=p1, players=[p1, p2])

    def play_card(self, player, card) -> PlayResult:
        if self.check_game_over():
            raise RuntimeError("Game is already over")
        if player != self.hand.current_player:
            raise RuntimeError(f"It's not {player.name}'s turn")
        if self._has_pending_bet():
            raise RuntimeError("Cannot play card while a bet is pending")

        # Remove card from player's hand before registering play
        player.play_card(card)

        round_winner = self.hand.register_play(player, card, self._all_players)
        hand_over, hand_winner_team = self._check_hand_over()

        if hand_over and hand_winner_team:
            truco_val = self.hand.truco.current_value
            hand_winner_team.add_points(truco_val)

        next_player = self.hand.current_player if not hand_over else None

        return PlayResult(
            round_winner=round_winner,
            round_over=round_winner is not None,
            hand_winner=hand_winner_team if hand_over else None,
            hand_over=hand_over,
            next_player=next_player,
            round_number=len([r for r in self.hand.rounds if r.resolved]),
        )

    def _check_hand_over(self):
        resolved = [r for r in self.hand.rounds if r.resolved]
        if len(resolved) < 2:
            return False, None

        def p_to_team(p):
            if p is None:
                return None
            return self.team1 if p in self.team1.players else self.team2

        r1 = p_to_team(resolved[0].winner)
        r2 = p_to_team(resolved[1].winner)

        mano_team = p_to_team(self.hand.mano_player)

        if r1 is not None and r1 == r2:
            return True, r1                    # won 2 in a row
        if r1 is None and r2 is not None:
            return True, r2                    # tie r1 → win r2
        if r1 is not None and r2 is None:
            return True, r1                    # win r1 → tie r2
        if r1 is None and r2 is None:
            # tie r1 + tie r2 → r3 decides; all-3-tie → mano
            if len(resolved) >= 3:
                r3 = p_to_team(resolved[2].winner)
                return True, r3 if r3 is not None else mano_team
            return False, None                 # need r3
        # split (r1 != r2): r3 decides; r3 tie → r1 winner wins
        if len(resolved) >= 3:
            r3 = p_to_team(resolved[2].winner)
            return True, r3 if r3 is not None else r1
        return False, None                     # need r3

    def _has_pending_bet(self) -> bool:
        return (
            self.hand.truco.status == BetStatus.PENDING
            or self.hand.envido.status == BetStatus.PENDING
            or self.hand.flor.waiting_for_response
        )

    def _player_team(self, player):
        return self.team1 if player in self.team1.players else self.team2

    def _other_player(self, player):
        p1, p2 = self._all_players
        return p2 if player == p1 else p1

    def _other_team(self, team):
        return self.team2 if team == self.team1 else self.team1

    def can_ask_truco(self, player) -> bool:
        return self.hand.truco.can_ask(self._player_team(player))

    def ask_truco(self, player) -> BetResult:
        if self._has_pending_bet():
            raise RuntimeError("Cannot ask truco while another bet is pending")
        team = self._player_team(player)
        self.hand.truco.ask(team)
        return BetResult(
            bet_pending=True,
            hand_value=self.hand.truco.current_value,
            who_responds=self._other_player(player),
        )

    def respond_truco(self, player, response: BetResponse) -> BetResult:
        if response == BetResponse.ACCEPT:
            self.hand.truco.accept()
            return BetResult(bet_pending=False, hand_value=self.hand.truco.current_value)
        if response == BetResponse.REFUSE:
            self.hand.truco.refuse()
            asking_team = self.hand.truco.who_asked
            pts = self.hand.truco.value_if_refused
            asking_team.add_points(pts)
            return BetResult(
                bet_pending=False,
                hand_over=True,
                winner_team=asking_team,
                points_winner=pts,
            )
        # RAISE
        team = self._player_team(player)
        self.hand.truco.raise_bet(team)
        return BetResult(
            bet_pending=True,
            hand_value=self.hand.truco.current_value,
            who_responds=self._other_player(player),
        )

    def can_envido(self, player) -> bool:
        return self.hand.can_envido(player)

    def ask_envido(self, player, bet_type: BetType) -> BetResult:
        if not self.hand.can_envido(player):
            raise RuntimeError("Envido not available")
        if self.hand.truco.status == BetStatus.PENDING or self.hand.flor.waiting_for_response:
            raise RuntimeError("Cannot ask envido while another bet is pending")
        # Falta = the points the OTHER team still needs to win
        opponent_team = self._other_team(self._player_team(player))
        pts_needed = self.points_to_win - opponent_team.points
        self.hand.envido.ask(player, bet_type, points_to_win=pts_needed)
        return BetResult(bet_pending=True, who_responds=self._other_player(player))

    def respond_envido(self, player, response: BetResponse) -> BetResult:
        if response == BetResponse.ACCEPT:
            self.hand.envido.accept()
            p1, p2 = self._all_players
            v1 = self.hand.envido_value(p1)
            v2 = self.hand.envido_value(p2)
            mano_team = self._player_team(self.hand.mano_player)
            if v1 > v2:
                winner_team = self._player_team(p1)
                loser_team = self._player_team(p2)
            elif v2 > v1:
                winner_team = self._player_team(p2)
                loser_team = self._player_team(p1)
            else:
                winner_team = mano_team
                loser_team = self._other_team(mano_team)
            # Falta Envido: winner gets the loser's falta (what the LOSER still needs to win)
            if self.hand.envido.bet_type == BetType.FALTA_ENVIDO:
                pts = self.points_to_win - loser_team.points
            else:
                pts = self.hand.envido.value_accepted
            winner_team.add_points(pts)
            game_over = self.check_game_over()
            return BetResult(
                bet_pending=False, hand_over=game_over, game_over=game_over,
                winner_team=winner_team, points_winner=pts,
            )
        if response == BetResponse.REFUSE:
            self.hand.envido.refuse()
            asker = self.hand.envido.who_asked
            asking_team = self._player_team(asker)
            pts = self.hand.envido.value_if_refused
            asking_team.add_points(pts)
            game_over = self.check_game_over()
            return BetResult(
                bet_pending=False, hand_over=game_over, game_over=game_over,
                winner_team=asking_team, points_winner=pts,
            )
        raise RuntimeError("Use ask_envido to raise the envido bet")

    def can_flor(self, player) -> bool:
        return self.hand.can_flor(player)

    def declare_flor(self, player) -> BetResult:
        team = self._player_team(player)
        self.hand.flor.declare(team)
        return BetResult(bet_pending=True, who_responds=self._other_player(player))

    def respond_flor(self, player, response: FlorResponse) -> BetResult:
        if self.hand.flor.contra_flor_pending:
            return self._respond_flor_phase2(player, response)
        return self._respond_flor_phase1(player, response)

    def _respond_flor_phase1(self, player, response: FlorResponse) -> BetResult:
        declaring_team = self.hand.flor.who_declared
        responding_team = self._player_team(player)
        if response == FlorResponse.ME_ACHICO:
            # folder (responding team) gets 2; declarant gets 4
            self.hand.flor.close()
            declaring_team.add_points(4)
            responding_team.add_points(2)
            game_over = self.check_game_over()
            return BetResult(
                bet_pending=False, hand_over=game_over, game_over=game_over,
                winner_team=declaring_team, points_winner=4, points_loser=2,
            )
        if response == FlorResponse.CONTRA_FLOR:
            team = self._player_team(player)
            self.hand.flor.contra_flor(team)
            return BetResult(bet_pending=True, who_responds=self._other_player(player))
        raise RuntimeError("Only ME_ACHICO or CONTRA_FLOR are valid in the initial flor phase")

    def _respond_flor_phase2(self, player, response: FlorResponse) -> BetResult:
        # The original declarant is responding to ContraFlor
        declaring_team = self.hand.flor.who_declared
        contra_team = self._other_team(declaring_team)
        if response == FlorResponse.ME_ACHICO:
            # declarant folds: contra team gets 4, declarant gets 2
            self.hand.flor.close()
            contra_team.add_points(4)
            declaring_team.add_points(2)
            game_over = self.check_game_over()
            return BetResult(
                bet_pending=False, hand_over=game_over, game_over=game_over,
                winner_team=contra_team, points_winner=4, points_loser=2,
            )
        if response == FlorResponse.ACEITAR:
            # compare flores; winner gets 6
            return self._resolve_flor_confronto(6)
        if response == FlorResponse.CONTRA_FLOR_AL_RESTO:
            return self._resolve_flor_al_resto()
        raise RuntimeError("Invalid response for ContraFlor phase")

    def _resolve_flor_confronto(self, points: int) -> BetResult:
        p1, p2 = self._all_players
        v1 = self.hand.flor_value(p1) if Hand.has_flor(p1.hand) else -1
        v2 = self.hand.flor_value(p2) if Hand.has_flor(p2.hand) else -1
        mano_team = self._player_team(self.hand.mano_player)
        if v1 > v2:
            winner_team = self._player_team(p1)
        elif v2 > v1:
            winner_team = self._player_team(p2)
        else:
            winner_team = mano_team
        self.hand.flor.close()
        winner_team.add_points(points)
        game_over = self.check_game_over()
        return BetResult(
            bet_pending=False, hand_over=game_over, game_over=game_over,
            winner_team=winner_team, points_winner=points,
        )

    def _resolve_flor_al_resto(self) -> BetResult:
        p1, p2 = self._all_players
        v1 = self.hand.flor_value(p1) if Hand.has_flor(p1.hand) else -1
        v2 = self.hand.flor_value(p2) if Hand.has_flor(p2.hand) else -1
        mano_team = self._player_team(self.hand.mano_player)
        if v1 > v2:
            winner_team = self._player_team(p1)
            loser_team = self._player_team(p2)
        elif v2 > v1:
            winner_team = self._player_team(p2)
            loser_team = self._player_team(p1)
        else:
            winner_team = mano_team
            loser_team = self._other_team(mano_team)
        # Flor al Resto: winner gets the loser's falta (what the loser still needs to win)
        pts = self.points_to_win - loser_team.points
        self.hand.flor.close()
        winner_team.add_points(pts)
        game_over = self.check_game_over()
        return BetResult(
            bet_pending=False, hand_over=game_over, game_over=game_over,
            winner_team=winner_team, points_winner=pts,
        )

    def get_score(self) -> dict:
        return {self.team1: self.team1.points, self.team2: self.team2.points}

    def check_game_over(self) -> bool:
        return self.team1.points >= self.points_to_win or self.team2.points >= self.points_to_win

    def get_winner(self):
        """Returns winning team. If both crossed points_to_win in the same hand, higher score wins."""
        if not self.check_game_over():
            return None
        if self.team1.points >= self.points_to_win and self.team2.points >= self.points_to_win:
            return self.team1 if self.team1.points >= self.team2.points else self.team2
        return self.team1 if self.team1.points >= self.points_to_win else self.team2
