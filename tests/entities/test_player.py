import pytest
from truco.entities.player import Player
from truco.entities.card import Card
from truco.enums import Suit


def _make_player_with_cards():
    player = Player(name="Alice")
    player.hand = [
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.OUROS),
        Card(number=1, suit=Suit.COPAS),
    ]
    return player


def test_player_has_name():
    player = Player(name="Alice")
    assert player.name == "Alice"


def test_player_hand_starts_empty():
    player = Player(name="Alice")
    assert player.hand == []


def test_play_card_removes_from_hand():
    player = _make_player_with_cards()
    card = player.hand[0]
    played = player.play_card(card)
    assert played == card
    assert card not in player.hand
    assert len(player.hand) == 2


def test_play_card_raises_if_not_in_hand():
    player = _make_player_with_cards()
    foreign_card = Card(number=2, suit=Suit.PAUS)
    with pytest.raises(ValueError):
        player.play_card(foreign_card)


def test_clear_hand_empties_hand():
    player = _make_player_with_cards()
    player.clear_hand()
    assert player.hand == []
