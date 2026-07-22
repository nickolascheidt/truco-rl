"""
Watch the trained agent play full games.

Usage:
    python watch.py models/truco_final               # agent vs random
    python watch.py models/truco_final --vs-self     # agent vs itself
    python watch.py models/truco_final --vs-self --games 3 --seed 42
"""
import argparse
import numpy as np
from sb3_contrib import MaskablePPO

from truco.rl.env import TrucoEnv, RandomPolicy
from truco.rl.actions import compute_action_mask, apply_action, TrucoAction, N_ACTIONS
from truco.rl.obs import encode_obs
from truco.enums import BetStatus


class ModelPolicy:
    """Wraps a loaded MaskablePPO so it can be used as an opponent policy."""
    def __init__(self, model):
        self._model = model

    def predict(self, obs: np.ndarray, action_masks: np.ndarray | None = None):
        obs_2d = obs[np.newaxis, :]
        masks_2d = action_masks[np.newaxis, :] if action_masks is not None else None
        action, _ = self._model.predict(obs_2d, action_masks=masks_2d, deterministic=True)
        return int(action[0]), None


ACTION_NAMES = {
    TrucoAction.PLAY_CARD_0: "joga carta 0",
    TrucoAction.PLAY_CARD_1: "joga carta 1",
    TrucoAction.PLAY_CARD_2: "joga carta 2",
    TrucoAction.TRUCO_ASK_OR_RAISE: "TRUCO / eleva truco",
    TrucoAction.TRUCO_ACCEPT: "aceita truco",
    TrucoAction.TRUCO_REFUSE: "recusa truco",
    TrucoAction.ENVIDO: "ENVIDO",
    TrucoAction.REAL_ENVIDO: "REAL ENVIDO",
    TrucoAction.FALTA_ENVIDO: "FALTA ENVIDO",
    TrucoAction.ENVIDO_ACCEPT: "aceita envido",
    TrucoAction.ENVIDO_REFUSE: "recusa envido",
    TrucoAction.DECLARE_FLOR: "FLOR",
    TrucoAction.FLOR_ME_ACHICO: "me achico (flor)",
    TrucoAction.FLOR_CONTRA_FLOR: "CONTRA-FLOR",
    TrucoAction.FLOR_ACEITAR: "aceita confronto",
    TrucoAction.FLOR_CONTRA_FLOR_AL_RESTO: "CONTRA-FLOR AL RESTO",
}

SUIT_SYMBOLS = {
    "espadas": "E",
    "ouros": "O",
    "copas": "C",
    "paus": "P",
}


def fmt_card(card):
    suit = SUIT_SYMBOLS.get(card.suit.value, card.suit.value[0].upper())
    return f"{card.number}{suit}(str={card.strength})"


def fmt_hand(cards):
    return "[" + ", ".join(fmt_card(c) for c in cards) + "]"


def watch_game(model, game_num: int, seed: int, opp_label: str = "Random", opp_policy=None):
    from truco.entities.game import Game
    from truco.entities.player import Player
    from truco.entities.team import Team

    np.random.seed(seed)

    p1_label = "Agente"
    p2_label = opp_label
    alice = Player(p1_label)
    bob = Player(p2_label)
    t1 = Team("T1", [alice])
    t2 = Team("T2", [bob])
    game = Game(t1, t2)

    p2_policy = opp_policy or RandomPolicy()

    print(f"\n{'='*60}")
    print(f"  JOGO {game_num}  ({p1_label} vs {p2_label})  seed={seed}")
    print(f"{'='*60}")

    hand_num = 0
    while not game.check_game_over():
        hand_num += 1
        game.start_hand()
        hand = game.hand
        mano_name = hand.mano_player.name

        print(f"\n--- Mao {hand_num}  |  {p1_label}={t1.points}  {p2_label}={t2.points}  |  Mano={mano_name} ---")
        print(f"  {p1_label:8s}: {fmt_hand(alice.hand)}")
        print(f"  {p2_label:8s}: {fmt_hand(bob.hand)}")

        for _ in range(200):
            if game.check_game_over():
                break

            current = _current_actor(game, alice, bob)

            if current == alice:
                mask = compute_action_mask(game, alice)
                obs = encode_obs(game, alice)
                action_arr, _ = model.predict(obs[np.newaxis], action_masks=mask[np.newaxis], deterministic=True)
                action = int(action_arr[0])
                actor_label = p1_label
            else:
                mask = compute_action_mask(game, bob)
                obs = encode_obs(game, bob)
                action, _ = p2_policy.predict(obs, action_masks=mask)
                actor_label = p2_label

            action_name = ACTION_NAMES.get(TrucoAction(action), f"acao_{action}")

            extra = ""
            act = TrucoAction(action)
            if act == TrucoAction.PLAY_CARD_0 and current.hand:
                extra = f"  [{fmt_card(current.hand[0])}]"
            elif act == TrucoAction.PLAY_CARD_1 and len(current.hand) > 1:
                extra = f"  [{fmt_card(current.hand[1])}]"
            elif act == TrucoAction.PLAY_CARD_2 and len(current.hand) > 2:
                extra = f"  [{fmt_card(current.hand[2])}]"

            print(f"    {actor_label:10s}: {action_name}{extra}")

            result = apply_action(game, current, action)

            if game.check_game_over():
                break
            if getattr(result, "hand_over", False):
                break

        for i, r in enumerate(hand.rounds):
            if r.resolved:
                winner_name = r.winner.name if r.winner else "empate"
                played = {p.name: fmt_card(c) for p, c in r.plays.items()}
                print(f"  Rodada {i+1}: {played}  ->  {winner_name}")

        print(f"  Placar: {p1_label}={t1.points}  {p2_label}={t2.points}")

    winner = p1_label if t1.points >= game.points_to_win else p2_label
    print(f"\n>>> VENCEDOR: {winner}  ({t1.points} x {t2.points})  em {hand_num} maos")


def _current_actor(game, alice, bob):
    hand = game.hand
    if hand.truco.status == BetStatus.PENDING:
        return bob if hand.truco.who_asked == game._player_team(alice) else alice
    if hand.envido.status == BetStatus.PENDING:
        return bob if hand.envido.who_asked == alice else alice
    if hand.flor.waiting_for_response:
        declarer = hand.flor.who_declared.players[0]
        if hand.flor.contra_flor_pending:
            return declarer
        return bob if declarer == alice else alice
    return hand.current_player


def _encode(game, player):
    from truco.rl.obs import encode_obs
    return encode_obs(game, player)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str)
    parser.add_argument("--vs-self", action="store_true", help="Opponent also uses the trained model")
    parser.add_argument("--games", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    model = MaskablePPO.load(args.model)

    if args.vs_self:
        opp_label = "Agente-2"
        opp_policy = ModelPolicy(model)
    else:
        opp_label = "Random"
        opp_policy = None

    for i in range(args.games):
        watch_game(model, game_num=i + 1, seed=args.seed + i,
                   opp_label=opp_label, opp_policy=opp_policy)


if __name__ == "__main__":
    main()
