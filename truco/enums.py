from enum import Enum


class Suit(Enum):
    ESPADAS = "espadas"
    OUROS = "ouros"
    COPAS = "copas"
    PAUS = "paus"


class BetType(Enum):
    ENVIDO = "envido"
    ENVIDO_ENVIDO = "envido_envido"
    REAL_ENVIDO = "real_envido"
    FALTA_ENVIDO = "falta_envido"
    TRUCO = "truco"
    RETRUCO = "retruco"
    VALE_QUATRO = "vale_quatro"


class BetResponse(Enum):
    ACCEPT = "accept"
    REFUSE = "refuse"
    RAISE = "raise"


class FlorResponse(Enum):
    ACCEPT = "accept"
    CONTRA_FLOR = "contra_flor"
    CONTRA_FLOR_AL_RESTO = "contra_flor_al_resto"


class BetStatus(Enum):
    NONE = "none"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"
