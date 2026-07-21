import pytest
from truco.states.truco_state import TrucoState
from truco.entities.team import Team
from truco.entities.player import Player
from truco.enums import BetStatus


def _make_teams():
    p1 = Player(name="Alice")
    p2 = Player(name="Bob")
    t1 = Team(name="T1", players=[p1])
    t2 = Team(name="T2", players=[p2])
    return t1, t2


def test_initial_state():
    state = TrucoState()
    assert state.current_value == 1
    assert state.value_if_refused == 0
    assert state.who_asked is None
    assert state.status == BetStatus.NONE


def test_can_ask_initially():
    state = TrucoState()
    t1, t2 = _make_teams()
    assert state.can_ask(t1) is True


def test_ask_sets_pending():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    assert state.status == BetStatus.PENDING
    assert state.who_asked == t1
    assert state.current_value == 2
    assert state.value_if_refused == 1


def test_cannot_ask_while_pending():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    assert state.can_ask(t1) is False
    assert state.can_ask(t2) is False


def test_accept_clears_pending():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    assert state.status == BetStatus.ACCEPTED
    assert state.current_value == 2


def test_refuse_sets_refused():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.refuse()
    assert state.status == BetStatus.REFUSED


def test_raise_bet_after_accept():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    state.raise_bet(t2)
    assert state.status == BetStatus.PENDING
    assert state.current_value == 3
    assert state.value_if_refused == 2
    assert state.who_asked == t2


def test_raise_to_vale_quatro():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    state.raise_bet(t2)
    state.accept()
    state.raise_bet(t1)
    assert state.current_value == 4
    assert state.value_if_refused == 3


def test_cannot_raise_past_vale_quatro():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    state.raise_bet(t2)
    state.accept()
    state.raise_bet(t1)
    state.accept()
    assert state.can_ask(t2) is False


def test_same_team_cannot_ask_twice_in_a_row():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    assert state.can_ask(t1) is False
    assert state.can_ask(t2) is True
