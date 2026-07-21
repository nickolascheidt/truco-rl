import pytest
from truco.entities.round import Round
from truco.entities.player import Player
from truco.entities.card import Card
from truco.enums import Suit


def _make_players():
    return Player(name="Alice"), Player(name="Bob")


def _card(number, suit=Suit.ESPADAS):
    return Card(number=number, suit=suit)


def test_round_starts_empty():
    r = Round()
    assert r.plays == {}
    assert r.winner is None
    assert r.resolved is False


def test_register_play():
    r = Round()
    alice, _ = _make_players()
    card = _card(3)
    r.register_play(alice, card)
    assert r.plays[alice] == card


def test_register_play_duplicate_raises():
    r = Round()
    alice, _ = _make_players()
    r.register_play(alice, _card(3))
    with pytest.raises(RuntimeError):
        r.register_play(alice, _card(2))


def test_resolve_picks_higher_strength():
    r = Round()
    alice, bob = _make_players()
    r.register_play(alice, _card(3))   # strength 10
    r.register_play(bob, _card(2))     # strength 9
    winner = r.resolve()
    assert winner == alice
    assert r.winner == alice
    assert r.resolved is True


def test_resolve_tie_returns_none():
    r = Round()
    alice, bob = _make_players()
    r.register_play(alice, _card(3, Suit.COPAS))   # strength 10
    r.register_play(bob, _card(3, Suit.OUROS))     # strength 10
    winner = r.resolve()
    assert winner is None
    assert r.winner is None
    assert r.resolved is True


def test_resolve_requires_both_plays():
    r = Round()
    alice, _ = _make_players()
    r.register_play(alice, _card(3))
    with pytest.raises(RuntimeError):
        r.resolve()
