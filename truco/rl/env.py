from __future__ import annotations
import numpy as np
import gymnasium
from gymnasium import spaces

from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetStatus

from truco.rl.actions import N_ACTIONS, compute_action_mask, apply_action
from truco.rl.obs import OBS_DIM, encode_obs

# Small shaping coefficient: proportional point-gain reward to guide envido/bet learning.
# Scale: winning 4 pts in a 24-pt game → 0.2 * 4/24 ≈ 0.033 (vs terminal ±1).
_SHAPING = 0.2


class RandomPolicy:
    """Baseline opponent: picks a uniformly random legal action."""

    def predict(self, obs: np.ndarray, action_masks: np.ndarray | None = None):
        if action_masks is not None:
            legal = np.where(action_masks)[0]
            if len(legal) > 0:
                return int(np.random.choice(legal)), None
        return int(np.random.randint(N_ACTIONS)), None


class TrucoEnv(gymnasium.Env):
    """
    Single-agent Gymnasium environment for 1v1 Truco Gaúcho.

    The agent always plays as 'Agent' (alice / team1).
    The opponent is resolved internally using `opponent_policy`.
    Observation: float32 vector of shape (OBS_DIM,).
    Action:      Discrete(N_ACTIONS) with action masking.
    Reward:      +1 game win / -1 game loss  +  small shaping on point changes.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, opponent_policy=None, render_mode: str | None = None):
        super().__init__()
        self.observation_space = spaces.Box(
            low=-1.0, high=2.0, shape=(OBS_DIM,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(N_ACTIONS)
        self._opponent_policy = opponent_policy or RandomPolicy()
        self.render_mode = render_mode

        self._agent: Player | None = None
        self._opp: Player | None = None
        self._game: Game | None = None
        self._game_over = False

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(self, seed: int | None = None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            np.random.seed(seed)

        alice = Player("Agent")
        bob = Player("Opponent")
        t1 = Team("T1", [alice])
        t2 = Team("T2", [bob])
        self._agent = alice
        self._opp = bob
        self._game = Game(t1, t2)
        self._game_over = False

        self._game.start_hand()
        self._run_opponent_moves()

        return self._obs(), {}

    def step(self, action: int):
        assert not self._game_over, "Call reset() before stepping after game over."

        agent_team = self._game._player_team(self._agent)
        opp_team = self._game._other_team(agent_team)
        pts_before = (agent_team.points, opp_team.points)

        result = apply_action(self._game, self._agent, int(action))

        if self._game.check_game_over():
            self._game_over = True
        elif getattr(result, "hand_over", False):
            self._start_new_hand()
        else:
            self._run_opponent_moves()

        # Shaped reward: small signal proportional to net point gain this step
        agent_gained = agent_team.points - pts_before[0]
        opp_gained = opp_team.points - pts_before[1]
        shaped = _SHAPING * (agent_gained - opp_gained) / self._game.points_to_win

        obs = self._obs()
        reward = self._reward() + shaped
        return obs, reward, self._game_over, False, {}

    def action_masks(self) -> np.ndarray:
        if self._game_over or self._game is None:
            return np.zeros(N_ACTIONS, dtype=bool)
        return compute_action_mask(self._game, self._agent)

    def render(self):
        if self.render_mode != "human":
            return
        g = self._game
        if g is None:
            return
        agent_team = g._player_team(self._agent)
        opp_team = g._other_team(agent_team)
        print(
            f"Score  Agent={agent_team.points}  Opp={opp_team.points}  "
            f"| Hand #{g.hand.round_number}  "
            f"| Agent cards: {self._agent.hand}"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _obs(self) -> np.ndarray:
        if self._game_over or self._game is None or self._game.hand is None:
            return np.zeros(OBS_DIM, dtype=np.float32)
        return encode_obs(self._game, self._agent)

    def _reward(self) -> float:
        if not self._game_over:
            return 0.0
        agent_team = self._game._player_team(self._agent)
        winner = self._game.get_winner()
        return 1.0 if winner == agent_team else -1.0

    def _current_actor(self) -> Player:
        """Return whichever player must act next given the current state."""
        hand = self._game.hand
        if hand.truco.status == BetStatus.PENDING:
            return self._game._other_player(hand.truco.who_asked.players[0])
        if hand.envido.status == BetStatus.PENDING:
            return self._game._other_player(hand.envido.who_asked)
        if hand.flor.waiting_for_response:
            declarer = hand.flor.who_declared.players[0]
            if hand.flor.contra_flor_pending:
                return declarer
            return self._game._other_player(declarer)
        return hand.current_player

    def _run_opponent_moves(self):
        """Drive the opponent until it's the agent's turn (or the game/hand ends)."""
        while True:
            if self._game.check_game_over():
                self._game_over = True
                return

            actor = self._current_actor()
            if actor == self._agent:
                return

            opp_mask = compute_action_mask(self._game, self._opp)
            if not opp_mask.any():
                return

            opp_obs = encode_obs(self._game, self._opp)
            opp_action, _ = self._opponent_policy.predict(opp_obs, action_masks=opp_mask)

            result = apply_action(self._game, self._opp, int(opp_action))

            if self._game.check_game_over():
                self._game_over = True
                return

            if getattr(result, "hand_over", False):
                self._start_new_hand()
                return

    def _start_new_hand(self):
        self._game.start_hand()
        self._run_opponent_moves()
