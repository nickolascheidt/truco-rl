"""
Jogue contra o agente treinado no terminal.

Usage:
    python play.py models/truco_final
    python play.py models/truco_best_vs_random
"""
import argparse
import os
import numpy as np
from sb3_contrib import MaskablePPO

from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetStatus
from truco.rl.actions import compute_action_mask, apply_action, TrucoAction, N_ACTIONS
from truco.rl.obs import encode_obs


def clear():
    os.system("cls" if os.name == "nt" else "clear")


SUIT_SYMBOLS = {"espadas": "E", "ouros": "O", "copas": "C", "paus": "P"}

ACTION_LABELS = {
    TrucoAction.PLAY_CARD_0:               "Jogar carta 0",
    TrucoAction.PLAY_CARD_1:               "Jogar carta 1",
    TrucoAction.PLAY_CARD_2:               "Jogar carta 2",
    TrucoAction.TRUCO_ASK_OR_RAISE:        "TRUCO / Elevar truco",
    TrucoAction.TRUCO_ACCEPT:              "Aceitar truco",
    TrucoAction.TRUCO_REFUSE:              "Recusar truco (ir embora)",
    TrucoAction.ENVIDO:                    "ENVIDO",
    TrucoAction.REAL_ENVIDO:               "REAL ENVIDO",
    TrucoAction.FALTA_ENVIDO:              "FALTA ENVIDO",
    TrucoAction.ENVIDO_ACCEPT:             "Aceitar envido",
    TrucoAction.ENVIDO_REFUSE:             "Recusar envido",
    TrucoAction.DECLARE_FLOR:              "FLOR",
    TrucoAction.FLOR_ME_ACHICO:            "Me achico (flor)",
    TrucoAction.FLOR_CONTRA_FLOR:          "CONTRA-FLOR",
    TrucoAction.FLOR_ACEITAR:              "Aceitar confronto de flor",
    TrucoAction.FLOR_CONTRA_FLOR_AL_RESTO: "CONTRA-FLOR AL RESTO",
}


def fmt_card(card):
    suit = SUIT_SYMBOLS.get(card.suit.value, card.suit.value[0].upper())
    return f"{card.number}{suit}(forca={card.strength})"


def fmt_hand(cards):
    return "  ".join(f"[{i}] {fmt_card(c)}" for i, c in enumerate(cards))


def _current_actor(game, human, agent):
    hand = game.hand
    if hand.truco.status == BetStatus.PENDING:
        return agent if hand.truco.who_asked == game._player_team(human) else human
    if hand.envido.status == BetStatus.PENDING:
        return agent if hand.envido.who_asked == human else human
    if hand.flor.waiting_for_response:
        declarer = hand.flor.who_declared.players[0]
        if hand.flor.contra_flor_pending:
            return declarer
        return agent if declarer == human else human
    return hand.current_player


def agent_move(model, game, agent):
    mask = compute_action_mask(game, agent)
    obs = encode_obs(game, agent)
    action_arr, _ = model.predict(obs[np.newaxis], action_masks=mask[np.newaxis], deterministic=True)
    action = int(action_arr[0])
    name = ACTION_LABELS.get(TrucoAction(action), f"acao_{action}")

    extra = ""
    act = TrucoAction(action)
    if act == TrucoAction.PLAY_CARD_0 and agent.hand:
        extra = f" -> {fmt_card(agent.hand[0])}"
    elif act == TrucoAction.PLAY_CARD_1 and len(agent.hand) > 1:
        extra = f" -> {fmt_card(agent.hand[1])}"
    elif act == TrucoAction.PLAY_CARD_2 and len(agent.hand) > 2:
        extra = f" -> {fmt_card(agent.hand[2])}"

    print(f"\n  [AGENTE]  {name}{extra}")
    return action


def human_move(game, human):
    mask = compute_action_mask(game, human)
    legal = [TrucoAction(i) for i, ok in enumerate(mask) if ok]

    print("\n  Suas opcoes:")
    for i, act in enumerate(legal):
        label = ACTION_LABELS.get(act, str(act))
        extra = ""
        if act == TrucoAction.PLAY_CARD_0 and human.hand:
            extra = f" ({fmt_card(human.hand[0])})"
        elif act == TrucoAction.PLAY_CARD_1 and len(human.hand) > 1:
            extra = f" ({fmt_card(human.hand[1])})"
        elif act == TrucoAction.PLAY_CARD_2 and len(human.hand) > 2:
            extra = f" ({fmt_card(human.hand[2])})"
        print(f"    {i}) {label}{extra}")

    print()
    while True:
        try:
            choice = int(input("  Escolha: "))
            if 0 <= choice < len(legal):
                return int(legal[choice])
        except (ValueError, KeyboardInterrupt):
            pass
        print("  Opcao invalida, tente novamente.")


