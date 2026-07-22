import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetType, BetResponse, BetStatus


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    game = Game(team1=t1, team2=t2)
    game.start_hand()
    return game, alice, bob, t1, t2


def test_can_envido_before_first_play():
    game, alice, bob, t1, t2 = _make_game()
    assert game.can_envido(alice) is True


def test_ask_envido_returns_pending_result():
    game, alice, bob, t1, t2 = _make_game()
    result = game.ask_envido(alice, BetType.ENVIDO)
    assert result.bet_pending is True
    assert result.who_responds == bob


def test_respond_envido_accept_resolves():
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    result = game.respond_envido(bob, BetResponse.ACCEPT)
    assert result.bet_pending is False
    assert result.hand_over is False  # play continues after envido


def test_respond_envido_refuse_awards_points():
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    result = game.respond_envido(bob, BetResponse.REFUSE)
    assert result.bet_pending is False
    assert t1.points == 1  # refused envido = 1 point to asker


def test_envido_not_available_after_first_round():
    game, alice, bob, t1, t2 = _make_game()
    # Play first round completely
    game.play_card(alice, alice.hand[0])
    game.play_card(bob, bob.hand[0])
    # Now in round 2 (or hand over), envido not available
    assert game.can_envido(alice) is False


def test_ask_envido_raises_when_not_available():
    game, alice, bob, t1, t2 = _make_game()
    game.play_card(alice, alice.hand[0])
    game.play_card(bob, bob.hand[0])
    with pytest.raises(RuntimeError):
        game.ask_envido(alice, BetType.ENVIDO)
