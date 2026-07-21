from truco.entities.hand import Hand
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import Suit


def _setup_hand(alice_cards, bob_cards, mano="alice"):
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    alice.hand = alice_cards
    bob.hand = bob_cards
    mano_player = alice if mano == "alice" else bob
    hand = Hand(mano_player=mano_player, players=[alice, bob])
    return hand, alice, bob


def test_can_envido_at_start():
    alice_cards = [
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
        Card(number=1, suit=Suit.COPAS),
    ]
    bob_cards = [
        Card(number=2, suit=Suit.OUROS),
        Card(number=4, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    hand, alice, bob = _setup_hand(alice_cards, bob_cards)
    assert hand.can_envido(alice) is True
    assert hand.can_envido(bob) is True


def test_envido_value_two_same_suit():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=6, suit=Suit.ESPADAS),   # envido 6
        Card(number=1, suit=Suit.COPAS),     # envido 1 (different suit)
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.envido_value(alice) == 33  # 20 + 7 + 6


def test_envido_value_no_pair_returns_highest():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=6, suit=Suit.OUROS),     # envido 6
        Card(number=5, suit=Suit.COPAS),     # envido 5
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.envido_value(alice) == 7  # just highest individual


def test_envido_value_figure_counts_zero():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=10, suit=Suit.ESPADAS),  # envido 0
        Card(number=1, suit=Suit.COPAS),
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.envido_value(alice) == 27  # 20 + 7 + 0


def test_has_flor_all_same_suit():
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    assert Hand.has_flor(alice_cards) is True


def test_has_flor_false_mixed_suits():
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.OUROS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    assert Hand.has_flor(alice_cards) is False


def test_can_flor_with_all_same_suit():
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
    hand, alice, bob = _setup_hand(alice_cards, bob_cards)
    assert hand.can_flor(alice) is True
    assert hand.can_flor(bob) is False


def test_flor_value():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=6, suit=Suit.ESPADAS),   # envido 6
        Card(number=1, suit=Suit.ESPADAS),   # envido 1
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.flor_value(alice) == 34  # 20 + 7 + 6 + 1


def test_can_envido_false_when_flor():
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
    hand, alice, bob = _setup_hand(alice_cards, bob_cards)
    # Player with flor cannot envido
    assert hand.can_envido(alice) is False
    assert hand.can_envido(bob) is True
