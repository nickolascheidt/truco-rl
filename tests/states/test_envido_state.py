import pytest
from truco.states.envido_state import EnvidoState
from truco.entities.player import Player
from truco.entities.card import Card
from truco.enums import BetStatus, BetType


def _make_players():
    return Player(name="Alice"), Player(name="Bob")


def test_initial_state():
    state = EnvidoState()
    assert state.value_accepted == 0
    assert state.value_if_refused == 0
    assert state.bet_type is None
    assert state.who_asked is None
    assert state.status == BetStatus.NONE


def test_ask_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.ENVIDO)
    assert state.status == BetStatus.PENDING
    assert state.who_asked == alice
    assert state.bet_type == BetType.ENVIDO
    assert state.value_accepted == 2
    assert state.value_if_refused == 1


def test_ask_real_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.REAL_ENVIDO)
    assert state.value_accepted == 3
    assert state.value_if_refused == 1


def test_accept_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.accept()
    assert state.status == BetStatus.ACCEPTED


def test_refuse_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.refuse()
    assert state.status == BetStatus.REFUSED


def test_raise_envido_to_envido_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.ENVIDO_ENVIDO)
    assert state.bet_type == BetType.ENVIDO_ENVIDO
    assert state.value_accepted == 4
    assert state.value_if_refused == 2


def test_raise_envido_to_real_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.REAL_ENVIDO)
    assert state.value_accepted == 5  # 2 (envido) + 3 (real envido)
    assert state.value_if_refused == 2


def test_real_envido_stacked_on_real_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.REAL_ENVIDO)
    state.ask(alice, BetType.REAL_ENVIDO)
    assert state.value_accepted == 8  # 2 + 3 + 3
    assert state.value_if_refused == 5


def test_falta_envido_value():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.FALTA_ENVIDO, points_to_win=15)
    assert state.value_accepted == 15
    assert state.value_if_refused == 1


def test_falta_envido_after_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.FALTA_ENVIDO, points_to_win=12)
    assert state.value_accepted == 12  # falta is total, not cumulative
    assert state.value_if_refused == 2  # previous envido value = what you lose by folding