def print_header(game, human_team, agent_team, hand_num, human, agent):
    hand = game.hand
    mano = hand.mano_player.name
    pts_to_win = game.points_to_win
    print(f"{'='*55}")
    print(f"  MAO {hand_num}   |   Mano: {mano}")
    print(f"  Voce: {human_team.points}/{pts_to_win} pts   |   Agente: {agent_team.points}/{pts_to_win} pts")
    print(f"{'='*55}")
    print()
    print(f"  Suas cartas:  {fmt_hand(human.hand)}")
    env = game.hand.envido_value(human)
    print(f"  Envido:       {env} pts")
    print()


def print_envido_result(hand, human, agent, envido_result):
    from truco.enums import BetStatus
    env = hand.envido
    if env.status != BetStatus.ACCEPTED or envido_result is None:
        return
    human_pts = hand.envido_value(human)
    agent_pts = hand.envido_value(agent)
    winner_team = getattr(envido_result, "winner_team", None)
    winner_name = winner_team.players[0].name if winner_team else "?"
    print()
    print(f"  ENVIDO resolvido:")
    print(f"    {human.name}: {human_pts} pts   |   {agent.name}: {agent_pts} pts")
    print(f"    Vencedor: {winner_name}  (+{env.value_accepted} pts no placar)")


def print_round_results(hand, human, agent):
    print()
    print("  Rodadas:")
    for i, r in enumerate(hand.rounds):
        if r.resolved:
            winner = r.winner.name if r.winner else "empate"
            plays = "  ".join(f"{p.name}: {fmt_card(c)}" for p, c in r.plays.items())
            print(f"    Rodada {i+1}: {plays}  ->  {winner}")


def play_game(model, game_num):
    human = Player("Voce")
    agent = Player("Agente")
    human_team = Team("T1", [human])
    agent_team = Team("T2", [agent])
    game = Game(human_team, agent_team)

    hand_num = 0
    while not game.check_game_over():
        hand_num += 1
        game.start_hand()

        clear()
        print_header(game, human_team, agent_team, hand_num, human, agent)

        envido_result = None
        for _ in range(200):
            if game.check_game_over():
                break

            current = _current_actor(game, human, agent)

            if current == human:
                action = human_move(game, human)
                print(f"\n  [VOCE]    {ACTION_LABELS.get(TrucoAction(action), str(action))}")
            else:
                action = agent_move(model, game, agent)

            result = apply_action(game, current, action)

            act = TrucoAction(action)
            if act == TrucoAction.ENVIDO_ACCEPT:
                envido_result = result

            if game.check_game_over():
                break
            if getattr(result, "hand_over", False):
                break

        print_envido_result(game.hand, human, agent, envido_result)
        print_round_results(game.hand, human, agent)
        print()
        print(f"  Placar final da mao: Voce={human_team.points}  Agente={agent_team.points}")
        print()
        input("  [Enter para continuar...]")

    clear()
    winner = "VOCE" if human_team.points >= game.points_to_win else "AGENTE"
    print(f"\n{'='*55}")
    print(f"  FIM DE JOGO  —  {hand_num} maos jogadas")
    print(f"  VENCEDOR: {winner}")
    print(f"  Placar: Voce={human_team.points}  Agente={agent_team.points}")
    print(f"{'='*55}\n")
    return winner == "VOCE"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str, help="Caminho para o modelo (sem .zip)")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    clear()
    print(f"Carregando modelo: {args.model} ...")
    model = MaskablePPO.load(args.model)
    print()
    print("  Truco Gaucho 1v1 — Voce vs Agente treinado")
    print("  Primeira a chegar em 24 pontos vence.")
    print()
    input("  [Enter para comecar...]")

    game_num = 1
    while True:
        play_game(model, game_num)
        again = input("  Jogar de novo? [s/N] ").strip().lower()
        if again not in ("s", "sim", "y", "yes"):
            break
        game_num += 1
        clear()

    print("\n  Ate mais!\n")


if __name__ == "__main__":
    main()
