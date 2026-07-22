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
    ME_ACHICO = "me_achico"          # fold (phase 1 or 2)
    CONTRA_FLOR = "contra_flor"      # counter-flor (phase 1 only)
    ACEITAR = "aceitar"              # accept confronto after ContraFlor (phase 2 only)
    CONTRA_FLOR_AL_RESTO = "contra_flor_al_resto"  # all-in (phase 2 only)


class BetStatus(Enum):
    NONE = "none"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"
