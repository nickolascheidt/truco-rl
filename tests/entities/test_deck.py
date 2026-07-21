from truco.entities.deck import Deck
from truco.enums import Suit


def test_deck_initializes_with_40_cards():
    deck = Deck()
    deck.initialize()
    assert len(deck.cards) == 40


def test_deck_has_valid_numbers_only():
    deck = Deck()
    deck.initialize()
    valid = {1, 2, 3, 4, 5, 6, 7, 10, 11, 12}
    for card in deck.cards:
        assert card.number in valid


def test_deck_has_all_suits():
    deck = Deck()
    deck.initialize()
    suits = {card.suit for card in deck.cards}
    assert suits == {Suit.ESPADAS, Suit.OUROS, Suit.COPAS, Suit.PAUS}


def test_deck_has_unique_cards():
    deck = Deck()
    deck.initialize()
    pairs = [(c.number, c.suit) for c in deck.cards]
    assert len(pairs) == len(set(pairs))


def test_deal_hand_returns_three_cards():
    deck = Deck()
    deck.initialize()
    hand = deck.deal_hand()
    assert len(hand) == 3


def test_deal_hand_removes_cards_from_deck():
    deck = Deck()
    deck.initialize()
    deck.deal_hand()
    assert len(deck.cards) == 37


def test_two_deal_hands_have_no_overlap():
    deck = Deck()
    deck.initialize()
    hand1 = deck.deal_hand()
    hand2 = deck.deal_hand()
    assert set(hand1).isdisjoint(set(hand2))


def test_shuffle_changes_order():
    import random
    random.seed(42)
    deck = Deck()
    deck.initialize()
    original = list(deck.cards)
    deck.shuffle()
    assert deck.cards != original


def test_initialize_resets_deck():
    deck = Deck()
    deck.initialize()
    deck.deal_hand()
    assert len(deck.cards) == 37
    deck.initialize()
    assert len(deck.cards) == 40
