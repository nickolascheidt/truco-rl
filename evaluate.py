"""
Evaluate a player against the baseline opponents.

The player is a trained model or one of the baselines, so the same table
shows how much the agent adds over the rule-based bot.

Usage:
    python evaluate.py models/truco_final                  # vs random and heuristic
    python evaluate.py models/truco_final --games 2000
    python evaluate.py models/truco_final --opponent heuristic
    python evaluate.py heuristic                           # baseline vs baselines
"""
import argparse
import math

from truco.rl.env import TrucoEnv, RandomPolicy
from truco.rl.heuristic import HeuristicPolicy

BASELINES = {"random": RandomPolicy, "heuristic": HeuristicPolicy}


class _ModelPolicy:
    def __init__(self, path: str):
        from sb3_contrib import MaskablePPO
        self._model = MaskablePPO.load(path)

    def predict(self, obs, action_masks=None):
        action, _ = self._model.predict(obs, action_masks=action_masks, deterministic=True)
        return int(action), None


def load_player(name: str):
    return BASELINES[name]() if name in BASELINES else _ModelPolicy(name)


def evaluate(player, opponent, n_games: int = 500) -> dict:
    env = TrucoEnv(opponent_policy=opponent)
    wins = 0
    total_steps = 0

    for _ in range(n_games):
        obs, _ = env.reset()
        for _ in range(1000):
            action, _ = player.predict(obs, action_masks=env.action_masks())
            obs, reward, done, _, _ = env.step(int(action))
            total_steps += 1
            if done:
                wins += reward > 0
                break

    win_rate = wins / n_games
    # 95% normal-approximation interval, so small differences are not over-read.
    margin = 1.96 * math.sqrt(win_rate * (1 - win_rate) / n_games)
    return {
        "win_rate": win_rate, "margin": margin, "wins": wins, "games": n_games,
        "avg_steps_per_game": total_steps / n_games,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("player", type=str, help="Model path (without .zip), or 'random' / 'heuristic'")
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--opponent", choices=[*BASELINES, "all"], default="all")
    args = parser.parse_args()

    player = load_player(args.player)
    opponents = list(BASELINES) if args.opponent == "all" else [args.opponent]

    print(f"Player: {args.player}  ({args.games} games per opponent)")
    for name in opponents:
        r = evaluate(player, BASELINES[name](), args.games)
        print(f"  vs {name:<9}  win {r['win_rate']:6.1%} +/- {r['margin']:.1%}"
              f"   avg steps/game {r['avg_steps_per_game']:.1f}")


if __name__ == "__main__":
    main()
