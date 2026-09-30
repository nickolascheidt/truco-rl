import numpy as np
import pytest

from truco.rl.actions import N_ACTIONS, TrucoAction as A
from truco.rl.env import TrucoEnv, RandomPolicy
from truco.rl.heuristic import HeuristicPolicy
from truco.rl.obs import OBS_DIM


def _obs(hand=(), envido=0, played_mine=(), played_opp=(), round_no=1):
    """Build an observation with only the fields the heuristic reads."""
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    for i, strength in enumerate(hand):
        obs[2 * i], obs[2 * i + 1] = 1.0, strength / 14
    for i, strength in played_mine:
        obs[6 + 2 * i], obs[7 + 2 * i] = 1.0, strength / 14
    for i, strength in played_opp:
        obs[12 + 2 * i], obs[13 + 2 * i] = 1.0, strength / 14
    obs[21] = round_no / 3
    obs[38] = envido / 33
    return obs


def _mask(*actions):
    mask = np.zeros(N_ACTIONS, dtype=bool)
    mask[list(actions)] = True
    return mask


def _act(obs, mask):
    return HeuristicPolicy().predict(obs, mask)[0]


def test_beats_opponent_card_with_the_cheapest_winner():
    obs = _obs(hand=(14, 9, 5), played_opp=[(0, 8)])
    assert _act(obs, _mask(A.PLAY_CARD_0, A.PLAY_CARD_1, A.PLAY_CARD_2)) == A.PLAY_CARD_1


def test_throws_the_weakest_card_when_it_cannot_win():
    obs = _obs(hand=(4, 2, 6), played_opp=[(0, 12)])
    assert _act(obs, _mask(A.PLAY_CARD_0, A.PLAY_CARD_1, A.PLAY_CARD_2)) == A.PLAY_CARD_1


def test_leads_with_the_strongest_card():
    obs = _obs(hand=(4, 10, 6))
    assert _act(obs, _mask(A.PLAY_CARD_0, A.PLAY_CARD_1, A.PLAY_CARD_2)) == A.PLAY_CARD_1


@pytest.mark.parametrize("envido, expected", [(33, A.ENVIDO), (20, A.PLAY_CARD_0)])
def test_calls_envido_only_with_a_good_score(envido, expected):
    obs = _obs(hand=(5, 4, 3), envido=envido)
    assert _act(obs, _mask(A.PLAY_CARD_0, A.PLAY_CARD_1, A.PLAY_CARD_2, A.ENVIDO)) == expected


@pytest.mark.parametrize("envido, expected", [(28, A.ENVIDO_ACCEPT), (21, A.ENVIDO_REFUSE)])
def test_answers_envido_by_score(envido, expected):
    obs = _obs(hand=(5, 5, 5), envido=envido)
    assert _act(obs, _mask(A.ENVIDO_ACCEPT, A.ENVIDO_REFUSE)) == expected


def test_refuses_truco_with_a_weak_hand():
    obs = _obs(hand=(1, 2, 3))
    assert _act(obs, _mask(A.TRUCO_ACCEPT, A.TRUCO_REFUSE, A.TRUCO_ASK_OR_RAISE)) == A.TRUCO_REFUSE


def test_only_picks_legal_actions_and_games_end():
    env = TrucoEnv(opponent_policy=HeuristicPolicy())
    policy = HeuristicPolicy()
    for _ in range(50):
        obs, _ = env.reset()
        for _ in range(300):
            mask = env.action_masks()
            action, _ = policy.predict(obs, mask)
            assert mask[action]
            obs, _, done, _, _ = env.step(action)
            if done:
                break
        else:
            pytest.fail("game did not finish")


def test_beats_a_random_player_most_of_the_time():
    env = TrucoEnv(opponent_policy=RandomPolicy())
    policy, wins, games = HeuristicPolicy(), 0, 300
    for _ in range(games):
        obs, _ = env.reset()
        while True:
            obs, reward, done, _, _ = env.step(policy.predict(obs, env.action_masks())[0])
            if done:
                wins += reward > 0
                break
    assert wins / games > 0.75
