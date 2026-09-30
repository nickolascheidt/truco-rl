from __future__ import annotations
import numpy as np

from truco.rl.actions import TrucoAction as A

# Thresholds on the envido score (0–33) and card strength (1–14), tuned by a
# small grid search against RandomPolicy.
_ENVIDO_ASK = 29
_ENVIDO_ACCEPT = 27
_ENVIDO_RAISE = 31
_TRUCO_STRONG_CARD = 12   # 7 of espadas or better
_TRUCO_ACCEPT_AVG = 6.0   # average strength of the cards still in hand


class HeuristicPolicy:
    """
    Rule-based opponent that reads the same observation the agent does.

    It plays the way a cautious beginner would: bets envido only with a good
    score, calls truco only with a strong card or a won round, and in each
    round plays the cheapest card that wins it. It is a stronger baseline
    than RandomPolicy, which accepts every bet it is offered.
    """

    def predict(self, obs: np.ndarray, action_masks: np.ndarray | None = None):
        mask = action_masks if action_masks is not None else np.ones(16, dtype=bool)
        return int(self._choose(obs, mask)), None

    def _choose(self, obs: np.ndarray, mask: np.ndarray) -> int:
        hand = [obs[2 * i + 1] * 14 for i in range(3) if obs[2 * i] > 0]
        envido = obs[38] * 33
        has_flor = obs[33] > 0
        rounds_won = int((obs[22:25] == 1).sum())
        rounds_lost = int((obs[22:25] == -1).sum())
        truco_strength = self._truco_strength(hand, rounds_won, rounds_lost)

        # Flor: always declare it, and answer a flor with contra-flor when possible.
        if mask[A.DECLARE_FLOR]:
            return A.DECLARE_FLOR
        if mask[A.FLOR_CONTRA_FLOR] and has_flor:
            return A.FLOR_CONTRA_FLOR
        if mask[A.FLOR_ACEITAR]:
            return A.FLOR_ACEITAR if envido >= _ENVIDO_ACCEPT else A.FLOR_ME_ACHICO
        if mask[A.FLOR_ME_ACHICO]:
            return A.FLOR_ME_ACHICO

        # Responding to envido.
        if mask[A.ENVIDO_ACCEPT]:
            if envido >= _ENVIDO_RAISE and mask[A.REAL_ENVIDO]:
                return A.REAL_ENVIDO
            return A.ENVIDO_ACCEPT if envido >= _ENVIDO_ACCEPT else A.ENVIDO_REFUSE

        # Responding to truco.
        if mask[A.TRUCO_ACCEPT]:
            if truco_strength >= _TRUCO_STRONG_CARD + 1 and mask[A.TRUCO_ASK_OR_RAISE]:
                return A.TRUCO_ASK_OR_RAISE
            return A.TRUCO_ACCEPT if truco_strength >= _TRUCO_ACCEPT_AVG else A.TRUCO_REFUSE

        # Own turn: bet first, then play a card.
        if mask[A.ENVIDO] and envido >= _ENVIDO_ASK:
            return A.ENVIDO
        if mask[A.TRUCO_ASK_OR_RAISE] and (
            max(hand, default=0) >= _TRUCO_STRONG_CARD or rounds_won > rounds_lost
        ):
            return A.TRUCO_ASK_OR_RAISE

        return self._play_card(obs, hand, mask)

    @staticmethod
    def _truco_strength(hand: list[float], won: int, lost: int) -> float:
        """Average strength of the cards in hand, shifted by the rounds already decided."""
        if not hand:
            return 0.0
        return sum(hand) / len(hand) + 3 * (won - lost)

    @staticmethod
    def _play_card(obs: np.ndarray, hand: list[float], mask: np.ndarray) -> int:
        playable = [i for i in range(len(hand)) if mask[A.PLAY_CARD_0 + i]]
        if not playable:
            return int(np.flatnonzero(mask)[0])

        # Opponent card on the table in the current round, if it already played.
        current = max(int(round(obs[21] * 3)) - 1, 0)
        opp_played = obs[12 + 2 * current] > 0 and obs[6 + 2 * current] == 0
        by_strength = sorted(playable, key=lambda i: hand[i])

        if opp_played:
            to_beat = obs[12 + 2 * current + 1] * 14
            winners = [i for i in by_strength if hand[i] > to_beat]
            # Cheapest card that wins; otherwise throw the weakest away.
            return A.PLAY_CARD_0 + (winners[0] if winners else by_strength[0])

        # Leading: open with the strongest card.
        return A.PLAY_CARD_0 + by_strength[-1]
