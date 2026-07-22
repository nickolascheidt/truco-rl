import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    return Game(team1=t1, team2=t2), alice, bob, t1, t2


def test_start_hand_deals_three_cards_to_each_player():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert len(alice.hand) == 3
    assert len(bob.hand) == 3


def test_start_hand_gives_unique_cards():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    all_cards = set(alice.hand) | set(bob.hand)
    assert len(all_cards) == 6


def test_current_player_is_mano_at_start():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert game.hand.current_player == alice  # alice is mano first hand


def test_play_card_returns_play_result():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    card = alice.hand[0]
    result = game.play_card(alice, card)
    assert result.round_over is False
    assert result.hand_over is False
    assert result.next_player == bob


def test_play_card_wrong_player_raises():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    with pytest.raises(RuntimeError):
        game.play_card(bob, bob.hand[0])  # bob is not current player


def test_hand_ends_after_winner_determined():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    hand_over = False
    for _ in range(6):  # max 6 plays (3 rounds x 2 players)
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            hand_over = True
            break
    assert hand_over


def test_mano_alternates_between_hands():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    first_mano = game.hand.mano_player
    # finish the hand
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    game.start_hand()
    second_mano = game.hand.mano_player
    assert first_mano != second_mano


def test_can_ask_truco():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert game.can_ask_truco(alice) is True


def test_check_game_over_false_at_start():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert game.check_game_over() is False
