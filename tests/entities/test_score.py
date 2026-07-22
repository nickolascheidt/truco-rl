from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetResponse


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    return Game(team1=t1, team2=t2), alice, bob, t1, t2


def test_winning_hand_without_bet_scores_one():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    total = t1.points + t2.points
    assert total == 1  # exactly 1 point for base hand (no truco bet)


def test_winning_hand_with_truco_bet_scores_two():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    game.ask_truco(alice)
    game.respond_truco(bob, BetResponse.ACCEPT)
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    total = t1.points + t2.points
    assert total == 2  # truco accepted = 2 points


def test_get_score_returns_both_teams():
    game, alice, bob, t1, t2 = _make_game()
    score = game.get_score()
    assert score[t1] == 0
    assert score[t2] == 0


def test_check_game_over_at_24():
    game, alice, bob, t1, t2 = _make_game()
    t1.points = 24
    assert game.check_game_over() is True


def test_game_not_over_below_24():
    game, alice, bob, t1, t2 = _make_game()
    t1.points = 15
    assert game.check_game_over() is False
