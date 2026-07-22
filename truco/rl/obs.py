from __future__ import annotations
import numpy as np
from truco.enums import BetStatus
from truco.entities.hand import Hand

# Observation layout (39 floats):
#   [0:6]   agent hand — 3 slots × [is_present, strength/14]
#   [6:12]  agent played cards per round — 3 slots × [is_present, strength/14]
#   [12:18] opponent played cards per round — 3 slots × [is_present, strength/14]
#   [18]    agent score / points_to_win
#   [19]    opponent score / points_to_win
#   [20]    i_am_mano (0 or 1)
#   [21]    round_number / 3
#   [22:25] round results — 3 values (1=won, -1=lost, 0=tie/unplayed)
#   [25]    truco current_value / 4
#   [26]    truco pending
#   [27]    truco i_must_respond
#   [28]    envido value_accepted / points_to_win
#   [29]    envido pending
#   [30]    envido i_must_respond
#   [31]    flor over
#   [32]    flor waiting_for_response
#   [33]    i_have_flor
#   [34]    envido_cancelled (flor declared this hand)
#   [35:38] initial hand envido_value per card (card 0,1,2) / 7
#   [38]    computed envido score / 33   (20 + top-2 same suit, or max single)

OBS_DIM = 39

# Max possible envido score: 20 + 7 + 6 = 33  (two highest same-suit values)
_MAX_ENVIDO = 33.0


def encode_obs(game, agent) -> np.ndarray:
    """Encode the game state from `agent`'s perspective into a float32 vector."""
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    hand = game.hand
    opp = game._other_player(agent)
    agent_team = game._player_team(agent)
    opp_team = game._other_team(agent_team)
    pts = game.points_to_win

    idx = 0

    # Agent's current hand (up to 3 cards)
    for i in range(3):
        if i < len(agent.hand):
            obs[idx] = 1.0
            obs[idx + 1] = agent.hand[i].strength / 14.0
        idx += 2

    # Cards played per round (agent then opponent), 3 round slots each
    for target in (agent, opp):
        for r in range(3):
            if r < len(hand.rounds):
                card = hand.rounds[r].plays.get(target)
                if card is not None:
                    obs[idx] = 1.0
                    obs[idx + 1] = card.strength / 14.0
            idx += 2

    # Scores
    obs[idx] = agent_team.points / pts
    obs[idx + 1] = opp_team.points / pts
    idx += 2

    # Mano
    obs[idx] = 1.0 if hand.mano_player == agent else 0.0
    idx += 1

    # Round number (1-indexed, normalized)
    obs[idx] = len(hand.rounds) / 3.0
    idx += 1

    # Round results (3 slots, regardless of how many have been played)
    for r in range(3):
        if r < len(hand.rounds) and hand.rounds[r].resolved:
            winner = hand.rounds[r].winner
            obs[idx] = 1.0 if winner == agent else (-1.0 if winner == opp else 0.0)
        idx += 1

    # Truco state
    obs[idx] = hand.truco.current_value / 4.0
    obs[idx + 1] = 1.0 if hand.truco.status == BetStatus.PENDING else 0.0
    i_must_respond_truco = (
        hand.truco.status == BetStatus.PENDING
        and hand.truco.who_asked != agent_team
    )
    obs[idx + 2] = 1.0 if i_must_respond_truco else 0.0
    idx += 3

    # Envido state
    obs[idx] = hand.envido.value_accepted / pts
    obs[idx + 1] = 1.0 if hand.envido.status == BetStatus.PENDING else 0.0
    i_must_respond_envido = (
        hand.envido.status == BetStatus.PENDING
        and hand.envido.who_asked != agent
    )
    obs[idx + 2] = 1.0 if i_must_respond_envido else 0.0
    idx += 3

    # Flor state
    obs[idx] = 1.0 if hand.flor.over else 0.0
    obs[idx + 1] = 1.0 if hand.flor.waiting_for_response else 0.0
    agent_initial = hand._initial_hands.get(agent, agent.hand)
    obs[idx + 2] = 1.0 if Hand.has_flor(agent_initial) else 0.0
    obs[idx + 3] = 1.0 if hand.flor.envido_cancelled else 0.0
    idx += 4

    # Envido features: individual card envido_values + computed total score
    for i in range(3):
        if i < len(agent_initial):
            obs[idx] = agent_initial[i].envido_value / 7.0
        idx += 1
    obs[idx] = hand.envido_value(agent) / _MAX_ENVIDO
    idx += 1

    assert idx == OBS_DIM, f"obs encoding mismatch: wrote {idx}, expected {OBS_DIM}"
    return obs
