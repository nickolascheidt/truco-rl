from truco.states.flor_state import FlorState
from truco.entities.team import Team
from truco.entities.player import Player


def _make_teams():
    p1 = Player(name="Alice")
    p2 = Player(name="Bob")
    t1 = Team(name="T1", players=[p1])
    t2 = Team(name="T2", players=[p2])
    return t1, t2


def test_initial_state():
    state = FlorState()
    assert state.who_declared is None
    assert state.both_declared is False
    assert state.contra_flor_pending is False
    assert state.over is False
    assert state.envido_cancelled is False
    assert state.waiting_for_response is False


def test_declare_first_team():
    state = FlorState()
    t1, _ = _make_teams()
    state.declare(t1)
    assert state.who_declared == t1
    assert state.envido_cancelled is True
    assert state.waiting_for_response is True
    assert state.both_declared is False


def test_declare_second_team_sets_both():
    state = FlorState()
    t1, t2 = _make_teams()
    state.declare(t1)
    state.declare(t2)
    assert state.both_declared is True
    assert state.waiting_for_response is False


def test_contra_flor_pending():
    state = FlorState()
    t1, t2 = _make_teams()
    state.declare(t1)
    state.contra_flor(t2)
    assert state.contra_flor_pending is True
    assert state.waiting_for_response is True


def test_close_ends_flor():
    state = FlorState()
    t1, t2 = _make_teams()
    state.declare(t1)
    state.close()
    assert state.over is True
    assert state.waiting_for_response is False
