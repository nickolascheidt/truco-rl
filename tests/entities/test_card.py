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
