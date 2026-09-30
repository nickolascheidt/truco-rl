"""
Integration smoke test: plays complete random games to catch logic bugs
that unit tests cannot detect in isolation.
"""
import random
import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetType, BetResponse, FlorResponse


def _make_game(seed=None):
    if seed is not None:
        random.seed(seed)
    alice = Player("Alice")
    bob = Player("Bob")
    t1 = Team("T1", [alice])
    t2 = Team("T2", [bob])
    return Game(t1, t2), alice, bob, t1, t2


def _play_random_game(seed):
    game, alice, bob, t1, t2 = _make_game(seed)
    max_hands = 50  # safety limit

    for hand_num in range(max_hands):
        game.start_hand()
        _play_random_hand(game, alice, bob)

        if game.check_game_over():
            winner = game.get_winner()
            loser = t2 if winner == t1 else t1
            assert winner is not None, f"seed={seed}: check_game_over True but get_winner returned None"
            assert winner.points >= game.points_to_win, (
                f"seed={seed}: winner {winner.name} has {winner.points} pts, needed {game.points_to_win}"
            )
            # Winner must have at least as many points as the loser
            assert winner.points >= loser.points, (
                f"seed={seed}: winner {winner.points} < loser {loser.points}"
            )
            return hand_num + 1

    raise AssertionError(f"seed={seed}: game did not finish in {max_hands} hands — possible infinite loop")


def _play_random_hand(game, alice, bob):
    """Play one hand to completion using random legal actions."""
    hand = game.hand
    players = [alice, bob]

    # --- Flor phase (obligatory if player has flor) ---
    for player in players:
        if game.can_flor(player):
            result = _handle_flor(game, player, alice, bob)
            if result and result.game_over:
                return
            if hand.flor.over:
                break

    if game.check_game_over():
        return

    # --- Envido phase (optional, random) ---
    for player in players:
        if game.can_envido(player) and random.random() < 0.5:
            result = _handle_envido(game, player, alice, bob)
            if result and result.game_over:
                return
            break  # one envido sequence per hand

    if game.check_game_over():
        return

    # --- Play cards until hand is over ---
    max_plays = 6
    for _ in range(max_plays):
        if hand.truco.status.value == "refused":
            break  # hand ended by truco refusal

        current = hand.current_player
        if not current.hand:
            break

        # Random truco ask (30% chance, only if legal)
        if game.can_ask_truco(current) and random.random() < 0.3:
            result = game.ask_truco(current)
            opponent = bob if current == alice else alice
            _handle_truco_response(game, opponent, alice, bob)
            if hand.truco.status.value == "refused":
                break

        if not current.hand:
            break

        card = random.choice(current.hand)
        result = game.play_card(current, card)

        # Validate invariants after every play
        _assert_play_result_valid(result, game)

        if result.hand_over:
            break


def _handle_flor(game, declarer, alice, bob):
    game.declare_flor(declarer)
    opponent = bob if declarer == alice else alice
    if game.can_flor(opponent):
        # Both have flor: opponent must respond
        response = random.choice([FlorResponse.ME_ACHICO, FlorResponse.CONTRA_FLOR])
        result = game.respond_flor(opponent, response)
        if not result.bet_pending:
            return result
        # Phase 2: declarer responds to contra_flor
        response2 = random.choice([FlorResponse.ME_ACHICO, FlorResponse.ACEITAR, FlorResponse.CONTRA_FLOR_AL_RESTO])
        return game.respond_flor(declarer, response2)
    else:
        # Opponent has no flor: must fold (ME_ACHICO)
        return game.respond_flor(opponent, FlorResponse.ME_ACHICO)


def _handle_envido(game, asker, alice, bob):
    bet_type = random.choice([BetType.ENVIDO, BetType.REAL_ENVIDO, BetType.FALTA_ENVIDO])
    game.ask_envido(asker, bet_type)
    opponent = bob if asker == alice else alice
    # Opponent can accept, refuse, or raise
    choices = [BetResponse.ACCEPT, BetResponse.REFUSE]
    # Raise only if the chain still allows a higher call
    raises = [b for b in (BetType.ENVIDO, BetType.REAL_ENVIDO, BetType.FALTA_ENVIDO)
              if game.hand.envido.can_raise(b)]
    if game.can_envido(opponent) and raises:
        choices.append(BetResponse.RAISE)
    response = random.choice(choices)
    if response == BetResponse.RAISE:
        raise_type = random.choice(raises)
        if game.can_envido(opponent):
            game.ask_envido(opponent, raise_type)
            # Original asker must now accept or refuse
            return game.respond_envido(asker, random.choice([BetResponse.ACCEPT, BetResponse.REFUSE]))
        else:
            return game.respond_envido(opponent, BetResponse.ACCEPT)
    else:
        return game.respond_envido(opponent, response)


def _handle_truco_response(game, responder, alice, bob):
    hand = game.hand
    choices = [BetResponse.ACCEPT, BetResponse.REFUSE]
    if game.can_ask_truco(responder):
        choices.append(BetResponse.RAISE)
    response = random.choice(choices)
    if response == BetResponse.RAISE:
        result = game.respond_truco(responder, BetResponse.RAISE)
        if result.bet_pending:
            original = bob if responder == alice else alice
            _handle_truco_response(game, original, alice, bob)
    else:
        game.respond_truco(responder, response)


def _assert_play_result_valid(result, game):
    hand = game.hand
    t1, t2 = game.team1, game.team2
    assert t1.points >= 0, f"t1 negative points: {t1.points}"
    assert t2.points >= 0, f"t2 negative points: {t2.points}"
    # Scores should never be astronomically wrong. Game ends immediately when a team
    # reaches points_to_win, so scores should never hugely exceed it (truco can add up to 4).
    max_possible = game.points_to_win + 4
    assert t1.points <= max_possible, f"t1 score looks impossible: {t1.points}"
    assert t2.points <= max_possible, f"t2 score looks impossible: {t2.points}"
    if result.hand_over:
        assert result.hand_winner is not None or hand.truco.status.value == "refused", \
            "hand_over=True but no winner and truco wasn't refused"


@pytest.mark.parametrize("seed", range(200))
def test_full_game_random(seed):
    """Play a complete game with random legal actions. Should never crash or loop."""
    hands_played = _play_random_game(seed)
    assert hands_played >= 1
