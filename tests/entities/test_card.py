from truco.enums import Suit, BetType, BetResponse, FlorResponse, BetStatus


def test_suit_values():
    assert Suit.ESPADAS.value == "espadas"
    assert Suit.OUROS.value == "ouros"
    assert Suit.COPAS.value == "copas"
    assert Suit.PAUS.value == "paus"


def test_bet_status_values():
    assert BetStatus.NONE.value == "none"
    assert BetStatus.PENDING.value == "pending"
    assert BetStatus.ACCEPTED.value == "accepted"
    assert BetStatus.REFUSED.value == "refused"


def test_bet_type_values():
    assert BetType.ENVIDO.value == "envido"
    assert BetType.ENVIDO_ENVIDO.value == "envido_envido"
    assert BetType.REAL_ENVIDO.value == "real_envido"
    assert BetType.FALTA_ENVIDO.value == "falta_envido"
    assert BetType.TRUCO.value == "truco"
    assert BetType.RETRUCO.value == "retruco"
    assert BetType.VALE_QUATRO.value == "vale_quatro"


def test_bet_response_values():
    assert BetResponse.ACCEPT.value == "accept"
    assert BetResponse.REFUSE.value == "refuse"
    assert BetResponse.RAISE.value == "raise"


def test_flor_response_values():
    assert FlorResponse.ACCEPT.value == "accept"
    assert FlorResponse.CONTRA_FLOR.value == "contra_flor"
    assert FlorResponse.CONTRA_FLOR_AL_RESTO.value == "contra_flor_al_resto"


from truco.entities.card import Card


def test_card_creation():
    card = Card(number=3, suit=Suit.ESPADAS)
    assert card.number == 3
    assert card.suit == Suit.ESPADAS


def test_manilha_is_strongest():
    manilha = Card(number=4, suit=Suit.ESPADAS)
    assert manilha.strength == 14


def test_seven_espadas():
    card = Card(number=7, suit=Suit.ESPADAS)
    assert card.strength == 13


def test_one_espadas():
    card = Card(number=1, suit=Suit.ESPADAS)
    assert card.strength == 12


def test_seven_ouros():
    card = Card(number=7, suit=Suit.OUROS)
    assert card.strength == 11


def test_three_any_suit():
    assert Card(number=3, suit=Suit.COPAS).strength == 10
    assert Card(number=3, suit=Suit.PAUS).strength == 10
    assert Card(number=3, suit=Suit.OUROS).strength == 10


def test_two_any_suit():
    assert Card(number=2, suit=Suit.ESPADAS).strength == 9


def test_one_not_espadas():
    assert Card(number=1, suit=Suit.COPAS).strength == 8
    assert Card(number=1, suit=Suit.OUROS).strength == 8
    assert Card(number=1, suit=Suit.PAUS).strength == 8


def test_figure_cards():
    assert Card(number=12, suit=Suit.ESPADAS).strength == 7
    assert Card(number=11, suit=Suit.ESPADAS).strength == 6
    assert Card(number=10, suit=Suit.ESPADAS).strength == 5


def test_seven_copas_paus():
    assert Card(number=7, suit=Suit.COPAS).strength == 4
    assert Card(number=7, suit=Suit.PAUS).strength == 4


def test_low_cards():
    assert Card(number=6, suit=Suit.ESPADAS).strength == 3
    assert Card(number=5, suit=Suit.ESPADAS).strength == 2
    assert Card(number=4, suit=Suit.COPAS).strength == 1


def test_envido_value_number_cards():
    assert Card(number=1, suit=Suit.ESPADAS).envido_value == 1
    assert Card(number=5, suit=Suit.COPAS).envido_value == 5
    assert Card(number=7, suit=Suit.OUROS).envido_value == 7


def test_envido_value_figure_cards():
    assert Card(number=10, suit=Suit.ESPADAS).envido_value == 0
    assert Card(number=11, suit=Suit.COPAS).envido_value == 0
    assert Card(number=12, suit=Suit.PAUS).envido_value == 0


def test_card_repr():
    card = Card(number=3, suit=Suit.ESPADAS)
    assert "3" in repr(card)
    assert "espadas" in repr(card).lower()
