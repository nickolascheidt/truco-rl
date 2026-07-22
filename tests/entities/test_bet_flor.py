import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import Suit, FlorResponse


def _make_game_with_flor():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    game = Game(team1=t1, team2=t2)
    # Inject specific hands (all same suit = flor for alice)
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    bob_cards = [
        Card(number=2, suit=Suit.OUROS),
        Card(number=4, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    game._deal_to_players(alice_cards, bob_cards)
    return game, alice, bob, t1, t2


def test_can_flor_with_all_same_suit():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    assert game.can_flor(alice) is True
    assert game.can_flor(bob) is False


def test_declare_flor_cancels_envido():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    game.declare_flor(alice)
    assert game.can_envido(alice) is False
    assert game.can_envido(bob) is False


def test_respond_flor_me_achico_awards_points():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    game.declare_flor(alice)
    result = game.respond_flor(bob, FlorResponse.ME_ACHICO)
    assert t1.points == 4  # declarant gets 4 on opponent's me_achico
    assert t2.points == 2  # folder gets 2


def test_declare_flor_sets_waiting():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    result = game.declare_flor(alice)
    assert result.bet_pending is True
    assert result.who_responds == bob
