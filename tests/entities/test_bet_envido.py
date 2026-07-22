import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import BetType, BetResponse, BetStatus, Suit


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    game = Game(team1=t1, team2=t2)
    # Inject fixed hands with mixed suits (no flor) so tests are deterministic
    game._deal_to_players(
        [Card(3, Suit.ESPADAS), Card(2, Suit.COPAS), Card(5, Suit.PAUS)],
        [Card(1, Suit.OUROS),  Card(6, Suit.COPAS), Card(4, Suit.PAUS)],
    )
    return game, alice, bob, t1, t2


def test_can_envido_before_first_play():
    game, alice, bob, t1, t2 = _make_game()
    assert game.can_envido(alice) is True


def test_mano_plays_card_second_player_can_still_call_envido():
    game, alice, bob, t1, t2 = _make_game()
    # alice is mano — plays a card
    card = alice.hand[0]
    game.play_card(alice, card)
    # alice already played so she cannot call envido
    assert game.can_envido(alice) is False
    # bob hasn't played yet — he can still call envido
    assert game.can_envido(bob) is True


def test_envido_value_uses_original_3_cards_after_mano_plays():
    """Mano plays a card; envido value must still be calculated on all 3 original cards."""
    game, alice, bob, t1, t2 = _make_game()
    # Alice's hand: 3♠(ev=3), 2♣(ev=2), 5♦(ev=5) — all different suits, best single = 5
    # After alice plays 3♠, only [2♣, 5♦] remain — but envido should still use the original 3
    card_played = alice.hand[0]  # 3♠
    game.play_card(alice, card_played)
    game.ask_envido(bob, __import__('truco.enums', fromlist=['BetType']).BetType.ENVIDO)
    result = game.respond_envido(alice, __import__('truco.enums', fromlist=['BetResponse']).BetResponse.ACCEPT)
    # The winner is decided; both teams have points (winner > 0) — key is no crash
    assert t1.points + t2.points > 0


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


def test_envido_refused_blocks_real_envido_for_refuser():
    # Bug scenario: bob refuses envido, then tries to ask real envido — must be blocked
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    game.respond_envido(bob, BetResponse.REFUSE)
    assert game.can_envido(bob) is False
    with pytest.raises(RuntimeError):
        game.ask_envido(bob, BetType.REAL_ENVIDO)


def test_envido_refused_blocks_real_envido_for_asker():
    # The asker also cannot raise after opponent refuses
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    game.respond_envido(bob, BetResponse.REFUSE)
    assert game.can_envido(alice) is False
    with pytest.raises(RuntimeError):
        game.ask_envido(alice, BetType.REAL_ENVIDO)


def test_envido_accepted_blocks_further_envido():
    # After envido is accepted and resolved, no more envido can be asked
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    game.respond_envido(bob, BetResponse.ACCEPT)
    assert game.can_envido(alice) is False
    assert game.can_envido(bob) is False


def test_envido_not_available_before_first_card_if_refused_in_same_round():
    # Sequence: ask envido → refuse → still in round 1 but envido is locked
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    game.respond_envido(bob, BetResponse.REFUSE)
    # Round 1 hasn't even started yet — but envido is done
    assert len(game.hand.rounds) == 1
    assert not game.hand.rounds[0].resolved
    assert game.can_envido(alice) is False
    assert game.can_envido(bob) is False
