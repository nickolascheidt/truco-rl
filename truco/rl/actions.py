from __future__ import annotations
from enum import IntEnum
import numpy as np
from truco.enums import BetStatus, BetType, BetResponse, FlorResponse

N_ACTIONS = 16


class TrucoAction(IntEnum):
    PLAY_CARD_0 = 0
    PLAY_CARD_1 = 1
    PLAY_CARD_2 = 2
    TRUCO_ASK_OR_RAISE = 3   # ask truco OR raise while responding
    TRUCO_ACCEPT = 4
    TRUCO_REFUSE = 5
    ENVIDO = 6
    REAL_ENVIDO = 7
    FALTA_ENVIDO = 8
    ENVIDO_ACCEPT = 9
    ENVIDO_REFUSE = 10
    DECLARE_FLOR = 11
    FLOR_ME_ACHICO = 12
    FLOR_CONTRA_FLOR = 13
    FLOR_ACEITAR = 14
    FLOR_CONTRA_FLOR_AL_RESTO = 15


def compute_action_mask(game, player) -> np.ndarray:
    """Return bool array of shape (N_ACTIONS,) with True where the action is legal."""
    mask = np.zeros(N_ACTIONS, dtype=bool)
    hand = game.hand

    truco = hand.truco
    envido = hand.envido
    flor = hand.flor
    player_team = game._player_team(player)

    truco_pending = truco.status == BetStatus.PENDING
    envido_pending = envido.status == BetStatus.PENDING
    flor_pending = flor.waiting_for_response

    # --- Truco response ---
    if truco_pending and truco.who_asked != player_team:
        mask[TrucoAction.TRUCO_ACCEPT] = True
        mask[TrucoAction.TRUCO_REFUSE] = True
        if truco.current_value < 4:
            mask[TrucoAction.TRUCO_ASK_OR_RAISE] = True
        return mask

    # --- Envido response ---
    if envido_pending and envido.who_asked != player:
        mask[TrucoAction.ENVIDO_ACCEPT] = True
        mask[TrucoAction.ENVIDO_REFUSE] = True
        # responder can also raise
        if game.can_envido(player):
            mask[TrucoAction.ENVIDO] = True
            mask[TrucoAction.REAL_ENVIDO] = True
            mask[TrucoAction.FALTA_ENVIDO] = True
        return mask

    # --- Flor response phase 1: opponent of declarer ---
    if flor_pending and not flor.contra_flor_pending:
        declarer = flor.who_declared.players[0]
        if player != declarer:
            mask[TrucoAction.FLOR_ME_ACHICO] = True
            if game.can_flor(player):
                mask[TrucoAction.FLOR_CONTRA_FLOR] = True
            return mask

    # --- Flor response phase 2: original declarer responds to contra_flor ---
    if flor_pending and flor.contra_flor_pending:
        declarer = flor.who_declared.players[0]
        if player == declarer:
            mask[TrucoAction.FLOR_ME_ACHICO] = True
            mask[TrucoAction.FLOR_ACEITAR] = True
            mask[TrucoAction.FLOR_CONTRA_FLOR_AL_RESTO] = True
            return mask

    # --- Normal turn: must be this player's turn to play a card ---
    if hand.current_player != player:
        return mask

    any_pending = truco_pending or envido_pending or flor_pending

    for i in range(min(len(player.hand), 3)):
        mask[TrucoAction.PLAY_CARD_0 + i] = True

    if not any_pending and game.can_ask_truco(player):
        mask[TrucoAction.TRUCO_ASK_OR_RAISE] = True

    if not any_pending and game.can_envido(player):
        mask[TrucoAction.ENVIDO] = True
        mask[TrucoAction.REAL_ENVIDO] = True
        mask[TrucoAction.FALTA_ENVIDO] = True

    if not any_pending and game.can_flor(player):
        mask[TrucoAction.DECLARE_FLOR] = True

    return mask


def apply_action(game, player, action: int):
    """Apply action to the game and return the result (BetResult or PlayResult)."""
    act = TrucoAction(action)

    if act == TrucoAction.PLAY_CARD_0:
        return game.play_card(player, player.hand[0])
    if act == TrucoAction.PLAY_CARD_1:
        return game.play_card(player, player.hand[1])
    if act == TrucoAction.PLAY_CARD_2:
        return game.play_card(player, player.hand[2])
    if act == TrucoAction.TRUCO_ASK_OR_RAISE:
        if game.hand.truco.status == BetStatus.PENDING:
            return game.respond_truco(player, BetResponse.RAISE)
        return game.ask_truco(player)
    if act == TrucoAction.TRUCO_ACCEPT:
        return game.respond_truco(player, BetResponse.ACCEPT)
    if act == TrucoAction.TRUCO_REFUSE:
        return game.respond_truco(player, BetResponse.REFUSE)
    if act == TrucoAction.ENVIDO:
        return game.ask_envido(player, BetType.ENVIDO)
    if act == TrucoAction.REAL_ENVIDO:
        return game.ask_envido(player, BetType.REAL_ENVIDO)
    if act == TrucoAction.FALTA_ENVIDO:
        return game.ask_envido(player, BetType.FALTA_ENVIDO)
    if act == TrucoAction.ENVIDO_ACCEPT:
        return game.respond_envido(player, BetResponse.ACCEPT)
    if act == TrucoAction.ENVIDO_REFUSE:
        return game.respond_envido(player, BetResponse.REFUSE)
    if act == TrucoAction.DECLARE_FLOR:
        return game.declare_flor(player)
    if act == TrucoAction.FLOR_ME_ACHICO:
        return game.respond_flor(player, FlorResponse.ME_ACHICO)
    if act == TrucoAction.FLOR_CONTRA_FLOR:
        return game.respond_flor(player, FlorResponse.CONTRA_FLOR)
    if act == TrucoAction.FLOR_ACEITAR:
        return game.respond_flor(player, FlorResponse.ACEITAR)
    if act == TrucoAction.FLOR_CONTRA_FLOR_AL_RESTO:
        return game.respond_flor(player, FlorResponse.CONTRA_FLOR_AL_RESTO)
    raise ValueError(f"Unknown action: {action}")
