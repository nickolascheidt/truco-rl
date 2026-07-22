import pytest
from truco.entities.hand import Hand
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import Suit


def _setup():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    alice.hand = [
        Card(number=3, suit=Suit.ESPADAS),   # strength 10
        Card(number=2, suit=Suit.COPAS),      # strength 9
        Card(number=5, suit=Suit.PAUS),       # strength 2
    ]
    bob.hand = [
        Card(number=1, suit=Suit.COPAS),      # strength 8
        Card(number=6, suit=Suit.OUROS),      # strength 3
        Card(number=4, suit=Suit.PAUS),       # strength 1
    ]
    hand = Hand(mano_player=alice, players=[alice, bob])
    return hand, alice, bob, t1, t2


def test_hand_starts_at_round_one():
    hand, alice, bob, t1, t2 = _setup()
    assert hand.round_number == 1
    assert hand.current_player == alice


def test_register_play_advances_to_next_player():
    hand, alice, bob, t1, t2 = _setup()
    card = alice.hand[0]
    hand.register_play(alice, card, [alice, bob])
    assert hand.current_player == bob


def test_round_resolves_after_two_plays():
    hand, alice, bob, t1, t2 = _setup()
    # Alice plays 3♠ (str 10), Bob plays 1♥ (str 8) → Alice wins round 1
    hand.register_play(alice, alice.hand[0], [alice, bob])
    round_winner = hand.register_play(bob, bob.hand[0], [alice, bob])
    assert round_winner == alice
    assert hand.round_number == 2


def test_hand_winner_after_two_rounds_won():
    hand, alice, bob, t1, t2 = _setup()
    teams = [t1, t2]
    # Round 1: Alice plays 3♠ (10) beats Bob's 1♥ (8)
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    # Round 2: Alice plays 2♥ (9) beats Bob's 6♦ (3)
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    result = hand.resolve(teams)
    assert result == t1


def test_mano_wins_on_triple_tie():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    card_a = Card(number=3, suit=Suit.ESPADAS)   # strength 10
    card_b = Card(number=3, suit=Suit.COPAS)     # strength 10
    alice.hand = [card_a]
    bob.hand = [card_b]
    hand = Hand(mano_player=alice, players=[alice, bob])
    # Round 1 tie
    hand.register_play(alice, card_a, [alice, bob])
    hand.register_play(bob, card_b, [alice, bob])
    # After r1+r2 tie, resolve should be undecided (None)
    assert hand.resolve([t1, t2]) is None
    # Round 2 tie (same cards, different Round object)
    hand.register_play(alice, card_a, [alice, bob])
    hand.register_play(bob, card_b, [alice, bob])
    assert hand.resolve([t1, t2]) is None
    # Round 3 tie → mano wins (all three tied)
    hand.register_play(alice, card_a, [alice, bob])
    hand.register_play(bob, card_b, [alice, bob])
    result = hand.resolve([t1, t2])
    assert result == t1  # mano (alice) wins when all three tie


def test_double_tie_r3_decides():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    card_tie_a = Card(number=3, suit=Suit.ESPADAS)   # str 10
    card_tie_b = Card(number=3, suit=Suit.COPAS)     # str 10
    card_win_a = Card(number=2, suit=Suit.ESPADAS)   # str 9
    card_lose_b = Card(number=1, suit=Suit.COPAS)    # str 8
    alice.hand = [card_tie_a, card_win_a]
    bob.hand = [card_tie_b, card_lose_b]
    hand = Hand(mano_player=alice, players=[alice, bob])
    # R1 tie
    hand.register_play(alice, card_tie_a, [alice, bob])
    hand.register_play(bob, card_tie_b, [alice, bob])
    # R2 tie
    hand.register_play(alice, card_tie_a, [alice, bob])
    hand.register_play(bob, card_tie_b, [alice, bob])
    assert hand.resolve([t1, t2]) is None  # undecided
    # R3 alice wins
    hand.register_play(alice, card_win_a, [alice, bob])
    hand.register_play(bob, card_lose_b, [alice, bob])
    result = hand.resolve([t1, t2])
    assert result == t1


def test_split_r3_tie_r1_winner_wins():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    card_win_a = Card(number=3, suit=Suit.ESPADAS)   # str 10 → alice wins r1
    card_lose_b = Card(number=1, suit=Suit.COPAS)    # str 8
    card_win_b = Card(number=3, suit=Suit.OUROS)     # str 10 → bob wins r2 (alice played weaker)
    card_lose_a = Card(number=2, suit=Suit.COPAS)    # str 9
    card_tie_a = Card(number=5, suit=Suit.ESPADAS)   # str 2
    card_tie_b = Card(number=5, suit=Suit.COPAS)     # str 2 → tie r3
    alice.hand = [card_win_a, card_lose_a, card_tie_a]
    bob.hand = [card_lose_b, card_win_b, card_tie_b]
    hand = Hand(mano_player=alice, players=[alice, bob])
    # R1: alice wins
    hand.register_play(alice, card_win_a, [alice, bob])
    hand.register_play(bob, card_lose_b, [alice, bob])
    # R2: bob wins
    hand.register_play(alice, card_lose_a, [alice, bob])
    hand.register_play(bob, card_win_b, [alice, bob])
    assert hand.resolve([t1, t2]) is None  # split, need r3
    # R3: tie → r1 winner (alice/t1) wins
    hand.register_play(alice, card_tie_a, [alice, bob])
    hand.register_play(bob, card_tie_b, [alice, bob])
    result = hand.resolve([t1, t2])
    assert result == t1  # alice won r1, r3 tied → alice wins


def test_win_round1_tie_round2_wins_hand():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    alice.hand = [
        Card(number=3, suit=Suit.ESPADAS),  # str 10 - wins r1
        Card(number=2, suit=Suit.ESPADAS),  # str 9 - ties r2
        Card(number=5, suit=Suit.ESPADAS),
    ]
    bob.hand = [
        Card(number=1, suit=Suit.COPAS),   # str 8 - loses r1
        Card(number=2, suit=Suit.COPAS),   # str 9 - ties r2
        Card(number=5, suit=Suit.COPAS),
    ]
    hand = Hand(mano_player=alice, players=[alice, bob])
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    result = hand.resolve([t1, t2])
    assert result == t1
